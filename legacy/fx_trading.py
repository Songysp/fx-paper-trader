import threading
import time
import csv
import os
from collections import deque
from datetime import datetime

import numpy as np
import pandas as pd
from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract
from ibapi.order import Order


class IBPaperTrader(EWrapper, EClient):
    def __init__(self):
        """
        EWrapper:
            IBKR로부터 들어오는 이벤트(시세, 주문상태, 체결 등)를 받는 역할

        EClient:
            IBKR로 요청(시세 요청, 주문 전송 등)을 보내는 역할
        """
        EClient.__init__(self, self)

        # ==============================
        # 1. 연결 / 주문 관련 상태값
        # ==============================
        self.next_order_id = None          # 다음 주문에 사용할 ID
        self.connected_ok = False          # 연결 성공 여부
        self.pending_order = False         # 주문이 아직 처리 중인지 여부

        # ==============================
        # 2. 틱 데이터 저장
        # ==============================
        self.prices = deque(maxlen=1000)   # 최근 틱 가격 저장
        self.timestamps = deque(maxlen=1000)

        # ==============================
        # 3. 바(1분봉) 생성용 변수
        # ==============================
        self.current_bar_prices = []       # 현재 1분 동안 들어온 가격들
        self.last_bar_minute = None        # 현재 바가 어떤 분(minute)인지
        self.bars = []                     # 완성된 1분봉 저장

        # ==============================
        # 4. 포지션 상태
        # ==============================
        self.current_position = 0          # 0 = 포지션 없음, 1 = 매수 보유(long)
        self.position_qty = 0              # 현재 보유 수량
        self.entry_price = None            # 진입 가격

        # 마지막 주문 정보
        self.last_order_action = None
        self.last_order_quantity = 0

        # ==============================
        # 5. 리스크 관리 설정
        # ==============================
        self.stop_loss_pct = 0.005         # 0.5% 손절
        self.take_profit_pct = 0.01        # 1.0% 익절
        self.max_daily_loss = -50000       # 하루 최대 손실 제한 (예시: -50,000 KRW)

        self.daily_realized_pnl = 0.0      # 당일 실현손익
        self.trading_halted = False        # 하루 손실 한도 넘으면 거래 중지
        self.current_trading_date = datetime.now().date()

        # ==============================
        # 6. 전략 파라미터
        # ==============================
        self.short_window = 5              # 단기 이동평균
        self.long_window = 20              # 장기 이동평균
        self.default_order_qty = 1000      # 기본 주문 수량

        # ==============================
        # 7. 기타
        # ==============================
        self.req_id_market_data = 1        # 시장데이터 요청 ID
        self.contract = None               # 거래 종목 저장
        self.last_execution_price = None   # 마지막 체결가

        # ==============================
        # 8. 로그 파일
        # ==============================
        self.log_file = "trading_log.csv"
        self.initialize_log_file()

    # --------------------------------------------------
    # 로그 관련
    # --------------------------------------------------
    def initialize_log_file(self):
        """
        로그 파일이 없으면 새로 만들고 헤더(컬럼명)를 작성
        """
        if not os.path.exists(self.log_file):
            with open(self.log_file, mode="w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f)
                writer.writerow([
                    "timestamp",
                    "event_type",
                    "price",
                    "signal",
                    "current_position",
                    "position_qty",
                    "entry_price",
                    "daily_realized_pnl",
                    "message"
                ])

    def write_log(self, event_type, price=None, signal=None, message=""):
        """
        주요 이벤트를 CSV 파일에 기록
        """
        with open(self.log_file, mode="a", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerow([
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                event_type,
                price,
                signal,
                self.current_position,
                self.position_qty,
                self.entry_price,
                self.daily_realized_pnl,
                message
            ])

    # --------------------------------------------------
    # 연결 관련 콜백
    # --------------------------------------------------
    def nextValidId(self, orderId: int):
        """
        IBKR 연결 후 '다음 주문에 사용할 수 있는 ID'를 내려주는 콜백
        이 ID가 있어야 주문 전송 가능
        """
        self.next_order_id = orderId
        self.connected_ok = True
        print(f"[INFO] Connected. Next valid order id: {orderId}")
        self.write_log("SYSTEM", message=f"Connected. next_order_id={orderId}")

    def error(self, reqId, errorCode, errorString, advancedOrderRejectJson=""):
        """
        IBKR API 에러 콜백
        """
        print(f"[ERROR] reqId={reqId}, code={errorCode}, msg={errorString}")
        self.write_log("ERROR", message=f"reqId={reqId}, code={errorCode}, msg={errorString}")

    # --------------------------------------------------
    # 종목(계약) 생성
    # --------------------------------------------------
    def fx_contract(self, symbol="USD", currency="KRW", exchange="IDEALPRO"):
        """
        FX 현물 계약 생성
        예: USD/KRW
        """
        contract = Contract()
        contract.symbol = symbol
        contract.secType = "CASH"
        contract.currency = currency
        contract.exchange = exchange
        return contract

    # --------------------------------------------------
    # 주문 객체 생성
    # --------------------------------------------------
    def market_order(self, action: str, quantity: float):
        """
        시장가 주문 생성
        action: BUY / SELL
        quantity: 수량
        """
        order = Order()
        order.action = action
        order.orderType = "MKT"
        order.totalQuantity = quantity
        return order

    def limit_order(self, action: str, quantity: float, limit_price: float):
        """
        지정가 주문 생성
        """
        order = Order()
        order.action = action
        order.orderType = "LMT"
        order.totalQuantity = quantity
        order.lmtPrice = limit_price
        return order

    # --------------------------------------------------
    # 틱 데이터 수신
    # --------------------------------------------------
    def tickPrice(self, reqId, tickType, price, attrib):
        """
        실시간 시세가 들어올 때마다 호출되는 함수

        여기서 하는 일:
        1) 틱 가격 저장
        2) 1분봉 생성용으로 같은 분의 가격을 모음
        3) 분이 바뀌면 이전 분을 OHLC 바로 확정
        4) 새 바가 만들어지면 전략 실행
        """
        if reqId != self.req_id_market_data:
            return

        if price <= 0:
            return

        now = pd.Timestamp.now()
        current_minute = now.replace(second=0, microsecond=0)

        # 틱 저장
        self.prices.append(price)
        self.timestamps.append(now)

        print(f"[TICK] time={now.strftime('%H:%M:%S')} price={price}")
        self.write_log("TICK", price=price, message=f"tickType={tickType}")

        # 첫 틱이면 현재 분 초기화
        if self.last_bar_minute is None:
            self.last_bar_minute = current_minute

        # 같은 분이면 가격 추가
        if current_minute == self.last_bar_minute:
            self.current_bar_prices.append(price)
            return

        # 분이 바뀌었다면, 이전 분의 바를 확정
        if len(self.current_bar_prices) > 0:
            bar = {
                "time": self.last_bar_minute,
                "open": self.current_bar_prices[0],
                "high": max(self.current_bar_prices),
                "low": min(self.current_bar_prices),
                "close": self.current_bar_prices[-1]
            }

            self.bars.append(bar)

            print(
                f"[BAR] time={bar['time']} "
                f"O={bar['open']} H={bar['high']} L={bar['low']} C={bar['close']}"
            )
            self.write_log(
                "BAR",
                price=bar["close"],
                message=(
                    f"time={bar['time']}, open={bar['open']}, high={bar['high']}, "
                    f"low={bar['low']}, close={bar['close']}"
                )
            )

            # 새 바가 완성되었으니 전략 실행
            self.on_new_bar(bar)

        # 새 분 시작
        self.current_bar_prices = [price]
        self.last_bar_minute = current_minute

    # --------------------------------------------------
    # 주문 상태 / 체결 콜백
    # --------------------------------------------------
    def orderStatus(
        self,
        orderId,
        status,
        filled,
        remaining,
        avgFillPrice,
        permId,
        parentId,
        lastFillPrice,
        clientId,
        whyHeld,
        mktCapPrice
    ):
        """
        주문 상태가 바뀔 때마다 호출
        예: Submitted, Filled, Cancelled 등
        """
        print(
            f"[ORDER STATUS] orderId={orderId}, status={status}, "
            f"filled={filled}, remaining={remaining}, avgFillPrice={avgFillPrice}"
        )

        self.write_log(
            "ORDER_STATUS",
            price=avgFillPrice,
            message=f"orderId={orderId}, status={status}, filled={filled}, remaining={remaining}"
        )

        # 주문이 종료된 상태면 pending 해제
        if status in ["Filled", "Cancelled", "Inactive", "ApiCancelled"]:
            self.pending_order = False

    def execDetails(self, reqId, contract, execution):
        """
        실제 체결이 발생했을 때 호출

        핵심:
        주문 넣었다고 바로 포지션 바꾸는 게 아니라
        '실제 체결' 되었을 때 포지션을 갱신한다.
        """
        exec_price = execution.price
        exec_qty = execution.shares
        exec_side = execution.side.upper()

        print(
            f"[EXECUTION] symbol={contract.symbol}, side={exec_side}, "
            f"shares={exec_qty}, price={exec_price}"
        )

        self.last_execution_price = exec_price

        # 매수 체결
        if exec_side == "BOT":
            self.current_position = 1
            self.position_qty = exec_qty
            self.entry_price = exec_price

            self.write_log(
                "EXECUTION",
                price=exec_price,
                message=f"BUY filled qty={exec_qty}"
            )

        # 매도 체결
        elif exec_side == "SLD":
            realized_pnl = 0.0

            if self.entry_price is not None and self.position_qty > 0:
                # 매우 단순한 손익 계산
                realized_pnl = (exec_price - self.entry_price) * self.position_qty

            self.daily_realized_pnl += realized_pnl

            self.current_position = 0
            self.position_qty = 0
            self.entry_price = None

            self.write_log(
                "EXECUTION",
                price=exec_price,
                message=f"SELL filled qty={exec_qty}, realized_pnl={realized_pnl:.2f}"
            )

            print(f"[PNL] realized_pnl={realized_pnl:.2f}, daily_realized_pnl={self.daily_realized_pnl:.2f}")

        print(
            f"[POSITION UPDATED] current_position={self.current_position}, "
            f"position_qty={self.position_qty}, entry_price={self.entry_price}"
        )

    # --------------------------------------------------
    # 일자 변경 처리
    # --------------------------------------------------
    def reset_daily_state_if_needed(self):
        """
        날짜가 바뀌면 당일 손익과 거래중지 상태 초기화
        """
        today = datetime.now().date()

        if today != self.current_trading_date:
            self.current_trading_date = today
            self.daily_realized_pnl = 0.0
            self.trading_halted = False

            print("[INFO] New trading day detected. Daily PnL reset.")
            self.write_log("SYSTEM", message="New trading day detected. Daily PnL reset.")

    # --------------------------------------------------
    # 리스크 관리
    # --------------------------------------------------
    def check_risk_rules(self):
        """
        리스크 룰 체크

        반환값:
        - "HALT"        : 당일 최대 손실 도달
        - "STOP_LOSS"   : 손절
        - "TAKE_PROFIT" : 익절
        - "OK"          : 정상
        """
        self.reset_daily_state_if_needed()

        # 하루 최대 손실 도달 시 거래 중단
        if self.daily_realized_pnl <= self.max_daily_loss:
            self.trading_halted = True
            print("[RISK] Daily loss limit breached. Trading halted.")
            self.write_log("RISK", message="Daily loss limit breached. Trading halted.")
            return "HALT"

        # 포지션 보유 중이면 손절/익절 체크
        if self.current_position == 1 and self.entry_price is not None and len(self.prices) > 0:
            current_price = self.prices[-1]
            pnl_pct = (current_price - self.entry_price) / self.entry_price

            if pnl_pct <= -self.stop_loss_pct:
                print(f"[RISK] Stop loss triggered. pnl_pct={pnl_pct:.4%}")
                self.write_log("RISK", price=current_price, message=f"Stop loss triggered. pnl_pct={pnl_pct:.4%}")
                return "STOP_LOSS"

            if pnl_pct >= self.take_profit_pct:
                print(f"[RISK] Take profit triggered. pnl_pct={pnl_pct:.4%}")
                self.write_log("RISK", price=current_price, message=f"Take profit triggered. pnl_pct={pnl_pct:.4%}")
                return "TAKE_PROFIT"

        return "OK"

    # --------------------------------------------------
    # 전략 계산
    # --------------------------------------------------
    def compute_bar_signal(self):
        """
        완성된 1분봉의 close 가격을 기준으로 이동평균 전략 계산

        전략:
        - 최근 5개 바 평균 > 최근 20개 바 평균 => 매수 시그널(1)
        - 아니면 청산 시그널(0)
        """
        if len(self.bars) < self.long_window:
            return None, None, None

        df = pd.DataFrame(self.bars)

        short_ma = df["close"].rolling(self.short_window).mean().iloc[-1]
        long_ma = df["close"].rolling(self.long_window).mean().iloc[-1]

        if np.isnan(short_ma) or np.isnan(long_ma):
            return None, short_ma, long_ma

        signal = 1 if short_ma > long_ma else 0
        return signal, short_ma, long_ma

    # --------------------------------------------------
    # 새 바가 생길 때마다 전략 실행
    # --------------------------------------------------
    def on_new_bar(self, bar):
        """
        1분봉이 완성될 때마다 호출

        여기서 하는 일:
        1) 이동평균 계산
        2) 리스크 체크
        3) 주문 필요 여부 판단
        """
        signal, short_ma, long_ma = self.compute_bar_signal()

        # 아직 바가 충분하지 않으면 전략 실행 불가
        if signal is None:
            print("[INFO] Not enough bars for MA strategy yet.")
            return

        latest_price = bar["close"]

        print(
            f"[BAR STRATEGY] price={latest_price:.4f}, "
            f"short_ma={short_ma:.4f}, long_ma={long_ma:.4f}, "
            f"signal={signal}, current_position={self.current_position}, "
            f"pending_order={self.pending_order}, daily_realized_pnl={self.daily_realized_pnl:.2f}"
        )

        self.write_log(
            "SIGNAL",
            price=latest_price,
            signal=signal,
            message=(
                f"bar_time={bar['time']}, short_ma={short_ma:.4f}, "
                f"long_ma={long_ma:.4f}, pending_order={self.pending_order}"
            )
        )

        # 주문 처리 중이면 중복 주문 금지
        if self.pending_order:
            print("[ACTION] Pending order exists. No new trade.")
            return

        # 리스크 체크
        risk_status = self.check_risk_rules()

        # 하루 손실 한도 초과
        if risk_status == "HALT":
            print("[ACTION] Trading halted due to daily loss limit.")
            return

        # 손절 / 익절 우선
        if risk_status in ["STOP_LOSS", "TAKE_PROFIT"] and self.current_position == 1:
            print(f"[ACTION] Exit due to risk rule: {risk_status}")
            self.send_order(
                contract=self.contract,
                action="SELL",
                quantity=self.position_qty,
                use_limit=False
            )
            return

        # 전략에 따른 매수
        if signal == 1 and self.current_position == 0 and not self.trading_halted:
            print("[ACTION] BUY condition met")
            self.send_order(
                contract=self.contract,
                action="BUY",
                quantity=self.default_order_qty,
                use_limit=False
            )

        # 전략에 따른 매도(청산)
        elif signal == 0 and self.current_position == 1:
            print("[ACTION] SELL condition met")
            self.send_order(
                contract=self.contract,
                action="SELL",
                quantity=self.position_qty,
                use_limit=False
            )

        else:
            print("[ACTION] No trade")

    # --------------------------------------------------
    # 주문 전송
    # --------------------------------------------------
    def send_order(self, contract, action: str, quantity: float, use_limit=False):
        """
        주문 전송 함수
        use_limit=False 이면 시장가
        use_limit=True  이면 지정가
        """
        if self.next_order_id is None:
            print("[WARN] next_order_id is not ready.")
            return

        latest_price = self.prices[-1] if len(self.prices) > 0 else None

        # 지정가 주문
        if use_limit and latest_price is not None:
            # 매우 단순한 예시:
            # BUY는 현재가보다 조금 높게
            # SELL은 현재가보다 조금 낮게
            if action == "BUY":
                limit_price = latest_price * 1.0002
            else:
                limit_price = latest_price * 0.9998

            limit_price = round(limit_price, 4)
            order = self.limit_order(action, quantity, limit_price)

            print(f"[ORDER] Sending LIMIT {action}, qty={quantity}, limit={limit_price}")
            self.write_log("ORDER", price=latest_price, message=f"LIMIT {action}, qty={quantity}, limit={limit_price}")

        # 시장가 주문
        else:
            order = self.market_order(action, quantity)

            print(f"[ORDER] Sending MARKET {action}, qty={quantity}")
            self.write_log("ORDER", price=latest_price, message=f"MARKET {action}, qty={quantity}")

        self.placeOrder(self.next_order_id, contract, order)

        self.pending_order = True
        self.last_order_action = action
        self.last_order_quantity = quantity

        print(f"[ORDER SENT] orderId={self.next_order_id}")
        self.next_order_id += 1

    # --------------------------------------------------
    # 프로그램 시작 후 상태 출력용
    # --------------------------------------------------
    def print_strategy_summary(self):
        print("=" * 60)
        print("FX PAPER TRADING STRATEGY START")
        print(f"Short MA            : {self.short_window}")
        print(f"Long MA             : {self.long_window}")
        print(f"Default Order Qty   : {self.default_order_qty}")
        print(f"Stop Loss           : {self.stop_loss_pct:.2%}")
        print(f"Take Profit         : {self.take_profit_pct:.2%}")
        print(f"Max Daily Loss      : {self.max_daily_loss}")
        print(f"Log File            : {self.log_file}")
        print("=" * 60)

    # --------------------------------------------------
    # 메인 루프
    # --------------------------------------------------
    def run_strategy_loop(self):
        """
        실제 전략 판단은 on_new_bar() 안에서 수행됨.
        여기 루프는 프로그램이 살아있도록 유지하는 역할이 큼.
        """
        while True:
            try:
                time.sleep(1)

            except KeyboardInterrupt:
                print("[INFO] Strategy loop stopped by user.")
                self.write_log("SYSTEM", message="Strategy loop stopped by user.")
                break

            except Exception as e:
                print(f"[EXCEPTION] {e}")
                self.write_log("ERROR", message=f"Exception in strategy loop: {e}")
                time.sleep(1)


def main():
    # ==============================
    # 1. 앱 생성
    # ==============================
    app = IBPaperTrader()

    # ==============================
    # 2. 거래할 종목 설정
    #    예: USD/KRW
    #    다른 예: USD/JPY 로 바꾸려면 currency="JPY"
    # ==============================
    app.contract = app.fx_contract(symbol="USD", currency="KRW", exchange="IDEALPRO")

    # ==============================
    # 3. IBKR 연결
    #    일반적인 paper TWS 포트 예시: 7497
    # ==============================
    app.connect("127.0.0.1", 7497, clientId=123)

    # IBKR 이벤트 루프는 별도 스레드에서 실행
    api_thread = threading.Thread(target=app.run, daemon=True)
    api_thread.start()

    # 연결 완료 대기
    timeout = time.time() + 10
    while not app.connected_ok and time.time() < timeout:
        time.sleep(0.2)

    if not app.connected_ok:
        print("[FATAL] Could not connect to IBKR. Check TWS / IB Gateway / API settings.")
        return

    app.print_strategy_summary()

    # ==============================
    # 4. 실시간 시세 요청
    # ==============================
    app.reqMktData(app.req_id_market_data, app.contract, "", False, False, [])

    print("[INFO] Waiting for market data...")
    app.write_log("SYSTEM", message="Market data requested. Strategy started.")

    # ==============================
    # 5. 전략 루프 시작
    # ==============================
    app.run_strategy_loop()


if __name__ == "__main__":
    main()
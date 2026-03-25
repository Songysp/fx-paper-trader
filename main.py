"""Application entry point for the FX paper trader project."""

from __future__ import annotations

import time
from typing import List

from brokers.ibkr_client import IBKRClient
from config.settings import AppSettings
from data.bar_aggregator import BarAggregator
from data.tick_buffer import TickBuffer
from execution.order_factory import OrderFactory
from execution.position_manager import PositionManager
from logging_system.csv_logger import CSVTradeLogger
from models.state import Bar, ExecutionReport, OrderStatusEvent, PositionState, Tick
from risk.risk_manager import RiskManager
from strategies.ma_crossover import MovingAverageCrossoverStrategy


class TradingApplication:
    """Orchestrates the full trading flow in a beginner-friendly way."""

    def __init__(self) -> None:
        """Create every object the application needs."""
        self.settings = AppSettings.load()
        self.logger = CSVTradeLogger(self.settings.logging.log_file)
        self.tick_buffer = TickBuffer(max_size=1000)
        self.bar_aggregator = BarAggregator()
        self.strategy = MovingAverageCrossoverStrategy(
            short_window=self.settings.strategy.short_window,
            long_window=self.settings.strategy.long_window,
        )
        self.risk_manager = RiskManager(self.settings.risk)
        self.position_manager = PositionManager()
        self.order_factory = OrderFactory()
        self.position_state = PositionState()
        self.completed_bars: List[Bar] = []
        self.client = IBKRClient(
            settings=self.settings.broker,
            logger=self.logger,
        )
        self.contract = self.client.build_fx_contract()

    def wire_callbacks(self) -> None:
        """Connect broker events to the application handlers."""
        self.client.set_tick_handler(self.handle_tick)
        self.client.set_order_status_handler(self.handle_order_status)
        self.client.set_execution_handler(self.handle_execution)

    def print_startup_summary(self) -> None:
        """Print the most important runtime settings."""
        print("=" * 60)
        print("FX PAPER TRADER START")
        print(f"Symbol              : {self.settings.broker.symbol}/{self.settings.broker.currency}")
        print(f"Exchange            : {self.settings.broker.exchange}")
        print(f"Short MA            : {self.settings.strategy.short_window}")
        print(f"Long MA             : {self.settings.strategy.long_window}")
        print(f"Default Order Qty   : {self.settings.strategy.default_order_qty}")
        print(f"Stop Loss           : {self.settings.risk.stop_loss_pct:.2%}")
        print(f"Take Profit         : {self.settings.risk.take_profit_pct:.2%}")
        print(f"Max Daily Loss      : {self.settings.risk.max_daily_loss}")
        print(f"Log File            : {self.settings.logging.log_file}")
        print("=" * 60)

    def start(self) -> None:
        """Connect to IBKR, request market data, and keep the app alive."""
        self.wire_callbacks()

        if not self.client.connect_and_start():
            print("[FATAL] Could not connect to IBKR. Check TWS / IB Gateway / API settings.")
            return

        self.print_startup_summary()
        self.client.request_market_data(self.contract)
        self.logger.log_system("Market data requested. Strategy started.")
        print("[INFO] Waiting for market data...")

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("[INFO] Strategy loop stopped by user.")
            self.logger.log_system("Strategy loop stopped by user.")
        finally:
            flushed_bar = self.bar_aggregator.flush()
            if flushed_bar is not None:
                self.completed_bars.append(flushed_bar)
                self.logger.log_bar(flushed_bar)
                print(
                    f"[BAR] time={flushed_bar.timestamp} "
                    f"O={flushed_bar.open} H={flushed_bar.high} L={flushed_bar.low} C={flushed_bar.close}"
                )
                self.logger.log_system("Final unfinished bar was logged during shutdown without trading.")

            self.client.disconnect()

    def handle_tick(self, tick: Tick) -> None:
        """Store tick data and convert ticks into 1-minute bars."""
        self.tick_buffer.add_tick(tick)
        self.logger.log_tick(price=tick.price, tick_type=tick.tick_type)
        print(f"[TICK] time={tick.timestamp.strftime('%H:%M:%S')} price={tick.price}")

        completed_bar = self.bar_aggregator.update(tick)
        if completed_bar is not None:
            self.handle_completed_bar(completed_bar)

    def handle_completed_bar(self, bar: Bar) -> None:
        """Run risk checks and strategy checks when a new bar is ready."""
        self.completed_bars.append(bar)
        self.logger.log_bar(bar)

        print(
            f"[BAR] time={bar.timestamp} "
            f"O={bar.open} H={bar.high} L={bar.low} C={bar.close}"
        )

        close_prices = [completed_bar.close for completed_bar in self.completed_bars]

        risk_status = self.risk_manager.check(
            position=self.position_state,
            latest_price=bar.close,
        )
        self.logger.log_risk_check(
            status=risk_status,
            latest_price=bar.close,
            daily_realized_pnl=self.risk_manager.daily_realized_pnl,
        )

        if self.client.trade_state.pending_order:
            print("[ACTION] Pending order exists. No new trade.")
            return

        if risk_status == "HALT":
            print("[ACTION] Trading halted due to daily loss limit.")
            return

        if risk_status in {"STOP_LOSS", "TAKE_PROFIT"} and self.position_state.is_long:
            print(f"[ACTION] Exit due to risk rule: {risk_status}")
            self.submit_order("SELL", self.position_state.quantity)
            return

        signal = self.strategy.generate_signal(
            close_prices=close_prices,
            position=self.position_state,
        )

        short_ma, long_ma = self.strategy.get_latest_indicator_values(close_prices)
        self.logger.log_signal(
            price=bar.close,
            signal=signal,
            short_ma=short_ma,
            long_ma=long_ma,
            position_side=self.position_state.side,
        )

        if short_ma is None or long_ma is None:
            print("[INFO] Not enough bars for MA strategy yet.")
            return

        print(
            f"[BAR STRATEGY] price={bar.close:.4f}, "
            f"short_ma={short_ma:.4f}, long_ma={long_ma:.4f}, "
            f"signal={signal}, current_position={self.position_state.side}, "
            f"pending_order={self.client.trade_state.pending_order}, "
            f"daily_realized_pnl={self.risk_manager.daily_realized_pnl:.2f}"
        )

        if signal == "BUY" and not self.position_state.is_long and not self.risk_manager.trading_halted:
            print("[ACTION] BUY condition met")
            self.submit_order("BUY", self.settings.strategy.default_order_qty)
        elif signal == "SELL" and self.position_state.is_long:
            print("[ACTION] SELL condition met")
            self.submit_order("SELL", self.position_state.quantity)
        else:
            print("[ACTION] No trade")

    def submit_order(self, action: str, quantity: float) -> None:
        """Create and send a market order through the broker client."""
        latest_tick = self.tick_buffer.latest()
        latest_price = latest_tick.price if latest_tick is not None else None
        order_request = self.order_factory.market_order(action=action, quantity=quantity)
        self.client.submit_order(
            contract=self.contract,
            order_request=order_request,
            latest_price=latest_price,
        )

    def handle_order_status(self, event: OrderStatusEvent) -> None:
        """Handle order status events separately from execution events."""
        print(
            f"[ORDER STATUS] orderId={event.order_id}, status={event.status}, "
            f"filled={event.filled}, remaining={event.remaining}, avgFillPrice={event.avg_fill_price}"
        )

    def handle_execution(self, execution: ExecutionReport) -> None:
        """Update the position only after a real fill arrives."""
        print(
            f"[EXECUTION] symbol={execution.symbol}, side={execution.side}, "
            f"shares={execution.quantity}, price={execution.price}"
        )

        realized_pnl = self.position_manager.apply_execution(
            position=self.position_state,
            execution=execution,
        )
        self.risk_manager.register_realized_pnl(realized_pnl)
        self.logger.log_execution(
            execution=execution,
            position=self.position_state,
            realized_pnl=realized_pnl,
            daily_realized_pnl=self.risk_manager.daily_realized_pnl,
        )

        print(
            f"[POSITION UPDATED] current_position={self.position_state.side}, "
            f"position_qty={self.position_state.quantity}, "
            f"entry_price={self.position_state.avg_entry_price}"
        )

        if execution.side == "SLD":
            print(
                f"[PNL] realized_pnl={realized_pnl:.2f}, "
                f"daily_realized_pnl={self.risk_manager.daily_realized_pnl:.2f}"
            )


def main() -> None:
    """Run the trading application."""
    app = TradingApplication()
    app.start()


if __name__ == "__main__":
    main()

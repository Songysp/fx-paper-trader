# FX Paper Trader

`FX Paper Trader`는 IBKR(Interactive Brokers) API를 사용해
실시간 FX 데이터를 수신하고, tick 데이터를 1분봉으로 집계한 뒤
전략 신호와 리스크 조건에 따라 paper trading을 수행하는 Python 프로젝트입니다.

## 주요 기능

- IBKR paper trading 연결
- 실시간 tick 데이터 수신
- tick -> 1분봉 OHLC 집계
- MA crossover 전략 실행
- RSI / MA gap 필터 적용
- stop loss / take profit / max daily loss 적용
- `orderStatus` 와 `execDetails` 분리 처리
- 체결 기준 포지션 업데이트
- CSV 로그 기록
- CSV 기반 백테스트
- pytest 기반 단위 테스트

## 프로젝트 구조

```text
fx-paper-trader/
├─ README.md
├─ requirements.txt
├─ .env.example
├─ main.py
├─ config/
│  └─ settings.py
├─ brokers/
│  └─ ibkr_client.py
├─ data/
│  ├─ tick_buffer.py
│  └─ bar_aggregator.py
├─ strategies/
│  ├─ base.py
│  └─ ma_crossover.py
├─ risk/
│  └─ risk_manager.py
├─ execution/
│  ├─ order_factory.py
│  └─ position_manager.py
├─ logging_system/
│  └─ csv_logger.py
├─ models/
│  └─ state.py
├─ utils/
│  └─ time_utils.py
├─ backtests/
├─ historical_data/
├─ tests/
├─ legacy/
└─ logs/
```

## 모듈별 역할

### `main.py`

프로그램의 진입점입니다. 설정을 로드하고 각 객체를 생성한 뒤,
브로커 연결, 데이터 수신, 전략 실행, 주문 처리 흐름을 조립합니다.

### `config/settings.py`

브로커, 전략, 리스크, 로깅 관련 설정을 dataclass로 관리합니다.
`.env` 값을 읽어 실행 설정을 구성합니다.

### `brokers/ibkr_client.py`

IBKR API와 직접 연결되는 모듈입니다.

- 연결 / 해제
- 시장 데이터 요청
- 주문 전송
- `nextValidId`
- `tickPrice`
- `orderStatus`
- `execDetails`

### `data/tick_buffer.py`

실시간 tick 데이터를 저장하는 버퍼입니다.

### `data/bar_aggregator.py`

tick 데이터를 1분봉 OHLC로 집계합니다.

- 첫 tick: open
- 최고가: high
- 최저가: low
- 마지막 tick: close

### `strategies/base.py`

전략 인터페이스를 정의합니다.

### `strategies/ma_crossover.py`

종가 리스트를 바탕으로 이동평균 기반 매수/매도 신호를 생성합니다.
현재는 기본 MA crossover에 RSI 필터와 MA gap 필터를 추가한 구조입니다.

### `risk/risk_manager.py`

전략보다 먼저 리스크 조건을 확인합니다.

- stop loss
- take profit
- max daily loss

### `execution/order_factory.py`

시장가 / 지정가 주문 객체를 생성합니다.

### `execution/position_manager.py`

체결 기준으로 포지션 상태를 업데이트합니다.
주문을 전송했다고 바로 포지션을 바꾸지 않고,
실제 체결 이벤트가 들어온 뒤에만 상태를 반영합니다.

### `logging_system/csv_logger.py`

거래 및 시스템 이벤트를 CSV 파일로 기록합니다.

### `models/state.py`

`Bar`, `PositionState`, `TradeState` 같은 공통 dataclass를 정의합니다.

## 실행 흐름

프로그램은 아래 순서로 동작합니다.

1. 설정을 로드합니다.
2. 로거, 전략, 리스크 매니저, 브로커 클라이언트를 생성합니다.
3. IBKR에 연결합니다.
4. 실시간 tick 데이터를 수신합니다.
5. tick 데이터를 1분봉으로 집계합니다.
6. 새 봉이 완성되면 리스크 조건을 먼저 확인합니다.
7. 리스크 문제가 없으면 전략 신호를 계산합니다.
8. 주문을 전송합니다.
9. `orderStatus`는 주문 상태를 기록하고, `execDetails`는 실제 체결을 반영합니다.
10. 포지션과 손익을 업데이트하고 로그를 기록합니다.

## 매매 규칙

### 매수

아래 조건을 모두 만족해야 매수합니다.

1. 단기 MA > 장기 MA
2. RSI 필터 사용 시 `RSI <= RSI_BUY_MAX`
3. MA gap 필터 사용 시 단기 MA와 장기 MA 간격이 최소 기준 이상
4. 현재 포지션이 없음
5. pending order 가 없음
6. 일일 손실 한도 초과 상태가 아님

### 매도

- 단기 MA <= 장기 MA 이면 청산
- 또는 stop loss / take profit 조건이 먼저 충족되면 청산

## 빠른 시작

### 1. 가상환경 생성

```powershell
python -m venv .venv
```

### 2. 가상환경 활성화

```powershell
.\.venv\Scripts\Activate.ps1
```

PowerShell 정책 때문에 막히면:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

### 3. 패키지 설치

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### 4. 환경변수 파일 생성

```powershell
Copy-Item .env.example .env
```

### 5. 실행

```powershell
python main.py
```

## `.env` 설정 설명

### 브로커 연결

- `IBKR_HOST`: TWS / IB Gateway 주소
- `IBKR_PORT`: paper trading 포트
- `IBKR_CLIENT_ID`: API 클라이언트 ID
- `IBKR_CONNECT_TIMEOUT`: 연결 제한 시간
- `IBAPI_PATH`: 공식 IBKR Python API 경로

예시:

```env
IBAPI_PATH=C:\TWS API\source\pythonclient
```

### 종목 설정

- `FX_SYMBOL`: 기준 통화 예: `EUR`
- `FX_CURRENCY`: 상대 통화 예: `USD`
- `FX_EXCHANGE`: 거래소 예: `IDEALPRO`
- `MARKET_DATA_REQ_ID`: 시장 데이터 요청 ID

### 전략 설정

- `SHORT_WINDOW`: 단기 MA 기간
- `LONG_WINDOW`: 장기 MA 기간
- `DEFAULT_ORDER_QTY`: 주문 수량
- `ENABLE_RSI_FILTER`: RSI 필터 사용 여부
- `RSI_PERIOD`: RSI 기간
- `RSI_BUY_MAX`: RSI 상한값
- `ENABLE_MA_GAP_FILTER`: MA 간격 필터 사용 여부
- `MIN_MA_GAP_PCT`: MA 간 최소 거리

### 리스크 설정

- `STOP_LOSS_PCT`: 손절 비율
- `TAKE_PROFIT_PCT`: 익절 비율
- `MAX_DAILY_LOSS`: 일일 최대 손실 한도

### 로깅 설정

- `PRINT_TICKS`: 콘솔에 tick 로그 출력 여부
- `LOG_TICKS`: CSV에 tick 로그 저장 여부
- `PRINT_FILTER_REASONS`: 진입이 막힌 이유 출력 여부
- `LOG_SYSTEM_MESSAGES`: 시스템 메시지 저장 여부
- `LOG_RISK_CHECKS`: 리스크 체크 저장 여부
- `LOG_FILE`: 로그 파일 경로

권장 조용한 설정:

```env
PRINT_TICKS=false
LOG_TICKS=false
PRINT_FILTER_REASONS=true
LOG_SYSTEM_MESSAGES=false
LOG_RISK_CHECKS=false
```

## 백테스트

샘플 백테스트 실행:

```powershell
python -m backtests.run_backtest
```

전략 비교 실행:

```powershell
python -m backtests.compare_strategies
```

비교 차트 생성:

```powershell
python -m backtests.chart_generator
```

생성 파일 예시:

- `backtests/reports/latest_report.md`
- `backtests/reports/comparison_report.md`
- `backtests/reports/comparison_chart.svg`

## 테스트

```powershell
python -m pytest tests
```

## 참고

- [legacy/README.md](C:/Users/song/Documents/fx-paper-trader/legacy/README.md):
  리팩토링 이전 단일 파일 버전에 대한 안내입니다.
- `PROJECT_SUMMARY.md`, `CASE_STUDY.md`, `ARCHITECTURE.md`, `RESULTS.md`:
  프로젝트 설명을 보조하는 문서입니다.

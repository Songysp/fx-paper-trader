# FX Paper Trader

IBKR(Interactive Brokers) FX paper trading example project입니다.

기존 `fx_trading.py` 한 파일에 있던 기능을 책임별로 나누어, Python 초보자도 읽고 수정하기 쉬운 구조로 리팩토링했습니다.

## 주요 기능

- IBKR paper trading 연결
- 실시간 tick 데이터 수신
- tick 데이터를 1분봉 OHLC로 집계
- MA(Moving Average) crossover 전략
- `orderStatus` 와 `execDetails` 분리 처리
- 체결 기준 포지션 업데이트
- stop loss / take profit / max daily loss 적용
- CSV 로그 저장
- `.env` 기반 설정 관리

## 폴더 구조

```text
fx-paper-trader/
├─ README.md
├─ requirements.txt
├─ .env.example
├─ main.py
├─ config/
│  ├─ __init__.py
│  └─ settings.py
├─ brokers/
│  ├─ __init__.py
│  └─ ibkr_client.py
├─ data/
│  ├─ __init__.py
│  ├─ tick_buffer.py
│  └─ bar_aggregator.py
├─ strategies/
│  ├─ __init__.py
│  ├─ base.py
│  └─ ma_crossover.py
├─ risk/
│  ├─ __init__.py
│  └─ risk_manager.py
├─ execution/
│  ├─ __init__.py
│  ├─ order_factory.py
│  └─ position_manager.py
├─ logging_system/
│  ├─ __init__.py
│  └─ csv_logger.py
├─ models/
│  ├─ __init__.py
│  └─ state.py
├─ utils/
│  ├─ __init__.py
│  └─ time_utils.py
└─ logs/
   └─ trading_log.csv
```

## 빠른 시작

### 1. 가상환경 생성

Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### 2. 패키지 설치

```powershell
pip install -r requirements.txt
```

### 3. 환경 변수 파일 준비

`.env.example` 을 참고해서 `.env` 파일을 만듭니다.

```powershell
Copy-Item .env.example .env
```

### 4. IBKR 설정 확인

- TWS 또는 IB Gateway 를 paper trading 계정으로 실행합니다.
- API 설정에서 socket 연결을 허용합니다.
- 기본 paper trading 포트는 보통 `7497` 입니다.

### 5. 실행

```powershell
python main.py
```

## 실행 흐름

`main.py` 의 흐름은 다음 순서입니다.

1. 설정 로드
2. CSV 로거 생성
3. 전략, 리스크, 포지션 관리자 생성
4. IBKR 클라이언트 연결
5. 실시간 tick 수신
6. tick -> 1분봉 집계
7. 새 1분봉 완성 시 리스크 검사
8. 리스크 문제가 없으면 전략 시그널 계산
9. 주문 전송
10. 실제 체결(`execDetails`) 후 포지션 반영

## 주요 클래스 설명

### `config/settings.py`

- 환경설정과 전략설정, 리스크설정을 dataclass 로 관리합니다.

### `brokers/ibkr_client.py`

- IBKR API 와 직접 통신하는 클래스입니다.
- 연결, 실시간 tick, 주문 상태, 체결 이벤트를 처리합니다.

### `data/tick_buffer.py`

- 최근 tick 데이터를 메모리에 저장합니다.

### `data/bar_aggregator.py`

- 들어오는 tick 을 1분봉 OHLC 로 묶습니다.

### `strategies/base.py`

- 새로운 전략을 추가할 때 따라야 하는 인터페이스입니다.

### `strategies/ma_crossover.py`

- 종가 목록으로 단기/장기 이동평균을 계산해 `BUY`, `SELL`, `HOLD` 시그널을 냅니다.

### `risk/risk_manager.py`

- 일일 손실 한도, stop loss, take profit 을 검사합니다.

### `execution/order_factory.py`

- IBKR 주문 객체를 생성하기 전의 주문 요청을 만듭니다.

### `execution/position_manager.py`

- 실제 체결 정보를 기준으로 포지션 상태와 실현 손익을 갱신합니다.

### `logging_system/csv_logger.py`

- 로그 파일과 `logs/` 디렉토리를 자동 생성하고 CSV 로 기록합니다.

### `models/state.py`

- Tick, Bar, PositionState, TradeState 등 공통 dataclass 를 정의합니다.

## RSI 같은 새 전략 추가 방법

1. `strategies/` 아래에 새 파일을 추가합니다.
2. `BaseStrategy` 를 상속받아 `generate_signal()` 을 구현합니다.
3. `main.py` 에서 사용할 전략 클래스를 바꿉니다.

예를 들어:

```python
from strategies.rsi_strategy import RSIStrategy

strategy = RSIStrategy(period=14, oversold=30, overbought=70)
```

## 주의사항

- 이 프로젝트는 paper trading 용 예제입니다.
- 실제 계좌에 사용하기 전에 충분한 테스트가 필요합니다.
- 주문 상태(`orderStatus`)와 체결(`execDetails`)은 다릅니다.
- 포지션은 반드시 체결 후에만 바뀌도록 구현되어 있습니다.
- stop loss / take profit 은 현재 예제에서는 새 1분봉이 완성될 때 검사합니다.
- 환율 상품의 최소 주문 단위와 거래 가능 시간은 IBKR 설정을 확인해야 합니다.

## 추천 학습 순서

초보자라면 아래 순서로 읽으면 이해가 쉽습니다.

1. `main.py`
2. `models/state.py`
3. `config/settings.py`
4. `brokers/ibkr_client.py`
5. `data/bar_aggregator.py`
6. `strategies/ma_crossover.py`
7. `risk/risk_manager.py`
8. `execution/position_manager.py`
9. `logging_system/csv_logger.py`

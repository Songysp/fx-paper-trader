# FX Paper Trader

IBKR(Interactive Brokers) API를 사용해 실시간 FX 데이터를 수신하고,
전략 신호 생성, 리스크 관리, 주문 처리, 백테스트까지 한 흐름으로 구성한
Python 기반 FX paper trading 프로젝트입니다.

이 프로젝트는 원래 하나의 `fx_trading.py` 파일에서 시작했지만, 유지보수와
확장성을 높이기 위해 초보자도 읽기 쉬운 구조로 리팩토링되었습니다.

## 한눈에 보기

- IBKR paper trading 연결
- 실시간 tick 수신 및 1분봉 OHLC 집계
- MA crossover 전략
- RSI / MA 간격 필터
- stop loss / take profit / max daily loss
- 체결 기준 포지션 업데이트
- CSV 로깅
- pytest 기반 단위 테스트
- CSV 기반 백테스트
- 전략 비교 리포트와 포트폴리오 문서

## 이 프로젝트가 보여주는 것

이 저장소는 단순히 "자동매매 코드를 작성했다"에서 끝나지 않고, 아래 역량을 함께 보여줍니다.

- 이벤트 기반 시스템 설계
- 외부 브로커 API 연동
- 전략, 실행, 리스크, 데이터 처리의 책임 분리
- 주문 상태와 실제 체결 이벤트를 구분한 상태 관리
- 기본 전략에 필터를 추가하며 개선하는 과정
- 백테스트와 비교 리포트를 통한 검증 흐름
- 포트폴리오용 문서화 능력

## 문서 구성

프로젝트를 설명하는 핵심 문서는 아래와 같습니다.

- [PROJECT_SUMMARY.md](C:/Users/song/Documents/fx-paper-trader/PROJECT_SUMMARY.md)
  프로젝트 전체를 빠르게 소개하는 요약 문서입니다.
- [RESUME_BULLETS.md](C:/Users/song/Documents/fx-paper-trader/RESUME_BULLETS.md)
  이력서나 자기소개서에 넣기 좋은 문구를 정리한 문서입니다.
- [CASE_STUDY.md](C:/Users/song/Documents/fx-paper-trader/CASE_STUDY.md)
  프로젝트의 문제, 해결 방식, 설계 포인트를 서술형으로 정리한 문서입니다.
- [ARCHITECTURE.md](C:/Users/song/Documents/fx-paper-trader/ARCHITECTURE.md)
  런타임 흐름과 각 모듈의 책임을 설명한 문서입니다.
- [RESULTS.md](C:/Users/song/Documents/fx-paper-trader/RESULTS.md)
  백테스트 비교 결과와 포트폴리오 관점의 의미를 정리한 문서입니다.

README는 위 문서들의 내용을 종합해 처음 보는 사람이 빠르게 이해할 수 있도록 구성했습니다.

## 폴더 구조

```text
fx-paper-trader/
├─ README.md
├─ PROJECT_SUMMARY.md
├─ RESUME_BULLETS.md
├─ CASE_STUDY.md
├─ ARCHITECTURE.md
├─ RESULTS.md
├─ requirements.txt
├─ .env.example
├─ main.py
├─ config/
├─ brokers/
├─ data/
├─ strategies/
├─ risk/
├─ execution/
├─ logging_system/
├─ models/
├─ utils/
├─ historical_data/
├─ backtests/
├─ tests/
├─ legacy/
└─ logs/
```

## 핵심 구조 요약

### `main.py`

전체 실행 흐름을 조립하는 진입점입니다.

1. 설정 로드
2. 로거 / 전략 / 리스크 / 브로커 객체 생성
3. IBKR 연결
4. tick 수신
5. 1분봉 생성
6. 리스크 확인
7. 전략 신호 계산
8. 주문 전송
9. 체결 기준 상태 업데이트

### `brokers/ibkr_client.py`

IBKR API와 직접 통신하는 레이어입니다.

- 연결 / 해제
- 시장 데이터 요청
- 주문 전송
- `orderStatus`
- `execDetails`
- tick 수신

### `strategies/ma_crossover.py`

전략 로직만 담당합니다.

- 종가 리스트 입력
- MA crossover 계산
- RSI 필터 적용
- MA gap 필터 적용
- `BUY`, `SELL`, `HOLD` 신호 반환

### `risk/risk_manager.py`

전략보다 먼저 리스크 조건을 확인합니다.

- stop loss
- take profit
- max daily loss

### `execution/position_manager.py`

가장 중요한 정확성 포인트입니다.

- 주문 전송 시점에는 포지션을 바꾸지 않음
- 실제 `execDetails` 체결 후에만 포지션 상태 반영
- realized PnL 계산

## 주요 기능

- IBKR paper trading 연결
- 실시간 tick 데이터 수신
- tick -> 1분봉 OHLC 집계
- MA crossover 전략 실행
- RSI / MA gap 기반 진입 필터
- `orderStatus` 와 `execDetails` 분리 처리
- 체결 기준 포지션 업데이트
- stop loss / take profit / max daily loss 적용
- CSV 로그 기록
- 단위 테스트
- 과거 데이터 백테스트
- 전략 비교 리포트

## 실행 방법

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

## `.env` 설명

### 브로커 연결 관련

- `IBKR_HOST`: 보통 `127.0.0.1`
- `IBKR_PORT`: paper trading 기본은 `7497`
- `IBKR_CLIENT_ID`: API 클라이언트 식별자
- `IBKR_CONNECT_TIMEOUT`: 연결 타임아웃
- `IBAPI_PATH`: 공식 IBKR Python API 경로

예시:

```env
IBAPI_PATH=C:\TWS API\source\pythonclient
```

### 종목 설정

- `FX_SYMBOL`: 기준 통화 예: `EUR`
- `FX_CURRENCY`: 상대 통화 예: `USD`
- `FX_EXCHANGE`: 보통 `IDEALPRO`
- `MARKET_DATA_REQ_ID`: 시장 데이터 요청 ID

### 전략 설정

- `SHORT_WINDOW`: 단기 MA 기간
- `LONG_WINDOW`: 장기 MA 기간
- `DEFAULT_ORDER_QTY`: 기본 주문 수량

### 필터 설정

- `ENABLE_RSI_FILTER`: RSI 필터 사용 여부
- `RSI_PERIOD`: RSI 계산 기간
- `RSI_BUY_MAX`: 이 값보다 RSI가 높으면 매수 보류
- `ENABLE_MA_GAP_FILTER`: MA 간격 필터 사용 여부
- `MIN_MA_GAP_PCT`: 단기 MA와 장기 MA 간 최소 거리

### 리스크 설정

- `STOP_LOSS_PCT`: 손절 비율
- `TAKE_PROFIT_PCT`: 익절 비율
- `MAX_DAILY_LOSS`: 일일 최대 허용 손실

### 로깅 설정

- `PRINT_TICKS`: 콘솔에 tick 로그 출력 여부
- `LOG_TICKS`: CSV에 tick 로그 저장 여부
- `PRINT_FILTER_REASONS`: 필터 때문에 진입이 막힌 이유 출력 여부
- `LOG_SYSTEM_MESSAGES`: 시스템 메시지 CSV 저장 여부
- `LOG_RISK_CHECKS`: bar 단위 리스크 체크 저장 여부
- `LOG_FILE`: CSV 로그 경로

권장 조용한 설정:

```env
PRINT_TICKS=false
LOG_TICKS=false
PRINT_FILTER_REASONS=true
LOG_SYSTEM_MESSAGES=false
LOG_RISK_CHECKS=false
```

## 매매 규칙

### 매수 조건

아래 조건을 모두 만족해야 매수합니다.

1. `MA 5 > MA 20`
2. RSI 필터가 켜져 있으면 `RSI <= RSI_BUY_MAX`
3. MA gap 필터가 켜져 있으면 MA 간격이 최소 기준 이상
4. 현재 롱 포지션이 없음
5. pending order 가 없음
6. 일일 손실 한도 초과 상태가 아님

### 매도 조건

- `MA 5 <= MA 20` 이면 청산
- 또는 stop loss / take profit 조건이 먼저 충족되면 청산

## 백테스트와 비교

샘플 백테스트 실행:

```powershell
python -m backtests.run_backtest
```

생성 파일:

- [latest_report.md](C:/Users/song/Documents/fx-paper-trader/backtests/reports/latest_report.md)

전략 비교 실행:

```powershell
python -m backtests.compare_strategies
```

생성 파일:

- [comparison_report.md](C:/Users/song/Documents/fx-paper-trader/backtests/reports/comparison_report.md)
- [ma_only_report.md](C:/Users/song/Documents/fx-paper-trader/backtests/reports/ma_only_report.md)
- [filtered_report.md](C:/Users/song/Documents/fx-paper-trader/backtests/reports/filtered_report.md)

비교 차트 생성:

```powershell
python -m backtests.chart_generator
```

생성 파일:

- [comparison_chart.svg](C:/Users/song/Documents/fx-paper-trader/backtests/reports/comparison_chart.svg)

## 테스트

```powershell
python -m pytest tests
```

## 포트폴리오 관점 요약

이 프로젝트는 다음 세 가지 축으로 설명하면 가장 강합니다.

1. 브로커 API와 연결된 실시간 이벤트 기반 시스템
2. 단일 파일을 모듈형 구조로 리팩토링한 설계 프로젝트
3. 전략을 구현하는 데서 끝나지 않고 백테스트와 비교 리포트까지 포함한 검증 프로젝트

즉, 단순한 자동매매 코드보다 한 단계 더 나아가
"설계 + 정확한 실행 흐름 + 전략 검증 + 문서화"를 함께 보여주는 포트폴리오로 활용할 수 있습니다.

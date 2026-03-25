# FX Paper Trader

IBKR(Interactive Brokers) FX paper trading 예제 프로젝트입니다.  
기존 단일 파일 코드를 유지보수하기 쉬운 구조로 나누고, 초보자도 읽기 쉽게 정리한 버전입니다.

## 주요 기능

- IBKR paper trading 연결
- 실시간 tick 데이터 수신
- tick -> 1분봉 OHLC 집계
- MA crossover 전략
- RSI 필터, MA gap 필터
- `orderStatus` 와 `execDetails` 분리 처리
- 체결 기준 포지션 업데이트
- stop loss / take profit / max daily loss
- CSV 로깅
- `pytest` 테스트 포함

## 빠른 시작

### 1. 가상환경 생성

```powershell
python -m venv .venv
```

### 2. 가상환경 활성화

```powershell
.\.venv\Scripts\Activate.ps1
```

PowerShell 실행 정책 오류가 나면:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

### 3. 패키지 설치

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### 4. 환경 파일 준비

```powershell
Copy-Item .env.example .env
```

### 5. 실행

```powershell
python main.py
```

## `.env` 설명

### 브로커 연결

- `IBKR_HOST`
  - IBKR TWS 또는 IB Gateway 주소
  - 보통 `127.0.0.1`
- `IBKR_PORT`
  - TWS API 포트
  - paper 계정은 보통 `7497`
- `IBKR_CLIENT_ID`
  - API 클라이언트 구분용 번호
- `IBKR_CONNECT_TIMEOUT`
  - 연결 대기 시간(초)
- `IBAPI_PATH`
  - 공식 IBKR Python API 경로
  - 예: `C:\TWS API\source\pythonclient`

### 상품 설정

- `FX_SYMBOL`
  - 기준 통화
  - 예: `EUR`
- `FX_CURRENCY`
  - 상대 통화
  - 예: `USD`
- `FX_EXCHANGE`
  - 보통 `IDEALPRO`
- `MARKET_DATA_REQ_ID`
  - 시장 데이터 요청 ID

### 전략 설정

- `SHORT_WINDOW`
  - 단기 이동평균 기간
- `LONG_WINDOW`
  - 장기 이동평균 기간
- `DEFAULT_ORDER_QTY`
  - 기본 주문 수량

### 필터 설정

- `ENABLE_RSI_FILTER`
  - `true` 면 RSI 필터 사용
- `RSI_PERIOD`
  - RSI 계산 기간
- `RSI_BUY_MAX`
  - RSI가 이 값보다 높으면 매수 보류
- `ENABLE_MA_GAP_FILTER`
  - `true` 면 MA 간격 필터 사용
- `MIN_MA_GAP_PCT`
  - 단기/장기 MA 차이가 이 값보다 작으면 매수 보류

### 로그 설정

- `PRINT_TICKS`
  - 콘솔에 tick을 한 줄씩 출력할지 여부
  - 너무 많아서 기본값은 `false`
- `LOG_TICKS`
  - CSV에 tick을 저장할지 여부
  - 분석이 어려워질 수 있어 기본값은 `false`
- `PRINT_FILTER_REASONS`
  - 봉이 완성될 때 전략 판단 이유를 콘솔에 출력
- `LOG_SYSTEM_MESSAGES`
  - CSV에 연결/시작/종료 같은 시스템 로그를 남길지 여부
- `LOG_RISK_CHECKS`
  - CSV에 매 봉마다 리스크 점검 로그를 남길지 여부

### 리스크 설정

- `STOP_LOSS_PCT`
  - 손절 비율
- `TAKE_PROFIT_PCT`
  - 익절 비율
- `MAX_DAILY_LOSS`
  - 하루 최대 손실 한도

### 파일 경로

- `LOG_FILE`
  - CSV 로그 파일 위치

## 현재 매수/매도 조건

### 매수

아래 조건을 모두 만족해야 합니다.

1. `MA 5 > MA 20`
2. RSI 필터 사용 시 `RSI <= RSI_BUY_MAX`
3. MA gap 필터 사용 시 단기/장기 MA 차이가 최소 기준 이상
4. 현재 포지션 없음
5. 대기 중 주문 없음
6. 일일 손실 한도 초과 아님

### 매도

- `MA 5 <= MA 20` 이면 청산
- 또는 stop loss / take profit 이 먼저 걸리면 리스크 규칙으로 청산

## 콘솔 로그가 너무 많을 때

현재는 아래처럼 설정하면 tick 로그가 거의 사라집니다.

```env
PRINT_TICKS=false
LOG_TICKS=false
PRINT_FILTER_REASONS=true
LOG_SYSTEM_MESSAGES=false
LOG_RISK_CHECKS=false
```

이렇게 하면 주로 아래 로그만 보게 됩니다.

- 연결 로그
- 1분봉 로그
- 전략 판단 로그
- 주문 로그
- 체결 로그

## 10285 오류가 날 때

아래 오류가 나오면:

```text
code=10285, msg=Your API version does not support fractional size rules
```

대부분 `pip install ibapi` 로 설치된 오래된 패키지가 먼저 import 되는 경우입니다.  
`.env` 의 `IBAPI_PATH` 에 공식 API 경로를 지정하는 방법을 권장합니다.

## 테스트 실행

```powershell
python -m pytest tests
```

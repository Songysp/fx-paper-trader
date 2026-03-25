# Historical Data

이 폴더에는 백테스트용 1분봉 CSV 데이터를 넣습니다.

## CSV 형식

```csv
timestamp,open,high,low,close
2026-03-20 09:00:00,1.08000,1.08020,1.07990,1.08010
```

## 컬럼 설명

- `timestamp`: 봉 시작 시각
- `open`: 시가
- `high`: 고가
- `low`: 저가
- `close`: 종가

## 사용 방법

기본 실행 파일은 아래 샘플 데이터를 읽습니다.

```powershell
python -m backtests.run_backtest
```

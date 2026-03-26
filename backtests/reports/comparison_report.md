# 전략 비교 리포트

## 요약 표

| 전략 | 거래 수 | 승률 | 순손익 | 최대 낙폭 |
| --- | ---: | ---: | ---: | ---: |
| MA Only | 2 | 50.00% | -1.0500 | -1.2000 |
| MA + Filters | 2 | 50.00% | -0.4500 | -0.6000 |

## 해석

- `MA Only`는 기본 이동평균 크로스오버 전략입니다.
- `MA + Filters`는 RSI 필터와 MA gap 필터를 추가한 버전입니다.
- 현재 샘플 데이터에서는 필터 버전이 더 작은 손실과 더 작은 최대 낙폭을 보였습니다.
- 이것이 항상 더 좋은 전략이라는 뜻은 아니지만, 전략을 비교하고 검증하는 흐름이
  프로젝트 안에 포함되어 있다는 점을 보여줍니다.

## 생성된 세부 리포트

- MA Only: `C:\Users\song\Documents\fx-paper-trader\backtests\reports\ma_only_report.md`
- MA + Filters: `C:\Users\song\Documents\fx-paper-trader\backtests\reports\filtered_report.md`

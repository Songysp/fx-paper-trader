# 결과 정리

## 비교 대상

현재 프로젝트에는 아래 두 전략 버전 비교가 포함되어 있습니다.

- `MA Only`
- `MA + Filters`

필터 버전에서는 다음이 추가됩니다.

- RSI 진입 필터
- 최소 MA 간격 필터

## 현재 비교 결과

| 전략 | 거래 수 | 승률 | 순손익 | 최대 낙폭 |
| --- | ---: | ---: | ---: | ---: |
| MA Only | 2 | 50.00% | -1.0500 | -1.2000 |
| MA + Filters | 2 | 50.00% | -0.4500 | -0.6000 |

## 관련 산출물

- [comparison_report.md](C:/Users/song/Documents/fx-paper-trader/backtests/reports/comparison_report.md)
- [comparison_chart.svg](C:/Users/song/Documents/fx-paper-trader/backtests/reports/comparison_chart.svg)

## 해석

- 현재 샘플 데이터는 작기 때문에 통계적으로 강한 결론을 내리기에는 부족합니다.
- 그럼에도 필터 버전은 손실 폭과 최대 낙폭이 더 작게 나타났습니다.
- 즉, 이 프로젝트는 단순히 전략을 구현하는 데서 끝나지 않고, 필터를 추가하고
  그 영향을 비교하는 실험 흐름까지 포함하고 있음을 보여줍니다.

## 다음 개선 방향

- 더 긴 기간의 과거 데이터 적용
- 더 많은 전략 조합 비교
- profit factor, exposure time 같은 추가 지표 도입
- 누적 손익 곡선과 거래 분포 시각화 강화

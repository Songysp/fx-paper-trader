# Results

## Comparison Snapshot

The project includes a small comparison between:

- `MA Only`
- `MA + Filters`

The filtered version enables:

- RSI entry filtering
- minimum MA-gap filtering

## Current Metrics

| Strategy | Total Trades | Win Rate | Net Profit | Max Drawdown |
| --- | ---: | ---: | ---: | ---: |
| MA Only | 2 | 50.00% | -1.0500 | -1.2000 |
| MA + Filters | 2 | 50.00% | -0.4500 | -0.6000 |

## Linked Outputs

- [comparison_report.md](C:/Users/song/Documents/fx-paper-trader/backtests/reports/comparison_report.md)
- [comparison_chart.svg](C:/Users/song/Documents/fx-paper-trader/backtests/reports/comparison_chart.svg)

## Why These Results Matter

- They show a comparison workflow, not just a single implementation.
- They provide a simple argument that filters may improve trade quality.
- They make the project easier to explain in interviews or a portfolio review.

## Next Steps

- run on larger historical datasets
- compare more strategy variants
- add richer metrics such as profit factor and exposure time

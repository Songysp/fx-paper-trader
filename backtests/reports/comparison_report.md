# Strategy Comparison Report

## Summary Table

| Strategy | Total Trades | Win Rate | Net Profit | Max Drawdown |
| --- | ---: | ---: | ---: | ---: |
| MA Only | 2 | 50.00% | -1.0500 | -1.2000 |
| MA + Filters | 2 | 50.00% | -0.4500 | -0.6000 |

## Interpretation

- `MA Only` is the plain moving-average crossover baseline.
- `MA + Filters` adds the RSI filter and MA-gap filter.
- In this sample dataset, the filtered version produced a smaller loss and a smaller drawdown.
- This does not prove the filtered strategy is always better, but it demonstrates a clean experiment-and-compare workflow.

## Generated Reports

- MA Only: `C:\Users\song\Documents\New project\fx-paper-trader\backtests\reports\ma_only_report.md`
- MA + Filters: `C:\Users\song\Documents\New project\fx-paper-trader\backtests\reports\filtered_report.md`

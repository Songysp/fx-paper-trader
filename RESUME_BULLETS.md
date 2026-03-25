# Resume Bullets

## Short Version

- Built a modular FX paper trading system in Python using the IBKR API, with live tick ingestion, 1-minute bar aggregation, strategy execution, and risk controls.
- Refactored a single-file trading script into a maintainable project structure with separated broker, strategy, execution, logging, and state-management modules.
- Added historical backtesting and strategy comparison reporting to evaluate a baseline MA crossover strategy against filtered variants.

## Stronger Technical Version

- Designed and implemented an event-driven FX paper trading application in Python on top of the IBKR API, including market data handling, order state tracking, fill-based position updates, and risk management.
- Improved maintainability by decomposing a monolithic trading script into focused modules for broker integration, bar aggregation, trading strategy logic, execution, portfolio state, and logging.
- Added experimental validation tooling by building CSV-based backtesting, trade-level performance metrics, and comparison reports for `MA Only` versus `MA + Filters` strategy variants.

## Interview-Friendly Version

- Built a Python trading system that connects to IBKR, receives live FX ticks, converts them into 1-minute bars, and executes a rules-based strategy with risk protection.
- Added strategy filters and backtesting tools to compare signal quality and drawdown between baseline and filtered trading rules.
- Focused on correctness in execution flow by ensuring positions update only after real fills, not simply after order submission.

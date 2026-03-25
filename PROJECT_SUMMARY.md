# Project Summary

## One-Line Summary

Built an IBKR FX paper trading system in Python with live market data handling, strategy filters, execution state management, and historical backtesting/reporting.

## Problem

The original project was a single-file script that mixed:

- broker callbacks
- strategy logic
- position updates
- risk checks
- logging

That structure made testing, maintenance, and strategy iteration difficult.

## Solution

Refactored the project into separate modules for:

- broker integration
- tick / bar data handling
- strategy logic
- risk management
- execution / position updates
- logging
- shared models
- tests
- backtests

## Technical Highlights

- Integrated with IBKR paper trading API
- Processed live tick data and aggregated it into 1-minute OHLC bars
- Implemented MA crossover strategy with RSI and MA-gap filters
- Ensured position changes occur only after execution fills
- Separated `orderStatus` and `execDetails`
- Added stop loss, take profit, and daily loss limit
- Added CSV logging with configurable noise control
- Added historical CSV backtesting
- Added strategy comparison reports

## Why It Matters

This project shows more than "I can write Python code."

It shows:

- system design
- asynchronous event handling
- external API integration
- trading domain awareness
- testing discipline
- experiment-driven iteration

## Suggested Demo Flow

1. Show the live trading structure in `main.py`
2. Show position updates happen only after `execDetails`
3. Show the RSI / MA-gap filter logic
4. Run the backtest
5. Open the comparison report
6. Explain what changed between `MA Only` and `MA + Filters`

# FX Paper Trader

IBKR(Interactive Brokers) FX paper trading project built for learning, experimentation, and portfolio presentation.

This project started from a single-file trading script and was refactored into a beginner-friendly structure with:

- broker integration
- live tick processing
- 1-minute bar aggregation
- MA crossover strategy
- RSI / MA-gap filters
- risk management
- execution state management
- CSV logging
- unit tests
- historical backtesting
- strategy comparison reports

## What This Project Shows

This repository is useful as a portfolio project because it demonstrates:

- event-driven trading system design
- external broker API integration
- separating strategy, execution, risk, and data responsibilities
- handling order status and fill events correctly
- adding filters to improve a simple baseline strategy
- validating ideas with backtests instead of only writing live-trading code
- generating readable reports from experiments

## Project Structure

```text
fx-paper-trader/
├─ README.md
├─ PROJECT_SUMMARY.md
├─ RESUME_BULLETS.md
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
└─ logs/
```

## Main Features

- Connect to IBKR paper trading
- Receive live tick data
- Aggregate tick data into 1-minute OHLC bars
- Run an MA crossover strategy
- Apply RSI and MA-gap entry filters
- Update positions only after real fills (`execDetails`)
- Separate `orderStatus` from execution handling
- Apply stop loss / take profit / max daily loss
- Write CSV logs
- Run historical backtests on CSV bar data
- Compare `MA Only` vs `MA + Filters`

## Quick Start

### 1. Create a virtual environment

```powershell
python -m venv .venv
```

### 2. Activate it

```powershell
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks script execution:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### 4. Copy environment settings

```powershell
Copy-Item .env.example .env
```

### 5. Run live paper trading

```powershell
python main.py
```

## `.env` Guide

### Broker connection

- `IBKR_HOST`: usually `127.0.0.1`
- `IBKR_PORT`: usually `7497` for paper trading
- `IBKR_CLIENT_ID`: API client identifier
- `IBKR_CONNECT_TIMEOUT`: connection timeout in seconds
- `IBAPI_PATH`: path to the official IBKR Python API

Example:

```env
IBAPI_PATH=C:\TWS API\source\pythonclient
```

### Instrument settings

- `FX_SYMBOL`: base currency, for example `EUR`
- `FX_CURRENCY`: quote currency, for example `USD`
- `FX_EXCHANGE`: usually `IDEALPRO`
- `MARKET_DATA_REQ_ID`: market data request id

### Strategy settings

- `SHORT_WINDOW`: short MA window
- `LONG_WINDOW`: long MA window
- `DEFAULT_ORDER_QTY`: default order size

### Filter settings

- `ENABLE_RSI_FILTER`: enable or disable RSI entry filter
- `RSI_PERIOD`: RSI calculation period
- `RSI_BUY_MAX`: skip buy if RSI is above this value
- `ENABLE_MA_GAP_FILTER`: enable or disable MA spread filter
- `MIN_MA_GAP_PCT`: minimum distance between short MA and long MA for buy entries

### Logging settings

- `PRINT_TICKS`: print tick-by-tick logs to console
- `LOG_TICKS`: store tick rows in CSV
- `PRINT_FILTER_REASONS`: show why a strategy decision was blocked
- `LOG_SYSTEM_MESSAGES`: store system messages in CSV
- `LOG_RISK_CHECKS`: store every bar-level risk check in CSV

Recommended quiet logging setup:

```env
PRINT_TICKS=false
LOG_TICKS=false
PRINT_FILTER_REASONS=true
LOG_SYSTEM_MESSAGES=false
LOG_RISK_CHECKS=false
```

### Risk settings

- `STOP_LOSS_PCT`: stop loss percentage
- `TAKE_PROFIT_PCT`: take profit percentage
- `MAX_DAILY_LOSS`: maximum daily realized loss before trading stops

### File path

- `LOG_FILE`: CSV log path

## Trading Rules

### Buy

The system buys only when all of these are true:

1. `MA 5 > MA 20`
2. If RSI filter is enabled, `RSI <= RSI_BUY_MAX`
3. If MA-gap filter is enabled, the MA spread is large enough
4. No current long position
5. No pending order
6. Daily loss limit not breached

### Sell

- Sell when `MA 5 <= MA 20`
- Or exit earlier if stop loss / take profit triggers

## Live Trading Notes

- Position state changes only after actual fills
- `orderStatus` and `execDetails` are intentionally handled separately
- Tick logs are noisy by nature, so they are disabled by default

## Backtesting

Run the sample backtest:

```powershell
python -m backtests.run_backtest
```

Generated report:

- [latest_report.md](C:/Users/song/Documents/fx-paper-trader/backtests/reports/latest_report.md)

Run strategy comparison:

```powershell
python -m backtests.compare_strategies
```

Generated reports:

- [comparison_report.md](C:/Users/song/Documents/fx-paper-trader/backtests/reports/comparison_report.md)
- [ma_only_report.md](C:/Users/song/Documents/fx-paper-trader/backtests/reports/ma_only_report.md)
- [filtered_report.md](C:/Users/song/Documents/fx-paper-trader/backtests/reports/filtered_report.md)

## Tests

```powershell
python -m pytest tests
```

## Portfolio Positioning

This project is strongest when presented as:

- a broker-integrated algorithmic trading system
- a refactoring and system design project
- a strategy validation project with experiment reporting

It becomes much stronger when paired with:

- real historical datasets
- longer backtest windows
- parameter comparison results
- a short write-up explaining trade-offs and findings

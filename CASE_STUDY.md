# Case Study

## Overview

This project started as a single-file Interactive Brokers FX paper trading
script. The goal of the refactor was to turn that prototype into a maintainable
and explainable system that can be shown as a portfolio project.

## Problem

The original script mixed too many responsibilities in one file:

- broker callbacks
- signal generation
- risk checks
- order state
- position updates
- logging

That made the code harder to maintain, extend, and explain.

## Solution

The project was reorganized into focused modules:

- `brokers/` for IBKR connectivity and callbacks
- `data/` for ticks and bar aggregation
- `strategies/` for signal generation
- `risk/` for stop loss, take profit, and daily loss controls
- `execution/` for order creation and fill-based position updates
- `logging_system/` for CSV logs
- `backtests/` for historical evaluation

## Key Decisions

### Fill-based state updates

Position state is not changed when an order is submitted. It changes only when
an execution callback is received. That keeps live behavior closer to real
broker behavior and avoids false assumptions.

### Strategy isolation

The strategy module only depends on close prices and position state. It does
not know about IBKR request IDs, contracts, or callbacks.

### Risk before entry

On each completed bar, risk logic runs before new strategy entries are allowed.

### Experimentation workflow

The repository does not stop at live execution. It also includes backtesting,
comparison reports, and chart generation so the strategy can be discussed with
evidence.

## What Improved

- readability for beginners
- ability to add new strategies or filters
- easier testing of core logic
- clearer portfolio narrative

## Presentation Angle

This project is strongest when presented as:

1. a broker-integrated event-driven system
2. a refactoring and system design project
3. a trading strategy validation workflow

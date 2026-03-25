"""Tests for the MA crossover strategy."""

from models.state import PositionState
from strategies.ma_crossover import MovingAverageCrossoverStrategy


def test_ma_crossover_returns_hold_when_not_enough_bars() -> None:
    """The strategy should wait until enough bars exist for the long MA."""
    strategy = MovingAverageCrossoverStrategy(
        short_window=3,
        long_window=5,
        enable_rsi_filter=False,
        enable_ma_gap_filter=False,
    )

    signal = strategy.generate_signal(
        close_prices=[1.0, 2.0, 3.0, 4.0],
        position=PositionState(),
    )

    assert signal == "HOLD"


def test_ma_crossover_returns_buy_when_short_ma_above_long_ma() -> None:
    """A higher short MA should generate a buy signal."""
    strategy = MovingAverageCrossoverStrategy(
        short_window=3,
        long_window=5,
        enable_rsi_filter=False,
        enable_ma_gap_filter=False,
    )

    signal = strategy.generate_signal(
        close_prices=[1.0, 2.0, 3.0, 4.0, 10.0],
        position=PositionState(),
    )

    assert signal == "BUY"


def test_ma_crossover_returns_sell_when_short_ma_not_above_long_ma() -> None:
    """A lower or equal short MA should generate a sell signal."""
    strategy = MovingAverageCrossoverStrategy(
        short_window=3,
        long_window=5,
        enable_rsi_filter=False,
        enable_ma_gap_filter=False,
    )

    signal = strategy.generate_signal(
        close_prices=[10.0, 9.0, 8.0, 7.0, 6.0],
        position=PositionState(side="LONG", quantity=1000, avg_entry_price=8.0),
    )

    assert signal == "SELL"


def test_ma_crossover_rsi_filter_blocks_overheated_buy_signal() -> None:
    """When RSI is too high, the strategy should skip a buy entry."""
    strategy = MovingAverageCrossoverStrategy(
        short_window=3,
        long_window=5,
        enable_rsi_filter=True,
        rsi_period=5,
        rsi_buy_max=60.0,
        enable_ma_gap_filter=False,
    )

    signal = strategy.generate_signal(
        close_prices=[1.0, 2.0, 3.0, 4.0, 5.0, 6.0],
        position=PositionState(),
    )

    assert signal == "HOLD"


def test_ma_crossover_ma_gap_filter_blocks_weak_buy_signal() -> None:
    """When the MA spread is too small, the strategy should skip the buy."""
    strategy = MovingAverageCrossoverStrategy(
        short_window=2,
        long_window=4,
        enable_rsi_filter=False,
        enable_ma_gap_filter=True,
        min_ma_gap_pct=0.01,
    )

    signal = strategy.generate_signal(
        close_prices=[100.0, 100.0, 100.01, 100.02],
        position=PositionState(),
    )

    assert signal == "HOLD"

"""Tests for the bar aggregator."""

from datetime import datetime

from data.bar_aggregator import BarAggregator
from models.state import Tick


def test_bar_aggregator_builds_correct_ohlc_for_one_minute() -> None:
    """The aggregator should return correct OHLC values when the minute changes."""
    aggregator = BarAggregator()

    ticks = [
        Tick(price=100.0, timestamp=datetime(2026, 3, 25, 9, 0, 1), tick_type=4),
        Tick(price=105.0, timestamp=datetime(2026, 3, 25, 9, 0, 10), tick_type=4),
        Tick(price=99.0, timestamp=datetime(2026, 3, 25, 9, 0, 30), tick_type=4),
        Tick(price=102.0, timestamp=datetime(2026, 3, 25, 9, 0, 59), tick_type=4),
        Tick(price=103.0, timestamp=datetime(2026, 3, 25, 9, 1, 0), tick_type=4),
    ]

    completed_bar = None
    for tick in ticks:
        completed_bar = aggregator.update(tick) or completed_bar

    assert completed_bar is not None
    assert completed_bar.timestamp == datetime(2026, 3, 25, 9, 0, 0)
    assert completed_bar.open == 100.0
    assert completed_bar.high == 105.0
    assert completed_bar.low == 99.0
    assert completed_bar.close == 102.0


def test_bar_aggregator_flush_returns_current_bar_without_new_minute() -> None:
    """Flush should return the in-progress bar using the latest collected prices."""
    aggregator = BarAggregator()

    aggregator.update(Tick(price=10.0, timestamp=datetime(2026, 3, 25, 9, 5, 1), tick_type=4))
    aggregator.update(Tick(price=12.0, timestamp=datetime(2026, 3, 25, 9, 5, 20), tick_type=4))
    aggregator.update(Tick(price=11.0, timestamp=datetime(2026, 3, 25, 9, 5, 58), tick_type=4))

    flushed_bar = aggregator.flush()

    assert flushed_bar is not None
    assert flushed_bar.timestamp == datetime(2026, 3, 25, 9, 5, 0)
    assert flushed_bar.open == 10.0
    assert flushed_bar.high == 12.0
    assert flushed_bar.low == 10.0
    assert flushed_bar.close == 11.0

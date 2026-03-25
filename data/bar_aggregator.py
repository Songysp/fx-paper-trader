"""Convert ticks into 1-minute OHLC bars."""

from __future__ import annotations

from typing import List, Optional

from models.state import Bar, Tick
from utils.time_utils import floor_to_minute


class BarAggregator:
    """Aggregate live ticks into one-minute bars."""

    def __init__(self) -> None:
        """Initialize the current working bar state."""
        self.current_minute = None
        self.current_prices: List[float] = []

    def update(self, tick: Tick) -> Optional[Bar]:
        """Add one tick and return a completed bar when the minute changes."""
        tick_minute = floor_to_minute(tick.timestamp)

        if self.current_minute is None:
            self.current_minute = tick_minute

        if tick_minute == self.current_minute:
            self.current_prices.append(tick.price)
            return None

        completed_bar = self._build_bar()
        self.current_minute = tick_minute
        self.current_prices = [tick.price]
        return completed_bar

    def flush(self) -> Optional[Bar]:
        """Return the current unfinished bar if the program is shutting down."""
        return self._build_bar()

    def _build_bar(self) -> Optional[Bar]:
        """Build an OHLC bar from the currently stored prices."""
        if self.current_minute is None or not self.current_prices:
            return None

        return Bar(
            timestamp=self.current_minute,
            open=self.current_prices[0],
            high=max(self.current_prices),
            low=min(self.current_prices),
            close=self.current_prices[-1],
        )

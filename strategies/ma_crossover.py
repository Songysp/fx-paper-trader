"""Simple moving average crossover strategy."""

from __future__ import annotations

from typing import List, Optional, Tuple

from models.state import PositionState
from strategies.base import BaseStrategy


class MovingAverageCrossoverStrategy(BaseStrategy):
    """Generate signals from a short MA and a long MA."""

    name = "ma_crossover"

    def __init__(self, short_window: int, long_window: int) -> None:
        """Store MA window sizes."""
        self.short_window = short_window
        self.long_window = long_window

    def generate_signal(self, close_prices: List[float], position: PositionState) -> str:
        """Return a simple MA crossover signal."""
        short_ma, long_ma = self.get_latest_indicator_values(close_prices)
        if short_ma is None or long_ma is None:
            return "HOLD"
        return "BUY" if short_ma > long_ma else "SELL"

    def get_latest_indicator_values(
        self,
        close_prices: List[float],
    ) -> Tuple[Optional[float], Optional[float]]:
        """Calculate the most recent short and long moving average values."""
        if len(close_prices) < self.long_window:
            return None, None

        short_prices = close_prices[-self.short_window :]
        long_prices = close_prices[-self.long_window :]
        short_ma = sum(short_prices) / len(short_prices)
        long_ma = sum(long_prices) / len(long_prices)
        return short_ma, long_ma

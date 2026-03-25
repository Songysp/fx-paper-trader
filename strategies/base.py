"""Base interface for all trading strategies."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Optional, Tuple

from models.state import PositionState


class BaseStrategy(ABC):
    """Abstract base class for all strategies."""

    name: str = "base"

    @abstractmethod
    def generate_signal(self, close_prices: List[float], position: PositionState) -> str:
        """Return one of `BUY`, `SELL`, or `HOLD`."""

    @abstractmethod
    def get_latest_indicator_values(
        self,
        close_prices: List[float],
    ) -> Tuple[Optional[float], Optional[float]]:
        """Return the latest indicator values used for logging and debugging."""

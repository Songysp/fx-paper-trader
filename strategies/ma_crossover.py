"""Simple moving average crossover strategy with optional entry filters."""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from models.state import PositionState
from strategies.base import BaseStrategy


class MovingAverageCrossoverStrategy(BaseStrategy):
    """Generate signals from a short MA and a long MA.

    Optional filters:
    - RSI filter: avoid buying when the market already looks too overheated.
    - MA gap filter: avoid buying when the short/long MA difference is too small.
    """

    name = "ma_crossover"

    def __init__(
        self,
        short_window: int,
        long_window: int,
        enable_rsi_filter: bool = True,
        rsi_period: int = 14,
        rsi_buy_max: float = 65.0,
        enable_ma_gap_filter: bool = True,
        min_ma_gap_pct: float = 0.00005,
    ) -> None:
        """Store MA settings and optional entry filter settings."""
        self.short_window = short_window
        self.long_window = long_window
        self.enable_rsi_filter = enable_rsi_filter
        self.rsi_period = rsi_period
        self.rsi_buy_max = rsi_buy_max
        self.enable_ma_gap_filter = enable_ma_gap_filter
        self.min_ma_gap_pct = min_ma_gap_pct

    def generate_signal(self, close_prices: List[float], position: PositionState) -> str:
        """Return a filtered MA crossover signal."""
        return self.evaluate_signal_details(close_prices)["signal"]

    def evaluate_signal_details(self, close_prices: List[float]) -> Dict[str, Optional[float]]:
        """Return the final signal with indicator values and a human-readable reason."""
        short_ma, long_ma = self.get_latest_indicator_values(close_prices)
        if short_ma is None or long_ma is None:
            return {
                "signal": "HOLD",
                "short_ma": None,
                "long_ma": None,
                "rsi": None,
                "reason": "Not enough bars yet",
            }

        raw_signal = "BUY" if short_ma > long_ma else "SELL"
        if raw_signal == "SELL":
            return {
                "signal": "SELL",
                "short_ma": short_ma,
                "long_ma": long_ma,
                "rsi": self.compute_rsi(close_prices),
                "reason": "Short MA is below or equal to Long MA",
            }

        if self.enable_ma_gap_filter:
            ma_gap_pct = self.compute_ma_gap_pct(short_ma, long_ma)
            if ma_gap_pct < self.min_ma_gap_pct:
                return {
                    "signal": "HOLD",
                    "short_ma": short_ma,
                    "long_ma": long_ma,
                    "rsi": self.compute_rsi(close_prices),
                    "reason": (
                        f"MA gap too small ({ma_gap_pct:.4%} < {self.min_ma_gap_pct:.4%})"
                    ),
                }

        if self.enable_rsi_filter:
            rsi_value = self.compute_rsi(close_prices)
            if rsi_value is None:
                return {
                    "signal": "HOLD",
                    "short_ma": short_ma,
                    "long_ma": long_ma,
                    "rsi": None,
                    "reason": "Not enough bars for RSI filter yet",
                }
            if rsi_value > self.rsi_buy_max:
                return {
                    "signal": "HOLD",
                    "short_ma": short_ma,
                    "long_ma": long_ma,
                    "rsi": rsi_value,
                    "reason": f"RSI too high for entry ({rsi_value:.2f} > {self.rsi_buy_max:.2f})",
                }

        return {
            "signal": "BUY",
            "short_ma": short_ma,
            "long_ma": long_ma,
            "rsi": self.compute_rsi(close_prices),
            "reason": "MA crossover and filters passed",
        }

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

    def compute_rsi(self, close_prices: List[float]) -> Optional[float]:
        """Calculate RSI using recent close prices.

        This implementation is intentionally simple so beginners can follow it.
        """
        if len(close_prices) < self.rsi_period + 1:
            return None

        recent_prices = close_prices[-(self.rsi_period + 1) :]
        gains: List[float] = []
        losses: List[float] = []

        for previous_price, current_price in zip(recent_prices, recent_prices[1:]):
            change = current_price - previous_price
            gains.append(max(change, 0.0))
            losses.append(abs(min(change, 0.0)))

        average_gain = sum(gains) / self.rsi_period
        average_loss = sum(losses) / self.rsi_period

        if average_loss == 0:
            return 100.0

        relative_strength = average_gain / average_loss
        return 100.0 - (100.0 / (1.0 + relative_strength))

    def compute_ma_gap_pct(self, short_ma: float, long_ma: float) -> float:
        """Return the percent distance between short MA and long MA."""
        if long_ma == 0:
            return 0.0
        return abs(short_ma - long_ma) / long_ma

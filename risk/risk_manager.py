"""Risk rules for stop loss, take profit, and max daily loss."""

from __future__ import annotations

from datetime import datetime

from config.settings import RiskSettings
from models.state import PositionState


class RiskManager:
    """Evaluate account-level and position-level risk rules."""

    def __init__(self, settings: RiskSettings) -> None:
        """Initialize risk settings and the current daily state."""
        self.settings = settings
        self.daily_realized_pnl = 0.0
        self.trading_halted = False
        self.current_trading_date = datetime.now().date()

    def reset_daily_state_if_needed(self) -> None:
        """Reset daily loss tracking when the date changes."""
        today = datetime.now().date()
        if today != self.current_trading_date:
            self.current_trading_date = today
            self.daily_realized_pnl = 0.0
            self.trading_halted = False

    def register_realized_pnl(self, realized_pnl: float) -> None:
        """Add realized PnL from a completed execution."""
        self.reset_daily_state_if_needed()
        self.daily_realized_pnl += realized_pnl

    def check(self, position: PositionState, latest_price: float) -> str:
        """Return one of `HALT`, `STOP_LOSS`, `TAKE_PROFIT`, or `OK`."""
        self.reset_daily_state_if_needed()

        if self.daily_realized_pnl <= self.settings.max_daily_loss:
            self.trading_halted = True
            return "HALT"

        if position.is_long and position.avg_entry_price is not None:
            pnl_pct = (latest_price - position.avg_entry_price) / position.avg_entry_price

            if pnl_pct <= -self.settings.stop_loss_pct:
                return "STOP_LOSS"

            if pnl_pct >= self.settings.take_profit_pct:
                return "TAKE_PROFIT"

        return "OK"

"""Tests for the risk manager."""

from config.settings import RiskSettings
from models.state import PositionState
from risk.risk_manager import RiskManager


def test_risk_manager_returns_ok_when_no_limits_are_hit() -> None:
    """The risk manager should allow trading when all values are normal."""
    risk_manager = RiskManager(
        RiskSettings(
            stop_loss_pct=0.01,
            take_profit_pct=0.02,
            max_daily_loss=-500.0,
        )
    )

    result = risk_manager.check(
        position=PositionState(side="LONG", quantity=1000, avg_entry_price=100.0),
        latest_price=100.5,
    )

    assert result == "OK"


def test_risk_manager_prioritizes_daily_loss_halt_over_strategy() -> None:
    """Daily loss limit should stop trading before strategy logic runs."""
    risk_manager = RiskManager(
        RiskSettings(
            stop_loss_pct=0.01,
            take_profit_pct=0.02,
            max_daily_loss=-100.0,
        )
    )
    risk_manager.daily_realized_pnl = -150.0

    result = risk_manager.check(
        position=PositionState(side="LONG", quantity=1000, avg_entry_price=100.0),
        latest_price=105.0,
    )

    assert result == "HALT"
    assert risk_manager.trading_halted is True


def test_risk_manager_returns_stop_loss_when_price_drops_enough() -> None:
    """A large enough loss on the open position should trigger stop loss."""
    risk_manager = RiskManager(
        RiskSettings(
            stop_loss_pct=0.01,
            take_profit_pct=0.03,
            max_daily_loss=-500.0,
        )
    )

    result = risk_manager.check(
        position=PositionState(side="LONG", quantity=1000, avg_entry_price=100.0),
        latest_price=98.5,
    )

    assert result == "STOP_LOSS"


def test_risk_manager_returns_take_profit_when_price_rises_enough() -> None:
    """A large enough gain on the open position should trigger take profit."""
    risk_manager = RiskManager(
        RiskSettings(
            stop_loss_pct=0.01,
            take_profit_pct=0.03,
            max_daily_loss=-500.0,
        )
    )

    result = risk_manager.check(
        position=PositionState(side="LONG", quantity=1000, avg_entry_price=100.0),
        latest_price=103.5,
    )

    assert result == "TAKE_PROFIT"

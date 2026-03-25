"""Tests for execution.position_manager.PositionManager."""

from execution.position_manager import PositionManager
from models.state import ExecutionReport, PositionState


def _execution(side: str, quantity: float, price: float) -> ExecutionReport:
    """Create a minimal execution report for tests."""
    return ExecutionReport(
        symbol="EUR",
        side=side,
        quantity=quantity,
        price=price,
        order_id=1,
        execution_id=f"exec-{side}-{quantity}-{price}",
    )


def test_apply_execution_handles_single_buy_fill() -> None:
    """A single BOT fill should open a LONG position with matching qty and price."""
    manager = PositionManager()
    position = PositionState()

    realized_pnl = manager.apply_execution(position=position, execution=_execution("BOT", 1000, 1.10))

    assert realized_pnl == 0.0
    assert position.side == "LONG"
    assert position.quantity == 1000
    assert position.avg_entry_price == 1.10


def test_apply_execution_handles_two_partial_buy_fills() -> None:
    """Two BOT partial fills should accumulate quantity into one LONG position."""
    manager = PositionManager()
    position = PositionState()

    manager.apply_execution(position=position, execution=_execution("BOT", 600, 1.1000))
    manager.apply_execution(position=position, execution=_execution("BOT", 400, 1.1200))

    assert position.side == "LONG"
    assert position.quantity == 1000


def test_apply_execution_calculates_weighted_average_entry_price() -> None:
    """Partial BOT fills should maintain weighted-average entry price."""
    manager = PositionManager()
    position = PositionState()

    manager.apply_execution(position=position, execution=_execution("BOT", 600, 1.1000))
    manager.apply_execution(position=position, execution=_execution("BOT", 400, 1.1200))

    expected_avg = ((600 * 1.1000) + (400 * 1.1200)) / 1000
    assert position.avg_entry_price is not None
    assert position.avg_entry_price == expected_avg


def test_apply_execution_calculates_realized_pnl_on_sell_fill() -> None:
    """SLD fill should compute realized PnL from avg entry and closed quantity."""
    manager = PositionManager()
    position = PositionState(side="LONG", quantity=1000, avg_entry_price=1.1000)

    realized_pnl = manager.apply_execution(position=position, execution=_execution("SLD", 1000, 1.1300))

    assert realized_pnl == (1.1300 - 1.1000) * 1000


def test_apply_execution_resets_position_after_full_sell() -> None:
    """A full SLD close should reset position to FLAT and clear entry price."""
    manager = PositionManager()
    position = PositionState(side="LONG", quantity=1000, avg_entry_price=1.1000)

    manager.apply_execution(position=position, execution=_execution("SLD", 1000, 1.1300))

    assert position.side == "FLAT"
    assert position.quantity == 0.0
    assert position.avg_entry_price is None

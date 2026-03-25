"""Update position state only after real executions arrive."""

from __future__ import annotations

from models.state import ExecutionReport, PositionState


class PositionManager:
    """Apply fills to the current position state."""

    def apply_execution(self, position: PositionState, execution: ExecutionReport) -> float:
        """Apply one execution report and return realized PnL."""
        side = execution.side.upper()

        if side == "BOT":
            self._apply_buy_execution(position, execution)
            return 0.0

        if side == "SLD":
            realized_pnl = 0.0

            if position.avg_entry_price is not None and position.quantity > 0:
                closed_quantity = min(position.quantity, execution.quantity)
                realized_pnl = (execution.price - position.avg_entry_price) * closed_quantity
                remaining_quantity = max(position.quantity - execution.quantity, 0.0)

                if remaining_quantity == 0:
                    position.side = "FLAT"
                    position.quantity = 0.0
                    position.avg_entry_price = None
                else:
                    position.quantity = remaining_quantity

            return realized_pnl

        return 0.0

    def _apply_buy_execution(self, position: PositionState, execution: ExecutionReport) -> None:
        """Update the position for a buy fill.

        This method supports repeated partial buy fills by updating the
        weighted average entry price.
        """
        if not position.is_long or position.avg_entry_price is None:
            position.side = "LONG"
            position.quantity = execution.quantity
            position.avg_entry_price = execution.price
            return

        total_cost = (position.avg_entry_price * position.quantity) + (execution.price * execution.quantity)
        total_quantity = position.quantity + execution.quantity
        position.side = "LONG"
        position.quantity = total_quantity
        position.avg_entry_price = total_cost / total_quantity

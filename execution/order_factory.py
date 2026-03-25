"""Factory for simple order request objects."""

from __future__ import annotations

from models.state import OrderRequest


class OrderFactory:
    """Build simple order request dataclasses."""

    def market_order(self, action: str, quantity: float) -> OrderRequest:
        """Create a market order request."""
        return OrderRequest(
            action=action,
            quantity=quantity,
            order_type="MKT",
        )

    def limit_order(self, action: str, quantity: float, limit_price: float) -> OrderRequest:
        """Create a limit order request."""
        return OrderRequest(
            action=action,
            quantity=quantity,
            order_type="LMT",
            limit_price=limit_price,
        )

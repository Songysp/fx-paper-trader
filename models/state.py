"""Shared dataclasses for ticks, bars, orders, and positions."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Tick:
    """One real-time tick from the broker."""

    price: float
    timestamp: datetime
    tick_type: int

    @classmethod
    def now(cls, price: float, tick_type: int) -> "Tick":
        """Create a tick using the current local time."""
        return cls(price=price, timestamp=datetime.now(), tick_type=tick_type)


@dataclass
class Bar:
    """One completed 1-minute OHLC bar."""

    timestamp: datetime
    open: float
    high: float
    low: float
    close: float


@dataclass
class PositionState:
    """Current trading position."""

    side: str = "FLAT"
    quantity: float = 0.0
    avg_entry_price: Optional[float] = None

    @property
    def is_long(self) -> bool:
        """Return True when there is an active long position."""
        return self.side == "LONG" and self.quantity > 0


@dataclass
class TradeState:
    """Runtime state related to broker connection and orders."""

    next_order_id: Optional[int] = None
    connected_ok: bool = False
    pending_order: bool = False
    active_order_id: Optional[int] = None
    active_order_is_filled: bool = False
    active_order_has_execution: bool = False
    last_order_action: Optional[str] = None
    last_order_quantity: float = 0.0
    last_execution_price: Optional[float] = None


@dataclass
class OrderRequest:
    """Simple order request before it becomes an IBKR order object."""

    action: str
    quantity: float
    order_type: str
    limit_price: Optional[float] = None


@dataclass
class OrderStatusEvent:
    """Order status event received from the broker."""

    order_id: int
    status: str
    filled: float
    remaining: float
    avg_fill_price: float
    last_fill_price: float


@dataclass
class ExecutionReport:
    """Execution event received when a fill really happens."""

    symbol: str
    side: str
    quantity: float
    price: float
    order_id: int
    execution_id: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

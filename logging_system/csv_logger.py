"""CSV logger used by the trading application."""

from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path
from typing import Optional

from models.state import Bar, ExecutionReport, OrderStatusEvent, PositionState


class CSVTradeLogger:
    """Write trading events into a CSV file."""

    def __init__(self, log_file: str) -> None:
        """Create the logs directory and CSV file if they do not exist."""
        self.log_path = Path(log_file)
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize_file()

    def _initialize_file(self) -> None:
        """Write the CSV header only once."""
        if self.log_path.exists() and self.log_path.stat().st_size > 0:
            return

        with self.log_path.open("w", newline="", encoding="utf-8-sig") as file:
            writer = csv.writer(file)
            writer.writerow(
                [
                    "timestamp",
                    "event_type",
                    "price",
                    "signal",
                    "position_side",
                    "position_qty",
                    "entry_price",
                    "daily_realized_pnl",
                    "message",
                ]
            )

    def log_row(
        self,
        event_type: str,
        price: Optional[float] = None,
        signal: Optional[str] = None,
        position_side: Optional[str] = None,
        position_qty: Optional[float] = None,
        entry_price: Optional[float] = None,
        daily_realized_pnl: Optional[float] = None,
        message: str = "",
    ) -> None:
        """Write one generic row to the CSV log."""
        with self.log_path.open("a", newline="", encoding="utf-8-sig") as file:
            writer = csv.writer(file)
            writer.writerow(
                [
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    event_type,
                    price,
                    signal,
                    position_side,
                    position_qty,
                    entry_price,
                    daily_realized_pnl,
                    message,
                ]
            )

    def log_system(self, message: str) -> None:
        """Log a system message."""
        self.log_row(event_type="SYSTEM", message=message)

    def log_error(self, message: str) -> None:
        """Log an error message."""
        self.log_row(event_type="ERROR", message=message)

    def log_tick(self, price: float, tick_type: int) -> None:
        """Log an incoming tick."""
        self.log_row(event_type="TICK", price=price, message=f"tickType={tick_type}")

    def log_bar(self, bar: Bar) -> None:
        """Log a completed bar."""
        self.log_row(
            event_type="BAR",
            price=bar.close,
            message=(
                f"time={bar.timestamp}, open={bar.open}, high={bar.high}, "
                f"low={bar.low}, close={bar.close}"
            ),
        )

    def log_signal(
        self,
        price: float,
        signal: str,
        short_ma: Optional[float],
        long_ma: Optional[float],
        position_side: str,
    ) -> None:
        """Log a strategy signal and the latest indicator values."""
        short_text = f"{short_ma:.4f}" if short_ma is not None else "None"
        long_text = f"{long_ma:.4f}" if long_ma is not None else "None"
        self.log_row(
            event_type="SIGNAL",
            price=price,
            signal=signal,
            position_side=position_side,
            message=f"short_ma={short_text}, long_ma={long_text}",
        )

    def log_order(
        self,
        action: str,
        quantity: float,
        order_type: str,
        latest_price: Optional[float],
        limit_price: Optional[float],
        order_id: int,
    ) -> None:
        """Log an order submission."""
        limit_text = f", limit_price={limit_price}" if limit_price is not None else ""
        self.log_row(
            event_type="ORDER",
            price=latest_price,
            signal=action,
            message=f"orderId={order_id}, type={order_type}, qty={quantity}{limit_text}",
        )

    def log_order_status(self, event: OrderStatusEvent) -> None:
        """Log a broker order status update."""
        self.log_row(
            event_type="ORDER_STATUS",
            price=event.avg_fill_price,
            message=(
                f"orderId={event.order_id}, status={event.status}, "
                f"filled={event.filled}, remaining={event.remaining}"
            ),
        )

    def log_execution(
        self,
        execution: ExecutionReport,
        position: PositionState,
        realized_pnl: float,
        daily_realized_pnl: float,
    ) -> None:
        """Log a real execution fill and the updated position."""
        self.log_row(
            event_type="EXECUTION",
            price=execution.price,
            signal=execution.side,
            position_side=position.side,
            position_qty=position.quantity,
            entry_price=position.avg_entry_price,
            daily_realized_pnl=daily_realized_pnl,
            message=(
                f"orderId={execution.order_id}, execution_id={execution.execution_id}, "
                f"qty={execution.quantity}, realized_pnl={realized_pnl:.2f}"
            ),
        )

    def log_risk_check(self, status: str, latest_price: float, daily_realized_pnl: float) -> None:
        """Log the result of a risk check."""
        self.log_row(
            event_type="RISK",
            price=latest_price,
            signal=status,
            daily_realized_pnl=daily_realized_pnl,
            message=f"risk_status={status}",
        )

"""IBKR client wrapper responsible for connection, market data, and order callbacks."""

from __future__ import annotations

import threading
import time
from typing import Callable, Optional

from ibapi.client import EClient
from ibapi.contract import Contract
from ibapi.order import Order
from ibapi.wrapper import EWrapper

from config.settings import BrokerSettings
from models.state import ExecutionReport, OrderRequest, OrderStatusEvent, Tick, TradeState


class IBKRClient(EWrapper, EClient):
    """Thin wrapper around the IBKR API with simple Python callbacks."""

    def __init__(self, settings: BrokerSettings, logger) -> None:
        """Initialize broker settings, runtime state, and callback holders."""
        EClient.__init__(self, self)
        self.settings = settings
        self.logger = logger
        self.trade_state = TradeState()
        self._connected_event = threading.Event()
        self._api_thread: Optional[threading.Thread] = None
        self._tick_handler: Optional[Callable[[Tick], None]] = None
        self._order_status_handler: Optional[Callable[[OrderStatusEvent], None]] = None
        self._execution_handler: Optional[Callable[[ExecutionReport], None]] = None

    def set_tick_handler(self, handler: Callable[[Tick], None]) -> None:
        """Register the callback for real-time tick updates."""
        self._tick_handler = handler

    def set_order_status_handler(self, handler: Callable[[OrderStatusEvent], None]) -> None:
        """Register the callback for order status updates."""
        self._order_status_handler = handler

    def set_execution_handler(self, handler: Callable[[ExecutionReport], None]) -> None:
        """Register the callback for actual fill events."""
        self._execution_handler = handler

    def connect_and_start(self) -> bool:
        """Connect to IBKR and start the API event loop in a background thread."""
        self.connect(self.settings.host, self.settings.port, clientId=self.settings.client_id)
        self._api_thread = threading.Thread(target=self.run, daemon=True)
        self._api_thread.start()

        connected = self._connected_event.wait(timeout=self.settings.connect_timeout)
        return connected and self.trade_state.connected_ok

    def build_fx_contract(self) -> Contract:
        """Create an IBKR FX contract from configured settings."""
        contract = Contract()
        contract.symbol = self.settings.symbol
        contract.secType = "CASH"
        contract.currency = self.settings.currency
        contract.exchange = self.settings.exchange
        return contract

    def request_market_data(self, contract: Contract) -> None:
        """Request real-time market data for the configured FX contract."""
        self.reqMktData(self.settings.market_data_req_id, contract, "", False, False, [])

    def submit_order(
        self,
        contract: Contract,
        order_request: OrderRequest,
        latest_price: Optional[float],
    ) -> None:
        """Send an order to IBKR and mark runtime state as pending."""
        if self.trade_state.next_order_id is None:
            print("[WARN] next_order_id is not ready.")
            self.logger.log_error("next_order_id is not ready.")
            return

        order = self._build_ib_order(order_request)
        order_id = self.trade_state.next_order_id

        self.placeOrder(order_id, contract, order)

        self.trade_state.pending_order = True
        self.trade_state.active_order_id = order_id
        self.trade_state.active_order_is_filled = False
        self.trade_state.active_order_has_execution = False
        self.trade_state.last_order_action = order_request.action
        self.trade_state.last_order_quantity = order_request.quantity
        self.trade_state.next_order_id += 1

        self.logger.log_order(
            action=order_request.action,
            quantity=order_request.quantity,
            order_type=order_request.order_type,
            latest_price=latest_price,
            limit_price=order_request.limit_price,
            order_id=order_id,
        )
        print(f"[ORDER SENT] orderId={order_id}")

    def _build_ib_order(self, order_request: OrderRequest) -> Order:
        """Convert a simple dataclass order request into an IBKR order object."""
        order = Order()
        order.action = order_request.action
        order.orderType = order_request.order_type
        order.totalQuantity = order_request.quantity

        if order_request.limit_price is not None:
            order.lmtPrice = order_request.limit_price

        return order

    def nextValidId(self, orderId: int) -> None:
        """Receive the first available order id after connection."""
        self.trade_state.next_order_id = orderId
        self.trade_state.connected_ok = True
        self._connected_event.set()
        print(f"[INFO] Connected. Next valid order id: {orderId}")
        self.logger.log_system(f"Connected. next_order_id={orderId}")

    def error(self, reqId, errorCode, errorString, advancedOrderRejectJson="") -> None:
        """Handle IBKR API errors."""
        print(f"[ERROR] reqId={reqId}, code={errorCode}, msg={errorString}")
        self.logger.log_error(f"reqId={reqId}, code={errorCode}, msg={errorString}")

        if errorCode in {502, 504, 1100} and not self.trade_state.connected_ok:
            self._connected_event.set()

    def tickPrice(self, reqId, tickType, price, attrib) -> None:
        """Receive live tick prices from IBKR."""
        if reqId != self.settings.market_data_req_id:
            return

        if price <= 0:
            return

        tick = Tick.now(price=price, tick_type=tickType)
        if self._tick_handler is not None:
            self._tick_handler(tick)

    def orderStatus(
        self,
        orderId,
        status,
        filled,
        remaining,
        avgFillPrice,
        permId,
        parentId,
        lastFillPrice,
        clientId,
        whyHeld,
        mktCapPrice,
    ) -> None:
        """Receive order status changes separately from real executions."""
        event = OrderStatusEvent(
            order_id=orderId,
            status=status,
            filled=filled,
            remaining=remaining,
            avg_fill_price=avgFillPrice,
            last_fill_price=lastFillPrice,
        )

        self.logger.log_order_status(event)

        if orderId == self.trade_state.active_order_id:
            if status == "Filled":
                self.trade_state.active_order_is_filled = True
                self._try_complete_active_order()
            elif status in {"Cancelled", "Inactive", "ApiCancelled"}:
                self._clear_active_order_state()

        if self._order_status_handler is not None:
            self._order_status_handler(event)

    def execDetails(self, reqId, contract, execution) -> None:
        """Receive actual execution fills from IBKR."""
        report = ExecutionReport(
            symbol=contract.symbol,
            side=str(execution.side).upper(),
            quantity=float(execution.shares),
            price=float(execution.price),
            order_id=int(execution.orderId),
            execution_id=str(execution.execId),
            timestamp=str(execution.time),
        )

        self.trade_state.last_execution_price = report.price
        if report.order_id == self.trade_state.active_order_id:
            self.trade_state.active_order_has_execution = True
            self._try_complete_active_order()

        if self._execution_handler is not None:
            self._execution_handler(report)

    def _try_complete_active_order(self) -> None:
        """Clear the pending state only after fill status and execution both arrive."""
        if (
            self.trade_state.active_order_id is not None
            and self.trade_state.active_order_is_filled
            and self.trade_state.active_order_has_execution
        ):
            self._clear_active_order_state()

    def _clear_active_order_state(self) -> None:
        """Reset active order tracking values."""
        self.trade_state.pending_order = False
        self.trade_state.active_order_id = None
        self.trade_state.active_order_is_filled = False
        self.trade_state.active_order_has_execution = False

    def disconnect(self) -> None:
        """Disconnect from IBKR and give the background loop a moment to stop."""
        if self.isConnected():
            self.logger.log_system("Disconnecting from IBKR.")
            super().disconnect()
            time.sleep(0.5)

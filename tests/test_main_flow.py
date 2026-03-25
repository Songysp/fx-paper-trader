"""Mock-based integration tests for the core main.py flow."""

from datetime import datetime
from types import SimpleNamespace
from unittest.mock import Mock

from main import TradingApplication
from models.state import Bar, PositionState, Tick


def test_handle_tick_to_completed_bar_flow_calls_order_send() -> None:
    """handle_tick should drive bar completion, risk/signal checks, and submit_order."""
    app = TradingApplication.__new__(TradingApplication)

    tick = Tick(price=1.2000, timestamp=datetime(2026, 3, 25, 9, 0, 0), tick_type=4)
    completed_bar = Bar(
        timestamp=datetime(2026, 3, 25, 9, 0, 0),
        open=1.1990,
        high=1.2010,
        low=1.1985,
        close=1.2005,
    )

    app.tick_buffer = Mock()
    app.logger = Mock()
    app.bar_aggregator = Mock()
    app.strategy = Mock()
    app.risk_manager = Mock()
    app.position_state = PositionState()
    app.client = SimpleNamespace(trade_state=SimpleNamespace(pending_order=False))
    app.settings = SimpleNamespace(strategy=SimpleNamespace(default_order_qty=1000))
    app.completed_bars = []
    app.submit_order = Mock()

    app.bar_aggregator.update.return_value = completed_bar
    app.risk_manager.check.return_value = "OK"
    app.risk_manager.trading_halted = False
    app.risk_manager.daily_realized_pnl = 0.0
    app.strategy.generate_signal.return_value = "BUY"
    app.strategy.get_latest_indicator_values.return_value = (1.2, 1.1)

    app.handle_tick(tick)

    app.tick_buffer.add_tick.assert_called_once_with(tick)
    app.bar_aggregator.update.assert_called_once_with(tick)

    app.risk_manager.check.assert_called_once_with(
        position=app.position_state,
        latest_price=completed_bar.close,
    )

    app.strategy.generate_signal.assert_called_once_with(
        close_prices=[completed_bar.close],
        position=app.position_state,
    )

    app.submit_order.assert_called_once_with("BUY", app.settings.strategy.default_order_qty)

"""Tests for the simple backtest engine."""

from pathlib import Path

from backtests.engine import BacktestEngine
from config.settings import AppSettings, BrokerSettings, LoggingSettings, RiskSettings, StrategySettings
from models.state import Bar


def test_backtest_engine_generates_report_and_metrics(tmp_path: Path) -> None:
    """The backtest engine should produce a report file and summary metrics."""
    settings = AppSettings(
        broker=BrokerSettings(symbol="EUR", currency="USD"),
        strategy=StrategySettings(
            short_window=3,
            long_window=5,
            default_order_qty=1000,
            enable_rsi_filter=False,
            enable_ma_gap_filter=False,
        ),
        risk=RiskSettings(stop_loss_pct=0.5, take_profit_pct=0.5, max_daily_loss=-999999),
        logging=LoggingSettings(),
    )
    bars = [
        Bar(timestamp=_ts(0), open=1.0, high=1.0, low=1.0, close=1.0),
        Bar(timestamp=_ts(1), open=1.1, high=1.1, low=1.1, close=1.1),
        Bar(timestamp=_ts(2), open=1.2, high=1.2, low=1.2, close=1.2),
        Bar(timestamp=_ts(3), open=1.3, high=1.3, low=1.3, close=1.3),
        Bar(timestamp=_ts(4), open=1.4, high=1.4, low=1.4, close=1.4),
        Bar(timestamp=_ts(5), open=1.2, high=1.2, low=1.2, close=1.2),
        Bar(timestamp=_ts(6), open=1.1, high=1.1, low=1.1, close=1.1),
    ]
    report_path = tmp_path / "report.md"

    result = BacktestEngine(settings).run(bars=bars, report_path=str(report_path))

    assert report_path.exists()
    assert result.metrics.total_trades >= 1
    assert "Backtest Report" in report_path.read_text(encoding="utf-8")


def _ts(minute: int):
    """Create a deterministic timestamp for tests."""
    from datetime import datetime, timedelta

    return datetime(2026, 3, 20, 9, 0, 0) + timedelta(minutes=minute)

"""Tests for the strategy comparison report helper."""

from pathlib import Path

from backtests.compare_strategies import build_comparison_report
from backtests.engine import BacktestResult, BacktestTrade
from backtests.metrics import BacktestMetrics


def test_build_comparison_report_contains_both_strategy_names() -> None:
    """The comparison report should include every compared strategy label."""
    dummy_metrics = BacktestMetrics(
        total_trades=1,
        winning_trades=1,
        losing_trades=0,
        win_rate=100.0,
        gross_profit=1.0,
        gross_loss=0.0,
        net_profit=1.0,
        average_trade=1.0,
        max_drawdown=0.0,
    )
    dummy_result = BacktestResult(
        metrics=dummy_metrics,
        trades=[
            BacktestTrade(
                entry_time="2026-03-20 09:00:00",
                exit_time="2026-03-20 09:05:00",
                entry_price=1.0,
                exit_price=1.1,
                quantity=1000,
                realized_pnl=1.0,
                exit_reason="TEST",
            )
        ],
        report_path=str(Path("reports") / "dummy.md"),
    )

    report = build_comparison_report(
        [
            ("MA Only", dummy_result),
            ("MA + Filters", dummy_result),
        ]
    )

    assert "MA Only" in report
    assert "MA + Filters" in report
    assert "Summary Table" in report

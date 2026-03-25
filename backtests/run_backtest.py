"""Command-line runner for the historical backtest."""

from __future__ import annotations

from pathlib import Path

from backtests.csv_loader import load_bars_from_csv
from backtests.engine import BacktestEngine
from config.settings import AppSettings


def main() -> None:
    """Run the backtest on the sample historical data file."""
    project_root = Path(__file__).resolve().parent.parent
    csv_path = project_root / "historical_data" / "eurusd_sample_1m.csv"
    report_path = project_root / "backtests" / "reports" / "latest_report.md"

    settings = AppSettings.load()
    bars = load_bars_from_csv(str(csv_path))
    result = BacktestEngine(settings).run(bars=bars, report_path=str(report_path))

    print("=" * 60)
    print("BACKTEST FINISHED")
    print(f"Data File      : {csv_path}")
    print(f"Report File    : {result.report_path}")
    print(f"Total Trades   : {result.metrics.total_trades}")
    print(f"Win Rate       : {result.metrics.win_rate:.2f}%")
    print(f"Net Profit     : {result.metrics.net_profit:.4f}")
    print(f"Max Drawdown   : {result.metrics.max_drawdown:.4f}")
    print("=" * 60)


if __name__ == "__main__":
    main()

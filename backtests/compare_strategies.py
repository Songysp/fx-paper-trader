"""Compare multiple strategy configurations on the same historical dataset."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from typing import List, Tuple

from backtests.csv_loader import load_bars_from_csv
from backtests.engine import BacktestEngine, BacktestResult
from config.settings import AppSettings


def main() -> None:
    """Run two strategy variants and write a comparison report."""
    project_root = Path(__file__).resolve().parent.parent
    csv_path = project_root / "historical_data" / "eurusd_sample_1m.csv"
    report_path = project_root / "backtests" / "reports" / "comparison_report.md"
    bars = load_bars_from_csv(str(csv_path))
    base_settings = AppSettings.load()

    ma_only_settings = replace(
        base_settings,
        strategy=replace(
            base_settings.strategy,
            enable_rsi_filter=False,
            enable_ma_gap_filter=False,
        ),
    )
    filtered_settings = replace(
        base_settings,
        strategy=replace(
            base_settings.strategy,
            enable_rsi_filter=True,
            enable_ma_gap_filter=True,
        ),
    )

    comparisons: List[Tuple[str, BacktestResult]] = [
        (
            "MA Only",
            BacktestEngine(ma_only_settings).run(
                bars=bars,
                report_path=str(project_root / "backtests" / "reports" / "ma_only_report.md"),
            ),
        ),
        (
            "MA + Filters",
            BacktestEngine(filtered_settings).run(
                bars=bars,
                report_path=str(project_root / "backtests" / "reports" / "filtered_report.md"),
            ),
        ),
    ]

    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(build_comparison_report(comparisons), encoding="utf-8")

    print("=" * 60)
    print("STRATEGY COMPARISON FINISHED")
    print(f"Data File      : {csv_path}")
    print(f"Report File    : {report_path}")
    for label, result in comparisons:
        print(
            f"{label:15} trades={result.metrics.total_trades:<3} "
            f"win_rate={result.metrics.win_rate:>6.2f}% "
            f"net={result.metrics.net_profit:>8.4f} "
            f"mdd={result.metrics.max_drawdown:>8.4f}"
        )
    print("=" * 60)


def build_comparison_report(comparisons: List[Tuple[str, BacktestResult]]) -> str:
    """Build a markdown report that compares multiple backtest results."""
    lines = [
        "# Strategy Comparison Report",
        "",
        "## Summary Table",
        "",
        "| Strategy | Total Trades | Win Rate | Net Profit | Max Drawdown |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]

    for label, result in comparisons:
        metrics = result.metrics
        lines.append(
            f"| {label} | {metrics.total_trades} | {metrics.win_rate:.2f}% | "
            f"{metrics.net_profit:.4f} | {metrics.max_drawdown:.4f} |"
        )

    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- `MA Only` is the plain moving-average crossover baseline.",
            "- `MA + Filters` adds the RSI filter and MA-gap filter.",
            "- The comparison shows how simple filters can affect trade quality, net PnL, and drawdown.",
            "",
            "## Generated Reports",
            "",
        ]
    )

    for label, result in comparisons:
        lines.append(f"- {label}: `{result.report_path}`")

    lines.append("")
    return "\n".join(lines)


if __name__ == "__main__":
    main()

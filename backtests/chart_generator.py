"""Generate a simple SVG chart from the strategy comparison report."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, List


def _parse_rows(report_text: str) -> List[Dict[str, float | str]]:
    """Extract metric rows from the markdown comparison table."""
    pattern = re.compile(
        r"^\|\s*(?P<label>[^|]+?)\s*\|\s*(?P<trades>\d+)\s*\|\s*"
        r"(?P<win_rate>[-\d.]+)%\s*\|\s*(?P<net_profit>[-\d.]+)\s*\|\s*"
        r"(?P<max_drawdown>[-\d.]+)\s*\|$"
    )
    rows: List[Dict[str, float | str]] = []

    for line in report_text.splitlines():
        match = pattern.match(line.strip())
        if match:
            rows.append(
                {
                    "label": match.group("label").strip(),
                    "trades": int(match.group("trades")),
                    "win_rate": float(match.group("win_rate")),
                    "net_profit": float(match.group("net_profit")),
                    "max_drawdown": float(match.group("max_drawdown")),
                }
            )

    return rows


def _scale(value: float, minimum: float, maximum: float, chart_height: float) -> float:
    """Convert a metric value into SVG chart coordinates."""
    if maximum == minimum:
        return chart_height / 2
    ratio = (value - minimum) / (maximum - minimum)
    return chart_height - (ratio * chart_height)


def build_svg(rows: List[Dict[str, float | str]]) -> str:
    """Build the SVG chart content."""
    width = 860
    height = 420
    margin_left = 90
    margin_right = 30
    margin_top = 60
    margin_bottom = 90
    chart_width = width - margin_left - margin_right
    chart_height = height - margin_top - margin_bottom

    values = [0.0]
    values.extend(float(row["net_profit"]) for row in rows)
    values.extend(float(row["max_drawdown"]) for row in rows)
    minimum = min(values)
    maximum = max(values)

    zero_y = margin_top + _scale(0.0, minimum, maximum, chart_height)
    group_width = chart_width / max(len(rows), 1)
    bar_width = min(56, group_width / 3)

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        "<style>",
        'text { font-family: "Segoe UI", Arial, sans-serif; fill: #202124; }',
        ".title { font-size: 22px; font-weight: 700; }",
        ".subtitle { font-size: 12px; fill: #5f6368; }",
        ".axis { stroke: #9aa0a6; stroke-width: 1; }",
        ".grid { stroke: #e8eaed; stroke-width: 1; }",
        ".label { font-size: 12px; }",
        ".value { font-size: 11px; font-weight: 600; }",
        "</style>",
        f'<rect x="0" y="0" width="{width}" height="{height}" fill="#ffffff" />',
        f'<text x="{margin_left}" y="32" class="title">Strategy Comparison</text>',
        f'<text x="{margin_left}" y="50" class="subtitle">Net profit and max drawdown from the latest comparison report</text>',
    ]

    for step in range(5):
        value = minimum + ((maximum - minimum) * step / 4 if maximum != minimum else 0)
        y = margin_top + _scale(value, minimum, maximum, chart_height)
        parts.append(f'<line x1="{margin_left}" y1="{y:.1f}" x2="{width - margin_right}" y2="{y:.1f}" class="grid" />')
        parts.append(f'<text x="{margin_left - 10}" y="{y + 4:.1f}" text-anchor="end" class="label">{value:.2f}</text>')

    parts.append(f'<line x1="{margin_left}" y1="{margin_top}" x2="{margin_left}" y2="{margin_top + chart_height}" class="axis" />')
    parts.append(f'<line x1="{margin_left}" y1="{zero_y:.1f}" x2="{width - margin_right}" y2="{zero_y:.1f}" class="axis" />')

    for index, row in enumerate(rows):
        center_x = margin_left + (group_width * index) + (group_width / 2)
        profit_value = float(row["net_profit"])
        drawdown_value = float(row["max_drawdown"])

        profit_x = center_x - bar_width - 8
        drawdown_x = center_x + 8
        profit_end_y = margin_top + _scale(profit_value, minimum, maximum, chart_height)
        drawdown_end_y = margin_top + _scale(drawdown_value, minimum, maximum, chart_height)

        parts.append(
            f'<rect x="{profit_x:.1f}" y="{min(zero_y, profit_end_y):.1f}" width="{bar_width:.1f}" height="{abs(profit_end_y - zero_y):.1f}" fill="#2e7d32" rx="4" />'
        )
        parts.append(
            f'<rect x="{drawdown_x:.1f}" y="{min(zero_y, drawdown_end_y):.1f}" width="{bar_width:.1f}" height="{abs(drawdown_end_y - zero_y):.1f}" fill="#c62828" rx="4" />'
        )
        parts.append(
            f'<text x="{profit_x + (bar_width / 2):.1f}" y="{min(zero_y, profit_end_y) - 8:.1f}" text-anchor="middle" class="value">{profit_value:.2f}</text>'
        )
        parts.append(
            f'<text x="{drawdown_x + (bar_width / 2):.1f}" y="{min(zero_y, drawdown_end_y) - 8:.1f}" text-anchor="middle" class="value">{drawdown_value:.2f}</text>'
        )
        parts.append(
            f'<text x="{center_x:.1f}" y="{height - 46}" text-anchor="middle" class="label">{row["label"]}</text>'
        )
        parts.append(
            f'<text x="{center_x:.1f}" y="{height - 28}" text-anchor="middle" class="subtitle">Trades: {int(row["trades"])} | Win Rate: {float(row["win_rate"]):.0f}%</text>'
        )

    legend_y = height - 14
    parts.append(f'<rect x="{margin_left}" y="{legend_y - 10}" width="14" height="14" fill="#2e7d32" rx="3" />')
    parts.append(f'<text x="{margin_left + 22}" y="{legend_y + 1}" class="label">Net Profit</text>')
    parts.append(f'<rect x="{margin_left + 120}" y="{legend_y - 10}" width="14" height="14" fill="#c62828" rx="3" />')
    parts.append(f'<text x="{margin_left + 142}" y="{legend_y + 1}" class="label">Max Drawdown</text>')
    parts.append("</svg>")
    return "\n".join(parts)


def main() -> None:
    """Generate the SVG file next to the comparison report."""
    project_root = Path(__file__).resolve().parent.parent
    report_path = project_root / "backtests" / "reports" / "comparison_report.md"
    output_path = project_root / "backtests" / "reports" / "comparison_chart.svg"

    rows = _parse_rows(report_path.read_text(encoding="utf-8"))
    output_path.write_text(build_svg(rows), encoding="utf-8")

    print("=" * 60)
    print("CHART GENERATED")
    print(f"Source Report : {report_path}")
    print(f"SVG Output    : {output_path}")
    print("=" * 60)


if __name__ == "__main__":
    main()

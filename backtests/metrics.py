"""Performance metrics for backtest results."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List


@dataclass
class BacktestMetrics:
    """Summary statistics from a backtest run."""

    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    gross_profit: float
    gross_loss: float
    net_profit: float
    average_trade: float
    max_drawdown: float


def calculate_max_drawdown(equity_curve: List[float]) -> float:
    """Return the maximum drawdown from the provided equity values."""
    if not equity_curve:
        return 0.0

    peak = equity_curve[0]
    max_drawdown = 0.0

    for equity in equity_curve:
        if equity > peak:
            peak = equity

        drawdown = equity - peak
        if drawdown < max_drawdown:
            max_drawdown = drawdown

    return max_drawdown


def build_metrics(realized_pnls: List[float], equity_curve: List[float]) -> BacktestMetrics:
    """Build summary metrics from realized trade PnL values."""
    total_trades = len(realized_pnls)
    winning_trades = sum(1 for pnl in realized_pnls if pnl > 0)
    losing_trades = sum(1 for pnl in realized_pnls if pnl < 0)
    gross_profit = sum(pnl for pnl in realized_pnls if pnl > 0)
    gross_loss = sum(pnl for pnl in realized_pnls if pnl < 0)
    net_profit = sum(realized_pnls)
    average_trade = net_profit / total_trades if total_trades else 0.0
    win_rate = (winning_trades / total_trades) * 100.0 if total_trades else 0.0
    max_drawdown = calculate_max_drawdown(equity_curve)

    return BacktestMetrics(
        total_trades=total_trades,
        winning_trades=winning_trades,
        losing_trades=losing_trades,
        win_rate=win_rate,
        gross_profit=gross_profit,
        gross_loss=gross_loss,
        net_profit=net_profit,
        average_trade=average_trade,
        max_drawdown=max_drawdown,
    )

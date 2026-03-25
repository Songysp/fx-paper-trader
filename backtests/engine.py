"""Simple backtest engine for bar-based trading strategies."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from config.settings import AppSettings
from execution.position_manager import PositionManager
from models.state import Bar, ExecutionReport, PositionState
from risk.risk_manager import RiskManager
from strategies.ma_crossover import MovingAverageCrossoverStrategy

from backtests.metrics import BacktestMetrics, build_metrics


@dataclass
class BacktestTrade:
    """One completed trade in the backtest."""

    entry_time: str
    exit_time: str
    entry_price: float
    exit_price: float
    quantity: float
    realized_pnl: float
    exit_reason: str


@dataclass
class BacktestResult:
    """Full result object returned by the backtest engine."""

    metrics: BacktestMetrics
    trades: List[BacktestTrade]
    report_path: str


class BacktestEngine:
    """Run a bar-based simulation using the same strategy and risk rules as live trading."""

    def __init__(self, settings: AppSettings) -> None:
        """Prepare strategy, risk, and position state for a backtest run."""
        self.settings = settings
        self.strategy = MovingAverageCrossoverStrategy(
            short_window=settings.strategy.short_window,
            long_window=settings.strategy.long_window,
            enable_rsi_filter=settings.strategy.enable_rsi_filter,
            rsi_period=settings.strategy.rsi_period,
            rsi_buy_max=settings.strategy.rsi_buy_max,
            enable_ma_gap_filter=settings.strategy.enable_ma_gap_filter,
            min_ma_gap_pct=settings.strategy.min_ma_gap_pct,
        )
        self.risk_manager = RiskManager(settings.risk)
        self.position_manager = PositionManager()
        self.position_state = PositionState()
        self.bars: List[Bar] = []
        self.trades: List[BacktestTrade] = []
        self.realized_pnls: List[float] = []
        self.equity_curve: List[float] = [0.0]
        self.pending_entry_bar: Optional[Bar] = None

    def run(self, bars: List[Bar], report_path: str) -> BacktestResult:
        """Run the backtest on a list of bars and write a markdown report."""
        for bar in bars:
            self.bars.append(bar)
            close_prices = [item.close for item in self.bars]

            risk_status = self.risk_manager.check(
                position=self.position_state,
                latest_price=bar.close,
            )
            if risk_status in {"STOP_LOSS", "TAKE_PROFIT"} and self.position_state.is_long:
                self._exit_position(bar=bar, reason=risk_status)
                continue

            if risk_status == "HALT":
                continue

            signal = self.strategy.generate_signal(
                close_prices=close_prices,
                position=self.position_state,
            )

            if signal == "BUY" and not self.position_state.is_long and not self.risk_manager.trading_halted:
                self._enter_position(bar)
            elif signal == "SELL" and self.position_state.is_long:
                self._exit_position(bar=bar, reason="MA_SELL")

        if self.position_state.is_long and self.pending_entry_bar is not None and self.bars:
            self._exit_position(bar=self.bars[-1], reason="END_OF_DATA")

        metrics = build_metrics(self.realized_pnls, self.equity_curve)
        report_text = self._build_report(metrics)
        report_file = Path(report_path)
        report_file.parent.mkdir(parents=True, exist_ok=True)
        report_file.write_text(report_text, encoding="utf-8")

        return BacktestResult(
            metrics=metrics,
            trades=self.trades,
            report_path=str(report_file),
        )

    def _enter_position(self, bar: Bar) -> None:
        """Simulate a buy fill at the bar close."""
        self.pending_entry_bar = bar
        execution = ExecutionReport(
            symbol=f"{self.settings.broker.symbol}.{self.settings.broker.currency}",
            side="BOT",
            quantity=self.settings.strategy.default_order_qty,
            price=bar.close,
            order_id=0,
            execution_id=f"entry-{bar.timestamp.isoformat()}",
            timestamp=bar.timestamp.isoformat(),
        )
        self.position_manager.apply_execution(self.position_state, execution)

    def _exit_position(self, bar: Bar, reason: str) -> None:
        """Simulate a sell fill at the bar close and record the trade."""
        if not self.position_state.is_long or self.pending_entry_bar is None:
            return

        execution = ExecutionReport(
            symbol=f"{self.settings.broker.symbol}.{self.settings.broker.currency}",
            side="SLD",
            quantity=self.position_state.quantity,
            price=bar.close,
            order_id=0,
            execution_id=f"exit-{bar.timestamp.isoformat()}",
            timestamp=bar.timestamp.isoformat(),
        )
        entry_bar = self.pending_entry_bar
        realized_pnl = self.position_manager.apply_execution(self.position_state, execution)
        self.risk_manager.register_realized_pnl(realized_pnl)
        self.realized_pnls.append(realized_pnl)
        self.equity_curve.append(self.equity_curve[-1] + realized_pnl)

        self.trades.append(
            BacktestTrade(
                entry_time=entry_bar.timestamp.isoformat(sep=" "),
                exit_time=bar.timestamp.isoformat(sep=" "),
                entry_price=entry_bar.close,
                exit_price=bar.close,
                quantity=self.settings.strategy.default_order_qty,
                realized_pnl=realized_pnl,
                exit_reason=reason,
            )
        )
        self.pending_entry_bar = None

    def _build_report(self, metrics: BacktestMetrics) -> str:
        """Build a human-readable markdown report."""
        lines = [
            "# Backtest Report",
            "",
            "## Strategy Settings",
            "",
            f"- Symbol: {self.settings.broker.symbol}/{self.settings.broker.currency}",
            f"- Short MA: {self.settings.strategy.short_window}",
            f"- Long MA: {self.settings.strategy.long_window}",
            f"- Default Order Qty: {self.settings.strategy.default_order_qty}",
            f"- RSI Filter: {self.settings.strategy.enable_rsi_filter}",
            f"- RSI Period: {self.settings.strategy.rsi_period}",
            f"- RSI Buy Max: {self.settings.strategy.rsi_buy_max}",
            f"- MA Gap Filter: {self.settings.strategy.enable_ma_gap_filter}",
            f"- Min MA Gap %: {self.settings.strategy.min_ma_gap_pct:.4%}",
            "",
            "## Summary",
            "",
            f"- Total Trades: {metrics.total_trades}",
            f"- Winning Trades: {metrics.winning_trades}",
            f"- Losing Trades: {metrics.losing_trades}",
            f"- Win Rate: {metrics.win_rate:.2f}%",
            f"- Gross Profit: {metrics.gross_profit:.4f}",
            f"- Gross Loss: {metrics.gross_loss:.4f}",
            f"- Net Profit: {metrics.net_profit:.4f}",
            f"- Average Trade: {metrics.average_trade:.4f}",
            f"- Max Drawdown: {metrics.max_drawdown:.4f}",
            "",
            "## Trades",
            "",
            "| Entry Time | Exit Time | Entry Price | Exit Price | Qty | PnL | Exit Reason |",
            "| --- | --- | ---: | ---: | ---: | ---: | --- |",
        ]

        if not self.trades:
            lines.append("| No trades | - | - | - | - | - | - |")
        else:
            for trade in self.trades:
                lines.append(
                    f"| {trade.entry_time} | {trade.exit_time} | "
                    f"{trade.entry_price:.5f} | {trade.exit_price:.5f} | "
                    f"{trade.quantity:.0f} | {trade.realized_pnl:.4f} | {trade.exit_reason} |"
                )

        lines.append("")
        return "\n".join(lines)

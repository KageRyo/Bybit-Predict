# SPDX-FileCopyrightText: 2022-2026 CodeRyo Studio, Chien-Hsun Chang, and contributors
# SPDX-License-Identifier: GPL-2.0-or-later
"""Formatting shared by the human-facing interfaces."""

from __future__ import annotations

from bybit_predict.backtest.models import BacktestResult
from bybit_predict.models import PredictionResult, SignalTrend

DISPLAY_TRENDS = {
    SignalTrend.BULLISH: "Bullish",
    SignalTrend.BEARISH: "Bearish",
    SignalTrend.NEUTRAL: "Neutral",
}


def format_result_text(result: PredictionResult) -> str:
    """Return a dependency-free readable representation for the CLI."""
    lines = [
        f"Symbol: {result.symbol}",
        f"Strategy: {result.strategy} (rule-based, not ML)",
        f"Timeframe: {result.interval}",
        f"Candles: {result.candle_count}",
        f"Period (UTC): {result.period_start.isoformat()} -> {result.period_end.isoformat()}",
        f"Trend: {DISPLAY_TRENDS[result.trend]}",
        f"Signal strength: {result.signal_strength:.2%}",
        f"Bullish volume power: {result.bullish_power:.4f}",
        f"Bearish volume power: {result.bearish_power:.4f}",
    ]
    if result.reference_levels:
        lines.extend(["", "Reference levels:"])
        lines.extend(f"  {level.label:>5}  {level.price:.4f}" for level in result.reference_levels)
    else:
        lines.extend(["", "Reference levels: unavailable while the signal is neutral"])
    lines.extend(["", "Time references (UTC):"])
    lines.extend(
        f"  {reference.label:>6}  {reference.timestamp.isoformat()}"
        for reference in result.time_references
    )
    lines.extend(
        [
            "",
            "Informational market analysis only; not financial advice or a trading instruction.",
        ]
    )
    return "\n".join(lines)


def format_backtest_result_text(result: BacktestResult) -> str:
    """Return a readable report that keeps backtest assumptions beside metrics."""
    metrics = result.metrics
    lines = [
        f"Symbol: {result.symbol}",
        f"Strategy: {result.strategy} (rule-based, not ML)",
        f"Timeframe: {result.interval}",
        f"Candles: {result.candle_count}",
        f"Period (UTC): {result.period_start.isoformat()} -> {result.period_end.isoformat()}",
        f"Signals evaluated: {result.signal_count}",
        f"Trades: {result.trade_count}",
        "",
        "Assumptions:",
        f"  Analysis window: {result.assumptions.analysis_window} closed candles",
        f"  Entry: {result.assumptions.entry_rule}",
        f"  Exit: {result.assumptions.exit_rule}",
        f"  Fee rate per side: {result.assumptions.fee_rate:.4%}",
        f"  Slippage per side: {result.assumptions.slippage_rate:.4%}",
        "",
        "Performance:",
        f"  Directional accuracy: {_format_percentage(metrics.directional_accuracy)}",
        f"  Win rate: {_format_percentage(metrics.win_rate)}",
        f"  Average trade return: {_format_percentage(metrics.average_trade_return)}",
        f"  Strategy total return: {_format_percentage(metrics.total_return)}",
        f"  Maximum drawdown: {_format_percentage(metrics.maximum_drawdown)}",
        f"  Annualized Sharpe ratio: {_format_number(metrics.sharpe_ratio)}",
        "",
        "Baselines:",
    ]
    lines.extend(
        f"  {baseline.name}: {_format_percentage(baseline.total_return)}"
        + (f" ({baseline.trade_count} trades)" if baseline.trade_count is not None else "")
        for baseline in result.baselines
    )
    lines.extend(
        [
            "",
            "Historical results use the assumptions above; they are not financial advice",
            "or a guarantee of future performance.",
        ]
    )
    return "\n".join(lines)


def _format_percentage(value: float | None) -> str:
    return "N/A" if value is None else f"{value:.2%}"


def _format_number(value: float | None) -> str:
    return "N/A" if value is None else f"{value:.3f}"

# SPDX-FileCopyrightText: 2022-2026 CodeRyo Studio, Chien-Hsun Chang, and contributors
# SPDX-License-Identifier: GPL-2.0-or-later
"""Formatting shared by the human-facing interfaces."""

from __future__ import annotations

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

# SPDX-FileCopyrightText: 2022-2026 CodeRyo Studio, Chien-Hsun Chang, and contributors
# SPDX-License-Identifier: GPL-2.0-or-later
"""Pure metric calculations used by the backtesting engine."""

from __future__ import annotations

from math import sqrt
from statistics import fmean, stdev


def maximum_drawdown(equity_values: tuple[float, ...]) -> float:
    """Return the largest peak-to-trough drawdown as a negative return."""
    if not equity_values:
        return 0.0
    peak = equity_values[0]
    drawdown = 0.0
    for value in equity_values:
        peak = max(peak, value)
        if peak:
            drawdown = min(drawdown, value / peak - 1)
    return drawdown


def annualized_sharpe(returns: tuple[float, ...], periods_per_year: float) -> float | None:
    """Calculate a zero-risk-rate Sharpe ratio, or ``None`` when undefined."""
    if len(returns) < 2:
        return None
    dispersion = stdev(returns)
    if dispersion == 0:
        return None
    return fmean(returns) / dispersion * sqrt(periods_per_year)


def periods_per_year(interval: str) -> float:
    """Return crypto-market periods per year for a documented Bybit interval."""
    normalized = str(interval).upper()
    calendar_periods = {"D": 365.0, "W": 52.0, "M": 12.0}
    if normalized in calendar_periods:
        return calendar_periods[normalized]
    minutes = int(normalized)
    return 365.0 * 24 * 60 / minutes

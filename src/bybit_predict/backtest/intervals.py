# SPDX-FileCopyrightText: 2022-2026 CodeRyo Studio, Chien-Hsun Chang, and contributors
# SPDX-License-Identifier: GPL-2.0-or-later
"""Interval normalization and expected candle timestamp calculations."""

from __future__ import annotations

from datetime import datetime

from bybit_predict.exceptions import BacktestError
from bybit_predict.market.intervals import SUPPORTED_INTERVALS
from bybit_predict.market.intervals import expected_next_timestamp as _expected_next_timestamp


def normalize_backtest_interval(interval: str) -> str:
    """Return the canonical form of a supported Bybit candle interval."""
    normalized = str(interval).upper()
    if normalized not in SUPPORTED_INTERVALS:
        allowed = ", ".join(sorted(SUPPORTED_INTERVALS))
        raise BacktestError(
            f"Unsupported or ambiguous backtest interval {interval!r}. Expected one of: {allowed}"
        )
    return normalized


def expected_next_timestamp(timestamp: datetime, interval: str) -> datetime:
    """Return the timestamp required for the candle after ``timestamp``."""
    normalized = normalize_backtest_interval(interval)
    try:
        return _expected_next_timestamp(timestamp, normalized)
    except ValueError as error:
        raise BacktestError(str(error)) from error

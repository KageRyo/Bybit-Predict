# SPDX-FileCopyrightText: 2022-2026 CodeRyo Studio, Chien-Hsun Chang, and contributors
# SPDX-License-Identifier: GPL-2.0-or-later
"""Interval normalization and expected candle timestamp calculations."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from bybit_predict.exceptions import BacktestError
from bybit_predict.market.bybit import SUPPORTED_INTERVALS


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
    _validate_utc_timestamp(timestamp)
    if normalized == "D":
        return timestamp + timedelta(days=1)
    if normalized == "W":
        return timestamp + timedelta(days=7)
    if normalized == "M":
        if (
            timestamp.day != 1
            or timestamp.hour != 0
            or timestamp.minute != 0
            or timestamp.second != 0
            or timestamp.microsecond != 0
        ):
            raise BacktestError(
                "Monthly backtest candles must use UTC timestamps at day 1, 00:00:00"
            )
        if timestamp.month == 12:
            return timestamp.replace(year=timestamp.year + 1, month=1)
        return timestamp.replace(month=timestamp.month + 1)
    return timestamp + timedelta(minutes=int(normalized))


def _validate_utc_timestamp(timestamp: datetime) -> None:
    if timestamp.tzinfo is None or timestamp.utcoffset() is None:
        raise BacktestError("Backtest candle timestamps must be timezone-aware UTC timestamps")
    if timestamp.utcoffset() != UTC.utcoffset(timestamp):
        raise BacktestError("Backtest candle timestamps must be in UTC")

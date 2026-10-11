# SPDX-FileCopyrightText: 2022-2026 CodeRyo Studio, Chien-Hsun Chang, and contributors
# SPDX-License-Identifier: GPL-2.0-or-later
"""Shared Bybit interval spacing and UTC candle-close calculations."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

SUPPORTED_INTERVALS = frozenset(
    {"1", "3", "5", "15", "30", "60", "120", "240", "360", "720", "D", "W", "M"}
)


def expected_next_timestamp(timestamp: datetime, interval: str) -> datetime:
    """Return the next start (and current candle's close) in a Bybit interval."""
    normalized = str(interval).upper()
    if normalized not in SUPPORTED_INTERVALS:
        raise ValueError(f"Unsupported Bybit interval {interval!r}")
    if timestamp.tzinfo is None or timestamp.utcoffset() is None:
        raise ValueError("Candle timestamps must be timezone-aware UTC timestamps")
    if timestamp.utcoffset() != UTC.utcoffset(timestamp):
        raise ValueError("Candle timestamps must be in UTC")
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
            raise ValueError("Monthly candles must use UTC timestamps at day 1, 00:00:00")
        if timestamp.month == 12:
            return timestamp.replace(year=timestamp.year + 1, month=1)
        return timestamp.replace(month=timestamp.month + 1)
    return timestamp + timedelta(minutes=int(normalized))

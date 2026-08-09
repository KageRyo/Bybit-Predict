# SPDX-FileCopyrightText: 2022-2026 CodeRyo Studio, Chien-Hsun Chang, and contributors
# SPDX-License-Identifier: GPL-2.0-or-later
"""Typed, immutable domain models used across every interface."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum


class SignalTrend(StrEnum):
    """The directional result of a strategy evaluation."""

    BULLISH = "bullish"
    BEARISH = "bearish"
    NEUTRAL = "neutral"


@dataclass(frozen=True, slots=True)
class Candle:
    """A normalized OHLCV candle with a timezone-aware UTC timestamp."""

    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float

    def __post_init__(self) -> None:
        if self.timestamp.tzinfo is None or self.timestamp.utcoffset() is None:
            raise ValueError("Candle timestamp must be timezone-aware")
        if self.timestamp.utcoffset() != UTC.utcoffset(self.timestamp):
            raise ValueError("Candle timestamp must be in UTC")
        if self.high < self.low:
            raise ValueError("Candle high cannot be below low")
        if self.high < max(self.open, self.close) or self.low > min(self.open, self.close):
            raise ValueError("Candle OHLC values are inconsistent")
        if self.volume < 0:
            raise ValueError("Candle volume cannot be negative")


@dataclass(frozen=True, slots=True)
class ReferenceLevel:
    """A price level produced by a strategy for informational reference."""

    label: str
    price: float


@dataclass(frozen=True, slots=True)
class TimeReference:
    """A projected time marker produced from historical candle spacing."""

    label: str
    timestamp: datetime


@dataclass(frozen=True, slots=True)
class PredictionResult:
    """A complete, serializable-by-fields market-analysis result."""

    symbol: str
    interval: str
    strategy: str
    trend: SignalTrend
    signal_strength: float
    candle_count: int
    period_start: datetime
    period_end: datetime
    bullish_power: float
    bearish_power: float
    reference_levels: tuple[ReferenceLevel, ...]
    time_references: tuple[TimeReference, ...]

    def __post_init__(self) -> None:
        if not 0 <= self.signal_strength <= 1:
            raise ValueError("Signal strength must be within [0, 1]")
        if self.candle_count <= 0:
            raise ValueError("Candle count must be positive")
        if self.period_start > self.period_end:
            raise ValueError("Analysis period start must not be after its end")

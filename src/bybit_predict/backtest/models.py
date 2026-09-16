# SPDX-FileCopyrightText: 2022-2026 CodeRyo Studio, Chien-Hsun Chang, and contributors
# SPDX-License-Identifier: GPL-2.0-or-later
"""Immutable result models for reproducible historical evaluation."""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import cast

from bybit_predict.backtest.intervals import normalize_backtest_interval
from bybit_predict.exceptions import BacktestError
from bybit_predict.models import SignalTrend

DATASET_MANIFEST_SCHEMA_VERSION = 1
DATASET_MANIFEST_SOURCE = "Bybit V5"
DATASET_MANIFEST_FIELDS = (
    "schema_version",
    "symbol",
    "category",
    "interval",
    "source",
    "requested_start",
    "requested_end",
    "generated_at",
    "content_sha256",
)
_SUPPORTED_CATEGORIES = frozenset({"linear", "spot", "inverse"})
_SHA256_PATTERN = re.compile(r"[0-9a-f]{64}")


@dataclass(frozen=True, slots=True)
class DatasetManifest:
    """Immutable provenance metadata for one normalized candle CSV."""

    schema_version: int
    symbol: str
    category: str
    interval: str
    source: str
    requested_start: datetime
    requested_end: datetime
    generated_at: datetime
    content_sha256: str

    def __post_init__(self) -> None:
        if (
            type(self.schema_version) is not int
            or self.schema_version != DATASET_MANIFEST_SCHEMA_VERSION
        ):
            raise ValueError(
                "Unsupported dataset manifest schema_version; supported version is "
                f"{DATASET_MANIFEST_SCHEMA_VERSION}"
            )
        object.__setattr__(self, "symbol", _normalize_symbol(self.symbol))
        object.__setattr__(self, "category", _normalize_category(self.category))
        object.__setattr__(self, "interval", _normalize_interval(self.interval))
        if self.source != DATASET_MANIFEST_SOURCE:
            raise ValueError(f"Dataset manifest source must be {DATASET_MANIFEST_SOURCE!r}")
        requested_start = _canonical_utc(self.requested_start, "requested_start")
        requested_end = _canonical_utc(self.requested_end, "requested_end")
        if requested_start >= requested_end:
            raise ValueError("requested_start must be before requested_end")
        object.__setattr__(self, "requested_start", requested_start)
        object.__setattr__(self, "requested_end", requested_end)
        object.__setattr__(self, "generated_at", _canonical_utc(self.generated_at, "generated_at"))
        if not isinstance(self.content_sha256, str) or not _SHA256_PATTERN.fullmatch(
            self.content_sha256
        ):
            raise ValueError("content_sha256 must be a lowercase 64-character SHA-256 digest")

    def to_dict(self) -> dict[str, int | str]:
        """Return the JSON representation with canonical UTC timestamps."""
        return {
            "schema_version": self.schema_version,
            "symbol": self.symbol,
            "category": self.category,
            "interval": self.interval,
            "source": self.source,
            "requested_start": _format_utc(self.requested_start),
            "requested_end": _format_utc(self.requested_end),
            "generated_at": _format_utc(self.generated_at),
            "content_sha256": self.content_sha256,
        }

    @classmethod
    def from_mapping(cls, values: Mapping[str, object]) -> DatasetManifest:
        """Build a manifest from JSON data and reject unknown or missing fields."""
        expected_fields = set(DATASET_MANIFEST_FIELDS)
        if set(values) != expected_fields:
            raise ValueError(
                "Dataset manifest must contain exactly these fields: "
                + ", ".join(DATASET_MANIFEST_FIELDS)
            )
        return cls(
            schema_version=cast(int, values["schema_version"]),
            symbol=cast(str, values["symbol"]),
            category=cast(str, values["category"]),
            interval=cast(str, values["interval"]),
            source=cast(str, values["source"]),
            requested_start=_parse_timestamp(values["requested_start"], "requested_start"),
            requested_end=_parse_timestamp(values["requested_end"], "requested_end"),
            generated_at=_parse_timestamp(values["generated_at"], "generated_at"),
            content_sha256=cast(str, values["content_sha256"]),
        )


def _normalize_symbol(value: str) -> str:
    if not isinstance(value, str):
        raise ValueError("symbol must be a string")
    normalized = value.strip().upper()
    if not normalized or any(character.isspace() for character in normalized):
        raise ValueError("symbol must be a non-empty symbol without whitespace")
    return normalized


def _normalize_category(value: str) -> str:
    if not isinstance(value, str):
        raise ValueError("category must be a string")
    normalized = value.strip().lower()
    if normalized not in _SUPPORTED_CATEGORIES:
        allowed = ", ".join(sorted(_SUPPORTED_CATEGORIES))
        raise ValueError(f"Unsupported dataset category {value!r}; expected one of: {allowed}")
    return normalized


def _normalize_interval(value: str) -> str:
    if not isinstance(value, str):
        raise ValueError("interval must be a string")
    try:
        return normalize_backtest_interval(value)
    except BacktestError as error:
        raise ValueError(str(error)) from error


def _canonical_utc(value: datetime, field: str) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field} must be a timezone-aware UTC timestamp")
    return value.astimezone(UTC)


def _format_utc(value: datetime) -> str:
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


def _parse_timestamp(value: object, field: str) -> datetime:
    if not isinstance(value, str):
        raise ValueError(f"{field} must be an ISO-8601 timestamp string")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise ValueError(f"{field} is not a valid ISO-8601 timestamp") from error
    return parsed


@dataclass(frozen=True, slots=True)
class BacktestAssumptions:
    """The execution model applied to every result in a backtest run."""

    analysis_window: int
    entry_rule: str = "next candle open"
    exit_rule: str = "same candle close"
    fee_rate: float = 0.0
    slippage_rate: float = 0.0
    allows_short: bool = True

    def __post_init__(self) -> None:
        if self.analysis_window < 1:
            raise ValueError("analysis_window must be positive")
        if self.fee_rate < 0 or self.slippage_rate < 0:
            raise ValueError("fee_rate and slippage_rate cannot be negative")


@dataclass(frozen=True, slots=True)
class Trade:
    """One non-neutral, one-candle simulated position."""

    signal_timestamp: datetime
    entry_timestamp: datetime
    exit_timestamp: datetime
    trend: SignalTrend
    entry_price: float
    exit_price: float
    gross_return: float
    net_return: float

    def __post_init__(self) -> None:
        if self.trend is SignalTrend.NEUTRAL:
            raise ValueError("A trade must have a bullish or bearish trend")
        if self.entry_price <= 0 or self.exit_price <= 0:
            raise ValueError("Trade prices must be positive")
        if self.entry_timestamp > self.exit_timestamp:
            raise ValueError("Trade exit cannot precede entry")


@dataclass(frozen=True, slots=True)
class EquityPoint:
    """The compounded strategy value after one evaluated candle."""

    timestamp: datetime
    value: float


@dataclass(frozen=True, slots=True)
class PerformanceMetrics:
    """Metrics calculated from the declared execution model, never forecasts."""

    directional_accuracy: float | None
    win_rate: float | None
    average_trade_return: float | None
    total_return: float
    maximum_drawdown: float
    sharpe_ratio: float | None


@dataclass(frozen=True, slots=True)
class BaselineResult:
    """A simple comparison result calculated over the same evaluation period."""

    name: str
    description: str
    total_return: float
    trade_count: int | None = None


@dataclass(frozen=True, slots=True)
class BacktestResult:
    """A complete deterministic evaluation result and its explicit assumptions."""

    symbol: str
    interval: str
    strategy: str
    period_start: datetime
    period_end: datetime
    candle_count: int
    signal_count: int
    trade_count: int
    assumptions: BacktestAssumptions
    metrics: PerformanceMetrics
    baselines: tuple[BaselineResult, ...]
    trades: tuple[Trade, ...]
    equity_curve: tuple[EquityPoint, ...]

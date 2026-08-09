# SPDX-FileCopyrightText: 2022-2026 CodeRyo Studio, Chien-Hsun Chang, and contributors
# SPDX-License-Identifier: GPL-2.0-or-later
"""Immutable result models for reproducible historical evaluation."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from bybit_predict.models import SignalTrend


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

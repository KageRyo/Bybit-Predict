# SPDX-FileCopyrightText: 2022-2026 CodeRyo Studio, Chien-Hsun Chang, and contributors
# SPDX-License-Identifier: GPL-2.0-or-later
"""Interfaces that decouple strategy code from external market-data APIs."""

from __future__ import annotations

from typing import Protocol

from bybit_predict.models import Candle


class MarketDataClient(Protocol):
    """A public source of normalized, chronological OHLCV data."""

    def get_candles(self, symbol: str, interval: str, limit: int) -> tuple[Candle, ...]:
        """Return up to ``limit`` candles in ascending chronological order."""
        ...

    def is_valid_symbol(self, symbol: str) -> bool:
        """Return whether a symbol is currently available for analysis."""
        ...

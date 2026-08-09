# SPDX-FileCopyrightText: 2022-2026 CodeRyo Studio, Chien-Hsun Chang, and contributors
# SPDX-License-Identifier: GPL-2.0-only
"""Strategy contracts shared by live analysis and future backtests."""

from __future__ import annotations

from typing import Protocol

from bybit_predict.models import Candle, PredictionResult


class Strategy(Protocol):
    """A deterministic market-analysis strategy."""

    name: str

    def analyze(
        self, candles: tuple[Candle, ...], *, symbol: str, interval: str
    ) -> PredictionResult:
        """Analyze chronological candles and return an immutable result."""
        ...

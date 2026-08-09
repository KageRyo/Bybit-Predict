# SPDX-FileCopyrightText: 2022-2026 CodeRyo Studio, Chien-Hsun Chang, and contributors
# SPDX-License-Identifier: GPL-2.0-only
"""The reusable application service shared by CLI and Discord interfaces."""

from __future__ import annotations

from bybit_predict.exceptions import SymbolNotFoundError
from bybit_predict.market.base import MarketDataClient
from bybit_predict.models import PredictionResult
from bybit_predict.strategies.base import Strategy
from bybit_predict.strategies.legacy import LegacyRuleBasedStrategy


class PredictionService:
    """Fetch public market data and pass it to one stateless strategy."""

    def __init__(self, market_data: MarketDataClient, strategy: Strategy | None = None) -> None:
        self._market_data = market_data
        self._strategy = strategy if strategy is not None else LegacyRuleBasedStrategy()

    def analyze(self, symbol: str, *, interval: str = "240", limit: int = 180) -> PredictionResult:
        """Return a market-analysis result without exposing infrastructure to strategies."""
        normalized_symbol = symbol.strip().upper()
        if not self._market_data.is_valid_symbol(normalized_symbol):
            subject = normalized_symbol or "The requested symbol"
            raise SymbolNotFoundError(f"{subject} is not an active Bybit symbol")
        candles = self._market_data.get_candles(normalized_symbol, interval=interval, limit=limit)
        return self._strategy.analyze(
            candles, symbol=normalized_symbol, interval=str(interval).upper()
        )

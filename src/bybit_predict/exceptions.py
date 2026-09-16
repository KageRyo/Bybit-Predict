# SPDX-FileCopyrightText: 2022-2026 CodeRyo Studio, Chien-Hsun Chang, and contributors
# SPDX-License-Identifier: GPL-2.0-or-later
"""Domain-specific errors exposed by Bybit-Predict."""


class BybitPredictError(Exception):
    """Base error for expected application failures."""


class ConfigurationError(BybitPredictError):
    """Raised when required runtime configuration is unavailable or invalid."""


class MarketDataError(BybitPredictError):
    """Raised when market data cannot be retrieved or normalized safely."""


class BybitAPIError(MarketDataError):
    """Raised when Bybit returns a non-success API response."""

    def __init__(self, ret_code: object, ret_message: str, *, retryable: bool) -> None:
        self.ret_code = ret_code
        self.ret_message = ret_message
        self.retryable = retryable
        super().__init__(f"Bybit API error {ret_code}: {ret_message}")


class SymbolNotFoundError(MarketDataError):
    """Raised when a symbol is not an active instrument in the requested market."""


class InsufficientDataError(BybitPredictError):
    """Raised when a strategy lacks enough candles for a valid analysis."""


class BacktestError(BybitPredictError):
    """Raised when backtest input or execution semantics are invalid."""

# SPDX-FileCopyrightText: 2022-2026 CodeRyo Studio, Chien-Hsun Chang, and contributors
# SPDX-License-Identifier: GPL-2.0-or-later
"""Bybit V5 public market-data adapter.

The client intentionally uses only public endpoints.  It never accepts or
requires Bybit API credentials for market analysis.
"""

from __future__ import annotations

import time
from collections.abc import Callable, Mapping, Sequence
from datetime import UTC, datetime
from typing import Any, Literal, Protocol, cast

from bybit_predict.exceptions import MarketDataError
from bybit_predict.models import Candle

MarketCategory = Literal["linear", "spot", "inverse"]
SUPPORTED_INTERVALS = frozenset(
    {"1", "3", "5", "15", "30", "60", "120", "240", "360", "720", "D", "W", "M"}
)


class BybitSession(Protocol):
    """The small part of pybit's HTTP client used by this adapter."""

    def get_kline(self, **kwargs: object) -> Mapping[str, Any]: ...

    def get_instruments_info(self, **kwargs: object) -> Mapping[str, Any]: ...


def _create_default_session(testnet: bool) -> BybitSession:
    """Import pybit only when the live Bybit adapter is actually constructed."""
    try:
        from pybit.unified_trading import HTTP
    except ImportError as error:  # pragma: no cover - installation concern
        raise MarketDataError(
            "pybit is required for Bybit access. Install Bybit-Predict with its standard "
            "dependencies."
        ) from error
    return cast(BybitSession, HTTP(testnet=testnet))


class BybitV5MarketClient:
    """Fetch and normalize public Bybit V5 candles with bounded retries."""

    def __init__(
        self,
        *,
        category: MarketCategory = "linear",
        testnet: bool = False,
        session: BybitSession | None = None,
        max_retries: int = 3,
        retry_delay_seconds: float = 0.5,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        if max_retries < 1:
            raise ValueError("max_retries must be at least 1")
        if retry_delay_seconds < 0:
            raise ValueError("retry_delay_seconds cannot be negative")
        self._category = category
        self._session = session if session is not None else _create_default_session(testnet)
        self._max_retries = max_retries
        self._retry_delay_seconds = retry_delay_seconds
        self._sleep = sleep

    def get_candles(
        self, symbol: str, interval: str = "240", limit: int = 180
    ) -> tuple[Candle, ...]:
        """Fetch candles in one V5 request and return them oldest-first."""
        normalized_symbol = self._normalize_symbol(symbol)
        normalized_interval = self._validate_interval(interval)
        if not 1 <= limit <= 1000:
            raise ValueError("Bybit candle limit must be between 1 and 1000")

        response = self._request(
            self._session.get_kline,
            category=self._category,
            symbol=normalized_symbol,
            interval=normalized_interval,
            limit=limit,
        )
        rows = self._result_list(response, endpoint="get_kline")
        candles = tuple(self._to_candle(row) for row in rows)
        if not candles:
            raise MarketDataError(f"Bybit returned no candles for {normalized_symbol}")
        return tuple(sorted(candles, key=lambda candle: candle.timestamp))

    def get_historical_candles(
        self, symbol: str, *, interval: str, start: datetime, end: datetime
    ) -> tuple[Candle, ...]:
        """Fetch an explicit UTC range, following Bybit's 1,000-candle pages.

        Bybit returns each page newest-first. The next request moves its
        inclusive end just before the oldest received candle, then normalized
        results are de-duplicated and returned in chronological order.
        """
        normalized_symbol = self._normalize_symbol(symbol)
        normalized_interval = self._validate_interval(interval)
        self._validate_range(start, end)
        start_ms = int(start.timestamp() * 1000)
        page_end_ms = int(end.timestamp() * 1000) - 1
        by_timestamp: dict[datetime, Candle] = {}

        while page_end_ms >= start_ms:
            response = self._request(
                self._session.get_kline,
                category=self._category,
                symbol=normalized_symbol,
                interval=normalized_interval,
                start=start_ms,
                end=page_end_ms,
                limit=1000,
            )
            rows = self._result_list(response, endpoint="get_kline")
            page = tuple(self._to_candle(row) for row in rows)
            if not page:
                break
            for candle in page:
                if start <= candle.timestamp < end:
                    by_timestamp[candle.timestamp] = candle
            oldest_ms = min(int(candle.timestamp.timestamp() * 1000) for candle in page)
            if oldest_ms <= start_ms:
                break
            if oldest_ms >= page_end_ms:
                raise MarketDataError("Bybit historical pagination did not advance")
            page_end_ms = oldest_ms - 1

        candles = tuple(sorted(by_timestamp.values(), key=lambda candle: candle.timestamp))
        if not candles:
            raise MarketDataError(
                f"Bybit returned no candles for {normalized_symbol} in the requested date range"
            )
        return candles

    def is_valid_symbol(self, symbol: str) -> bool:
        """Check an individual symbol against Bybit's current instrument metadata."""
        normalized_symbol = self._normalize_symbol(symbol)
        response = self._request(
            self._session.get_instruments_info,
            category=self._category,
            symbol=normalized_symbol,
        )
        instruments = self._result_list(response, endpoint="get_instruments_info")
        return any(
            item.get("symbol") == normalized_symbol and item.get("status", "Trading") == "Trading"
            for item in instruments
            if isinstance(item, Mapping)
        )

    def list_symbols(self) -> tuple[str, ...]:
        """List all trading symbols, following V5 pagination for large markets."""
        symbols: list[str] = []
        cursor: str | None = None
        while True:
            request: dict[str, object] = {"category": self._category, "limit": 1000}
            if cursor:
                request["cursor"] = cursor
            response = self._request(self._session.get_instruments_info, **request)
            result = self._result(response, endpoint="get_instruments_info")
            raw_items = result.get("list")
            if not isinstance(raw_items, Sequence) or isinstance(raw_items, (str, bytes)):
                raise MarketDataError("Bybit get_instruments_info response has no instrument list")
            symbols.extend(
                item["symbol"]
                for item in raw_items
                if isinstance(item, Mapping)
                and item.get("status", "Trading") == "Trading"
                and isinstance(item.get("symbol"), str)
            )
            next_cursor = result.get("nextPageCursor")
            if not isinstance(next_cursor, str) or not next_cursor:
                break
            cursor = next_cursor
        return tuple(sorted(set(symbols)))

    def _request(
        self, operation: Callable[..., Mapping[str, Any]], **kwargs: object
    ) -> Mapping[str, Any]:
        last_error: Exception | None = None
        for attempt in range(self._max_retries):
            try:
                response = operation(**kwargs)
                self._raise_for_api_error(response)
                return response
            except MarketDataError:
                raise
            except Exception as error:  # pybit exposes transport-specific exception types
                last_error = error
                if attempt + 1 < self._max_retries:
                    self._sleep(self._retry_delay_seconds * (2**attempt))
        raise MarketDataError("Bybit request failed after bounded retries") from last_error

    @staticmethod
    def _normalize_symbol(symbol: str) -> str:
        normalized = symbol.strip().upper()
        if not normalized:
            raise ValueError("Symbol cannot be empty")
        return normalized

    @staticmethod
    def _validate_interval(interval: str) -> str:
        normalized = str(interval).upper()
        if normalized not in SUPPORTED_INTERVALS:
            allowed = ", ".join(sorted(SUPPORTED_INTERVALS))
            raise ValueError(f"Unsupported Bybit interval {interval!r}. Expected one of: {allowed}")
        return normalized

    @staticmethod
    def _validate_range(start: datetime, end: datetime) -> None:
        if start.tzinfo is None or start.utcoffset() is None:
            raise ValueError("Historical start must be timezone-aware")
        if end.tzinfo is None or end.utcoffset() is None:
            raise ValueError("Historical end must be timezone-aware")
        if start.utcoffset() != UTC.utcoffset(start) or end.utcoffset() != UTC.utcoffset(end):
            raise ValueError("Historical dates must be in UTC")
        if start >= end:
            raise ValueError("Historical start must be before end")

    @staticmethod
    def _raise_for_api_error(response: Mapping[str, Any]) -> None:
        ret_code = response.get("retCode", response.get("ret_code"))
        if ret_code not in (None, 0, "0"):
            message = response.get("retMsg", response.get("ret_msg", "Unknown Bybit API error"))
            raise MarketDataError(f"Bybit API error {ret_code}: {message}")

    @classmethod
    def _result(cls, response: Mapping[str, Any], *, endpoint: str) -> Mapping[str, Any]:
        cls._raise_for_api_error(response)
        result = response.get("result")
        if not isinstance(result, Mapping):
            raise MarketDataError(f"Bybit {endpoint} response has no result object")
        return result

    @classmethod
    def _result_list(cls, response: Mapping[str, Any], *, endpoint: str) -> Sequence[Any]:
        values = cls._result(response, endpoint=endpoint).get("list")
        if not isinstance(values, Sequence) or isinstance(values, (str, bytes)):
            raise MarketDataError(f"Bybit {endpoint} response has no list")
        return values

    @staticmethod
    def _to_candle(row: Any) -> Candle:
        if not isinstance(row, Sequence) or isinstance(row, (str, bytes)) or len(row) < 6:
            raise MarketDataError("Bybit returned a malformed candle")
        try:
            timestamp = datetime.fromtimestamp(int(row[0]) / 1000, tz=UTC)
            return Candle(
                timestamp=timestamp,
                open=float(row[1]),
                high=float(row[2]),
                low=float(row[3]),
                close=float(row[4]),
                volume=float(row[5]),
            )
        except (TypeError, ValueError, OverflowError) as error:
            raise MarketDataError("Bybit returned a candle with invalid numeric values") from error

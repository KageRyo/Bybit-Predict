from __future__ import annotations

from collections.abc import Mapping
from datetime import UTC, datetime
from typing import Any

import pytest

from bybit_predict.exceptions import MarketDataError
from bybit_predict.market.bybit import BybitV5MarketClient


class FakeSession:
    def __init__(
        self,
        *,
        klines: list[object] | None = None,
        instruments: list[object] | None = None,
    ) -> None:
        self.klines = klines or []
        self.instruments = instruments or []
        self.kline_calls: list[dict[str, object]] = []
        self.instrument_calls: list[dict[str, object]] = []

    def get_kline(self, **kwargs: object) -> Mapping[str, Any]:
        self.kline_calls.append(kwargs)
        next_response = self.klines.pop(0)
        if isinstance(next_response, Exception):
            raise next_response
        return next_response  # type: ignore[return-value]

    def get_instruments_info(self, **kwargs: object) -> Mapping[str, Any]:
        self.instrument_calls.append(kwargs)
        next_response = self.instruments.pop(0)
        if isinstance(next_response, Exception):
            raise next_response
        return next_response  # type: ignore[return-value]


def kline_response() -> dict[str, object]:
    return {
        "retCode": 0,
        "result": {
            "list": [
                ["2000", "2", "4", "1", "3", "9", "0"],
                ["1000", "1", "3", "0", "2", "8", "0"],
            ]
        },
    }


def test_get_candles_makes_one_request_and_sorts_reverse_bybit_data() -> None:
    session = FakeSession(klines=[kline_response()])
    client = BybitV5MarketClient(session=session, sleep=lambda _: None)

    candles = client.get_candles("btcusdt", interval="240", limit=180)

    assert len(session.kline_calls) == 1
    assert session.kline_calls[0] == {
        "category": "linear",
        "symbol": "BTCUSDT",
        "interval": "240",
        "limit": 180,
    }
    assert [candle.open for candle in candles] == [1.0, 2.0]
    assert candles[0].timestamp < candles[1].timestamp


def test_get_candles_retries_transport_failure_with_a_bound() -> None:
    session = FakeSession(klines=[ConnectionError("temporary"), kline_response()])
    client = BybitV5MarketClient(session=session, max_retries=2, sleep=lambda _: None)

    assert len(client.get_candles("BTCUSDT", limit=2)) == 2
    assert len(session.kline_calls) == 2


def test_get_candles_rejects_bybit_api_error() -> None:
    session = FakeSession(klines=[{"retCode": 10001, "retMsg": "bad request"}])
    client = BybitV5MarketClient(session=session, sleep=lambda _: None)

    with pytest.raises(MarketDataError, match="10001"):
        client.get_candles("BTCUSDT")


def test_get_historical_candles_follows_reverse_ordered_pages() -> None:
    session = FakeSession(
        klines=[
            {
                "retCode": 0,
                "result": {
                    "list": [
                        ["4000", "4", "5", "3", "4.5", "1"],
                        ["3000", "3", "4", "2", "3.5", "1"],
                    ]
                },
            },
            {
                "retCode": 0,
                "result": {
                    "list": [
                        ["2000", "2", "3", "1", "2.5", "1"],
                        ["1000", "1", "2", "0.5", "1.5", "1"],
                    ]
                },
            },
        ]
    )
    client = BybitV5MarketClient(session=session, sleep=lambda _: None)
    start = datetime.fromtimestamp(1, tz=UTC)
    end = datetime.fromtimestamp(5, tz=UTC)

    candles = client.get_historical_candles("BTCUSDT", interval="240", start=start, end=end)

    assert [candle.open for candle in candles] == [1.0, 2.0, 3.0, 4.0]
    assert session.kline_calls == [
        {
            "category": "linear",
            "symbol": "BTCUSDT",
            "interval": "240",
            "start": 1000,
            "end": 4999,
            "limit": 1000,
        },
        {
            "category": "linear",
            "symbol": "BTCUSDT",
            "interval": "240",
            "start": 1000,
            "end": 2999,
            "limit": 1000,
        },
    ]


def test_symbol_validation_uses_bybit_instrument_metadata() -> None:
    session = FakeSession(
        instruments=[
            {"retCode": 0, "result": {"list": [{"symbol": "BTCUSDT", "status": "Trading"}]}}
        ]
    )
    client = BybitV5MarketClient(session=session, sleep=lambda _: None)

    assert client.is_valid_symbol("btcusdt")
    assert session.instrument_calls[0]["symbol"] == "BTCUSDT"


def test_list_symbols_follows_pagination() -> None:
    session = FakeSession(
        instruments=[
            {
                "retCode": 0,
                "result": {
                    "list": [{"symbol": "BTCUSDT", "status": "Trading"}],
                    "nextPageCursor": "next",
                },
            },
            {
                "retCode": 0,
                "result": {
                    "list": [
                        {"symbol": "ETHUSDT", "status": "Trading"},
                        {"symbol": "OLDUSDT", "status": "Settled"},
                    ],
                    "nextPageCursor": "",
                },
            },
        ]
    )
    client = BybitV5MarketClient(session=session, sleep=lambda _: None)

    assert client.list_symbols() == ("BTCUSDT", "ETHUSDT")
    assert session.instrument_calls[1]["cursor"] == "next"

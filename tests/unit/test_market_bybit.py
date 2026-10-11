from __future__ import annotations

from collections.abc import Mapping
from datetime import UTC, datetime, timedelta, timezone
from typing import Any

import pytest

from bybit_predict.exceptions import BybitAPIError, MarketDataError
from bybit_predict.market.bybit import BybitV5MarketClient

SNAPSHOT_NOW = datetime(2026, 10, 8, 14, tzinfo=UTC)
LATEST_START = datetime(2026, 10, 8, 12, tzinfo=UTC)


def response_for_times(timestamps: list[datetime]) -> dict[str, object]:
    return {
        "retCode": 0,
        "retMsg": "OK",
        "result": {
            "category": "linear",
            "symbol": "BTCUSDT",
            "list": [
                [str(int(timestamp.timestamp() * 1000)), "100", "101", "99", "100", "1", "100"]
                for timestamp in timestamps
            ],
        },
        "retExtInfo": {},
        "time": int(SNAPSHOT_NOW.timestamp() * 1000),
    }


def recent_times(count: int) -> list[datetime]:
    return [LATEST_START - timedelta(hours=4 * index) for index in range(count)]


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
                ["1000", "1", "3", "0.5", "2", "8", "0"],
            ]
        },
    }


def test_get_candles_makes_one_request_and_sorts_reverse_bybit_data() -> None:
    session = FakeSession(klines=[kline_response()])
    client = BybitV5MarketClient(session=session, sleep=lambda _: None, clock=lambda: SNAPSHOT_NOW)

    candles = client.get_candles("btcusdt", interval="240", limit=2)

    assert len(session.kline_calls) == 1
    assert session.kline_calls[0] == {
        "category": "linear",
        "symbol": "BTCUSDT",
        "interval": "240",
        "limit": 3,
    }
    assert [candle.open for candle in candles] == [1.0, 2.0]
    assert candles[0].timestamp < candles[1].timestamp


def test_get_candles_retries_transport_failure_with_a_bound() -> None:
    session = FakeSession(klines=[ConnectionError("temporary"), kline_response()])
    client = BybitV5MarketClient(session=session, max_retries=2, sleep=lambda _: None)

    assert len(client.get_candles("BTCUSDT", limit=2)) == 2
    assert len(session.kline_calls) == 2


def test_get_candles_retries_retryable_bybit_api_error_before_succeeding() -> None:
    sleeps: list[float] = []
    session = FakeSession(
        klines=[
            {"retCode": 10000, "retMsg": "server timeout"},
            kline_response(),
        ]
    )
    client = BybitV5MarketClient(
        session=session,
        max_retries=2,
        retry_delay_seconds=0.25,
        sleep=sleeps.append,
    )

    assert len(client.get_candles("BTCUSDT", limit=2)) == 2
    assert len(session.kline_calls) == 2
    assert sleeps == [0.25]


def test_get_candles_reports_final_retryable_bybit_api_error_after_exhaustion() -> None:
    sleeps: list[float] = []
    session = FakeSession(
        klines=[
            {"retCode": 10006, "retMsg": "rate limit"},
            {"retCode": 10016, "retMsg": "server unavailable"},
        ]
    )
    client = BybitV5MarketClient(
        session=session,
        max_retries=2,
        retry_delay_seconds=0.25,
        sleep=sleeps.append,
    )

    with pytest.raises(BybitAPIError, match="10016: server unavailable") as error:
        client.get_candles("BTCUSDT")

    assert error.value.ret_code == 10016
    assert error.value.ret_message == "server unavailable"
    assert len(session.kline_calls) == 2
    assert sleeps == [0.25]


def test_get_candles_does_not_retry_non_retryable_bybit_api_error() -> None:
    sleeps: list[float] = []
    session = FakeSession(
        klines=[
            {"retCode": 10001, "retMsg": "bad request"},
            kline_response(),
        ]
    )
    client = BybitV5MarketClient(session=session, max_retries=2, sleep=sleeps.append)

    with pytest.raises(MarketDataError, match="10001: bad request"):
        client.get_candles("BTCUSDT")

    assert len(session.kline_calls) == 1
    assert sleeps == []


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


@pytest.mark.parametrize(
    ("now", "expected_hours"),
    [
        (SNAPSHOT_NOW, [4, 8]),
        (datetime(2026, 10, 8, 15, 59, 59, 999999, tzinfo=UTC), [4, 8]),
        (datetime(2026, 10, 8, 16, tzinfo=UTC), [8, 12]),
    ],
)
def test_get_candles_filters_open_candle_and_includes_exact_boundary(
    now: datetime, expected_hours: list[int]
) -> None:
    session = FakeSession(klines=[response_for_times(recent_times(3))])
    client = BybitV5MarketClient(session=session, clock=lambda: now)
    candles = client.get_candles("BTCUSDT", interval="240", limit=2)
    assert [candle.timestamp.hour for candle in candles] == expected_hours
    assert session.kline_calls[0]["limit"] == 3


@pytest.mark.parametrize("at_boundary", [False, True])
def test_get_candles_uses_calendar_month_close(at_boundary: bool) -> None:
    starts = [datetime(2024, month, 1, tzinfo=UTC) for month in (3, 2, 1)]
    now = (
        datetime(2024, 3, 1, tzinfo=UTC)
        if at_boundary
        else datetime(2024, 2, 29, 23, 59, 59, 999999, tzinfo=UTC)
    )
    pages: list[object] = (
        [response_for_times(starts)]
        if at_boundary
        else [response_for_times(starts[:2]), response_for_times(starts[2:])]
    )
    session = FakeSession(klines=pages)
    client = BybitV5MarketClient(session=session, clock=lambda: now)
    candles = client.get_candles("BTCUSDT", interval="M", limit=2 if at_boundary else 1)
    assert [candle.timestamp.month for candle in candles] == ([1, 2] if at_boundary else [1])


@pytest.mark.parametrize("limit", [42, 180])
def test_closed_window_keeps_requested_count(limit: int) -> None:
    session = FakeSession(klines=[response_for_times(recent_times(limit + 1))])
    client = BybitV5MarketClient(session=session, clock=lambda: SNAPSHOT_NOW)
    candles = (
        client.get_candles("BTCUSDT")
        if limit == 180
        else client.get_candles("BTCUSDT", limit=limit)
    )
    assert len(candles) == limit
    assert candles[-1].timestamp == datetime(2026, 10, 8, 8, tzinfo=UTC)
    assert len(session.kline_calls) == 1


def test_1000_closed_candles_fetches_one_older_page() -> None:
    starts = recent_times(1001)
    session = FakeSession(
        klines=[response_for_times(starts[:1000]), response_for_times(starts[1000:])]
    )
    client = BybitV5MarketClient(session=session, clock=lambda: SNAPSHOT_NOW)
    candles = client.get_candles("BTCUSDT", limit=1000)
    assert len(candles) == len({candle.timestamp for candle in candles}) == 1000
    assert candles[0].timestamp == starts[-1]
    assert candles[-1].timestamp == starts[1]
    assert session.kline_calls[1]["end"] == int(starts[999].timestamp() * 1000) - 1
    assert [call["limit"] for call in session.kline_calls] == [1000, 1]


def test_closed_window_returns_latest_requested_candles_when_all_are_closed() -> None:
    session = FakeSession(klines=[response_for_times(recent_times(3))])
    client = BybitV5MarketClient(
        session=session, clock=lambda: datetime(2026, 10, 8, 16, tzinfo=UTC)
    )
    candles = client.get_candles("BTCUSDT", limit=2)
    assert [candle.timestamp.hour for candle in candles] == [8, 12]


@pytest.mark.parametrize("older_times", [[], recent_times(2)[1:], recent_times(1)])
def test_closed_window_rejects_empty_duplicate_or_nonadvancing_older_page(
    older_times: list[datetime],
) -> None:
    session = FakeSession(
        klines=[response_for_times(recent_times(2)), response_for_times(older_times)]
    )
    client = BybitV5MarketClient(session=session, clock=lambda: SNAPSHOT_NOW)
    with pytest.raises(MarketDataError, match="requested=2.*available=1"):
        client.get_candles("BTCUSDT", limit=2)
    assert len(session.kline_calls) == 2


def test_closed_window_rejects_empty_initial_page() -> None:
    session = FakeSession(klines=[response_for_times([])])
    client = BybitV5MarketClient(session=session, clock=lambda: SNAPSHOT_NOW)
    with pytest.raises(MarketDataError, match="requested=42.*available=0"):
        client.get_candles("BTCUSDT", limit=42)
    assert len(session.kline_calls) == 1


def test_get_candles_samples_clock_once_across_pages_and_retries() -> None:
    times = iter([SNAPSHOT_NOW, datetime(2026, 10, 8, 16, tzinfo=UTC)])
    clock_calls: list[datetime] = []

    def clock() -> datetime:
        now = next(times)
        clock_calls.append(now)
        return now

    starts = recent_times(3)
    session = FakeSession(
        klines=[
            ConnectionError("temporary"),
            response_for_times(starts[:2]),
            {"retCode": 10000, "retMsg": "timeout"},
            response_for_times(starts[2:]),
        ]
    )
    sleeps: list[float] = []
    client = BybitV5MarketClient(
        session=session, clock=clock, max_retries=2, retry_delay_seconds=0.25, sleep=sleeps.append
    )
    candles = client.get_candles("BTCUSDT", limit=2)
    assert [candle.timestamp.hour for candle in candles] == [4, 8]
    assert clock_calls == [SNAPSHOT_NOW]
    assert len(session.kline_calls) == 4
    assert sleeps == [0.25, 0.25]


@pytest.mark.parametrize(
    "now", [datetime(2026, 10, 8), datetime(2026, 10, 8, tzinfo=timezone(timedelta(hours=8)))]
)
def test_get_candles_rejects_naive_or_non_utc_clock(now: datetime) -> None:
    client = BybitV5MarketClient(session=FakeSession(), clock=lambda: now)
    with pytest.raises(MarketDataError, match="clock.*UTC"):
        client.get_candles("BTCUSDT")


def test_get_candles_rejects_misaligned_monthly_data() -> None:
    session = FakeSession(klines=[response_for_times([datetime(2024, 2, 2, tzinfo=UTC)])])
    client = BybitV5MarketClient(session=session, clock=lambda: SNAPSHOT_NOW)
    with pytest.raises(MarketDataError, match="(?i)month"):
        client.get_candles("BTCUSDT", interval="M", limit=1)

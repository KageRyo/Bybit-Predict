from __future__ import annotations

from collections.abc import Callable, Mapping
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest

from bybit_predict.market.bybit import BybitV5MarketClient
from bybit_predict.models import Candle


@pytest.fixture
def candles() -> tuple[Candle, ...]:
    """Chronological bullish candles with a four-hour interval."""
    start = datetime(2026, 1, 1, tzinfo=UTC)
    return tuple(
        Candle(
            timestamp=start + timedelta(hours=4 * index),
            open=100.0 + index,
            high=102.0 + index,
            low=99.0 + index,
            close=101.0 + index,
            volume=1000.0 + index,
        )
        for index in range(42)
    )


@pytest.fixture
def live_market_factory() -> Callable[[int], BybitV5MarketClient]:
    """Real adapter with a fixed UTC snapshot and raw, paginated fake API data."""
    now = datetime(2026, 10, 8, 14, tzinfo=UTC)
    latest = datetime(2026, 10, 8, 12, tzinfo=UTC)

    class Session:
        def __init__(self, count: int) -> None:
            self.rows = [
                [
                    str(int((latest - timedelta(hours=4 * index)).timestamp() * 1000)),
                    str(100 + index),
                    str(102 + index),
                    str(99 + index),
                    str(101 + index),
                    str(1000 + index),
                    "0",
                ]
                for index in range(count)
            ]

        def get_kline(self, **kwargs: object) -> Mapping[str, Any]:
            assert kwargs["symbol"] == "BTCUSDT" and kwargs["interval"] == "240"
            limit = kwargs["limit"]
            end = kwargs.get("end", int(now.timestamp() * 1000))
            assert isinstance(limit, int) and isinstance(end, int)
            return {
                "retCode": 0,
                "retMsg": "OK",
                "retExtInfo": {},
                "time": int(now.timestamp() * 1000),
                "result": {
                    "symbol": "BTCUSDT",
                    "category": "linear",
                    "list": [row for row in self.rows if int(row[0]) <= end][:limit],
                },
            }

        def get_instruments_info(self, **kwargs: object) -> Mapping[str, Any]:
            assert kwargs["symbol"] == "BTCUSDT"
            return {"retCode": 0, "result": {"list": [{"symbol": "BTCUSDT", "status": "Trading"}]}}

    def factory(count: int) -> BybitV5MarketClient:
        return BybitV5MarketClient(session=Session(count), clock=lambda: now, sleep=lambda _: None)

    return factory

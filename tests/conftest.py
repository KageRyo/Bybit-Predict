from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

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

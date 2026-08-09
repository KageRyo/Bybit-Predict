from __future__ import annotations

from datetime import UTC, datetime

import pytest

from bybit_predict.models import Candle


def test_candle_requires_utc_timestamp() -> None:
    with pytest.raises(ValueError, match="timezone-aware"):
        Candle(
            timestamp=datetime(2026, 1, 1),
            open=1,
            high=2,
            low=0.5,
            close=1.5,
            volume=1,
        )


def test_candle_rejects_inconsistent_ohlc() -> None:
    with pytest.raises(ValueError, match="inconsistent"):
        Candle(
            timestamp=datetime(2026, 1, 1, tzinfo=UTC),
            open=3,
            high=2,
            low=1,
            close=2,
            volume=1,
        )

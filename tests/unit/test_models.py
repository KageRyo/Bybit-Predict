from __future__ import annotations

from datetime import UTC, datetime

import pytest

from bybit_predict.models import Candle


def _candle_values() -> dict[str, float | datetime]:
    return {
        "timestamp": datetime(2026, 1, 1, tzinfo=UTC),
        "open": 1.0,
        "high": 2.0,
        "low": 0.5,
        "close": 1.5,
        "volume": 1.0,
    }


def test_candle_accepts_finite_positive_ohlc_and_zero_volume() -> None:
    candle = Candle(**{**_candle_values(), "volume": 0.0})

    assert candle.volume == 0.0


@pytest.mark.parametrize("field", ["open", "high", "low", "close", "volume"])
@pytest.mark.parametrize("value", [float("nan"), float("inf"), float("-inf")])
def test_candle_rejects_non_finite_numeric_values(field: str, value: float) -> None:
    with pytest.raises(ValueError, match=rf"Candle {field} must be finite"):
        Candle(**{**_candle_values(), field: value})


@pytest.mark.parametrize("field", ["open", "high", "low", "close"])
@pytest.mark.parametrize("value", [0.0, -1.0])
def test_candle_rejects_non_positive_prices(field: str, value: float) -> None:
    with pytest.raises(ValueError, match=rf"Candle {field} must be positive"):
        Candle(**{**_candle_values(), field: value})


def test_candle_rejects_negative_volume() -> None:
    with pytest.raises(ValueError, match="Candle volume must be non-negative"):
        Candle(**{**_candle_values(), "volume": -1.0})


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

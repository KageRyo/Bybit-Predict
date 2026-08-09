from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from bybit_predict.backtest.data import (
    filter_candles,
    load_candles_csv,
    parse_utc_datetime,
    save_candles_csv,
)
from bybit_predict.exceptions import BacktestError
from bybit_predict.models import Candle


def test_csv_round_trip_is_stable_and_date_filter_is_half_open(tmp_path: Path) -> None:
    start = datetime(2024, 1, 1, tzinfo=UTC)
    candles = tuple(
        Candle(
            timestamp=start + timedelta(hours=4 * index),
            open=10 + index,
            high=12 + index,
            low=9 + index,
            close=11 + index,
            volume=100 + index,
        )
        for index in range(3)
    )
    path = tmp_path / "candles.csv"

    save_candles_csv(path, candles)

    assert load_candles_csv(path) == candles
    assert filter_candles(candles, start=candles[1].timestamp, end=candles[2].timestamp) == (
        candles[1],
    )


def test_csv_rejects_duplicate_timestamps(tmp_path: Path) -> None:
    path = tmp_path / "duplicate.csv"
    path.write_text(
        "timestamp,open,high,low,close,volume\n"
        "2024-01-01T00:00:00Z,1,2,0.5,1.5,1\n"
        "2024-01-01T00:00:00Z,1,2,0.5,1.5,1\n"
    )

    with pytest.raises(BacktestError, match="duplicate"):
        load_candles_csv(path)


def test_parse_utc_datetime_handles_dates_and_rejects_naive_timestamps() -> None:
    assert parse_utc_datetime("2024-01-02") == datetime(2024, 1, 2, tzinfo=UTC)
    assert parse_utc_datetime("2024-01-02T08:00:00+08:00") == datetime(2024, 1, 2, tzinfo=UTC)
    with pytest.raises(ValueError, match="UTC offset"):
        parse_utc_datetime("2024-01-02T00:00:00")

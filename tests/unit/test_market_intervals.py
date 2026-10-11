from __future__ import annotations

from datetime import UTC, datetime, timedelta, timezone

import pytest

from bybit_predict.market.intervals import expected_next_timestamp


@pytest.mark.parametrize(
    ("timestamp", "interval", "expected"),
    [
        (datetime(2026, 10, 8, 12, tzinfo=UTC), "240", datetime(2026, 10, 8, 16, tzinfo=UTC)),
        (datetime(2026, 10, 8, tzinfo=UTC), "D", datetime(2026, 10, 9, tzinfo=UTC)),
        (datetime(2026, 10, 5, tzinfo=UTC), "W", datetime(2026, 10, 12, tzinfo=UTC)),
        (datetime(2024, 2, 1, tzinfo=UTC), "m", datetime(2024, 3, 1, tzinfo=UTC)),
        (datetime(2026, 12, 1, tzinfo=UTC), "M", datetime(2027, 1, 1, tzinfo=UTC)),
    ],
)
def test_next_timestamp_covers_bybit_intervals(
    timestamp: datetime, interval: str, expected: datetime
) -> None:
    assert expected_next_timestamp(timestamp, interval) == expected


@pytest.mark.parametrize(
    "timestamp",
    [datetime(2026, 1, 1), datetime(2026, 1, 1, tzinfo=timezone(timedelta(hours=8)))],
)
def test_next_timestamp_rejects_non_utc_timestamps(timestamp: datetime) -> None:
    with pytest.raises(ValueError, match="UTC"):
        expected_next_timestamp(timestamp, "D")


@pytest.mark.parametrize("interval", ["0", "01", "day"])
def test_next_timestamp_rejects_unsupported_intervals(interval: str) -> None:
    with pytest.raises(ValueError, match="interval"):
        expected_next_timestamp(datetime(2026, 1, 1, tzinfo=UTC), interval)


@pytest.mark.parametrize(
    "timestamp", [datetime(2026, 1, 2, tzinfo=UTC), datetime(2026, 1, 1, 1, tzinfo=UTC)]
)
def test_next_timestamp_rejects_misaligned_month(timestamp: datetime) -> None:
    with pytest.raises(ValueError, match="(?i)month"):
        expected_next_timestamp(timestamp, "M")

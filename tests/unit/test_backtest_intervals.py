from __future__ import annotations

from datetime import UTC, datetime, timedelta, timezone

import pytest

from bybit_predict.backtest.intervals import (
    expected_next_timestamp,
    normalize_backtest_interval,
)
from bybit_predict.exceptions import BacktestError


@pytest.mark.parametrize(
    ("interval", "expected"),
    [("1", "1"), ("240", "240"), ("d", "D"), ("W", "W"), ("m", "M")],
)
def test_normalize_backtest_interval_canonicalizes_supported_values(
    interval: str, expected: str
) -> None:
    assert normalize_backtest_interval(interval) == expected


@pytest.mark.parametrize("interval", ["", "0", "-1", "01", "2", "1.5", "1H", "day"])
def test_normalize_backtest_interval_rejects_unsupported_or_ambiguous_values(
    interval: str,
) -> None:
    with pytest.raises(BacktestError, match="interval"):
        normalize_backtest_interval(interval)


@pytest.mark.parametrize(
    ("timestamp", "interval", "expected"),
    [
        (
            datetime(2024, 1, 1, 12, 30, tzinfo=UTC),
            "5",
            datetime(2024, 1, 1, 12, 35, tzinfo=UTC),
        ),
        (
            datetime(2024, 1, 1, 12, 30, tzinfo=UTC),
            "d",
            datetime(2024, 1, 2, 12, 30, tzinfo=UTC),
        ),
        (
            datetime(2024, 1, 1, 12, 30, tzinfo=UTC),
            "W",
            datetime(2024, 1, 8, 12, 30, tzinfo=UTC),
        ),
        (
            datetime(2024, 1, 1, tzinfo=UTC),
            "M",
            datetime(2024, 2, 1, tzinfo=UTC),
        ),
        (
            datetime(2023, 12, 1, tzinfo=UTC),
            "M",
            datetime(2024, 1, 1, tzinfo=UTC),
        ),
    ],
)
def test_expected_next_timestamp_uses_interval_spacing(
    timestamp: datetime, interval: str, expected: datetime
) -> None:
    assert expected_next_timestamp(timestamp, interval) == expected


def test_expected_next_timestamp_rejects_non_month_start_monthly_timestamp() -> None:
    with pytest.raises(BacktestError, match="(?i)month"):
        expected_next_timestamp(datetime(2024, 1, 2, tzinfo=UTC), "M")


@pytest.mark.parametrize(
    "timestamp",
    [
        datetime(2024, 1, 1),
        datetime(2024, 1, 1, tzinfo=timezone(timedelta(hours=8))),
    ],
)
def test_expected_next_timestamp_requires_utc_aware_timestamp(timestamp: datetime) -> None:
    with pytest.raises(BacktestError, match="UTC"):
        expected_next_timestamp(timestamp, "D")

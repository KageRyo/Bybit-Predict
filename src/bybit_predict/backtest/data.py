# SPDX-FileCopyrightText: 2022-2026 CodeRyo Studio, Chien-Hsun Chang, and contributors
# SPDX-License-Identifier: GPL-2.0-or-later
"""CSV persistence and UTC date parsing for reproducible backtest inputs."""

from __future__ import annotations

import csv
from datetime import UTC, date, datetime, time
from pathlib import Path

from bybit_predict.exceptions import BacktestError
from bybit_predict.models import Candle

CSV_FIELDS = ("timestamp", "open", "high", "low", "close", "volume")


def parse_utc_datetime(value: str) -> datetime:
    """Parse an ISO-8601 date or UTC offset-aware timestamp into UTC.

    A date-only argument denotes midnight UTC. Backtest ranges use an inclusive
    start and exclusive end, so ``--end 2025-01-01`` ends immediately before
    that UTC date.
    """
    try:
        if len(value) == 10:
            return datetime.combine(date.fromisoformat(value), time.min, tzinfo=UTC)
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise ValueError(f"Expected an ISO-8601 UTC date or timestamp, got {value!r}") from error
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("Timestamp must include a UTC offset; use YYYY-MM-DD for UTC midnight")
    return parsed.astimezone(UTC)


def filter_candles(
    candles: tuple[Candle, ...], *, start: datetime, end: datetime
) -> tuple[Candle, ...]:
    """Select chronological candles in the half-open ``[start, end)`` range."""
    if start >= end:
        raise BacktestError("Backtest start must be before end")
    return tuple(candle for candle in candles if start <= candle.timestamp < end)


def save_candles_csv(path: Path, candles: tuple[Candle, ...]) -> None:
    """Save normalized candles in a headered, stable CSV format."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerows(
            {
                "timestamp": candle.timestamp.isoformat().replace("+00:00", "Z"),
                "open": candle.open,
                "high": candle.high,
                "low": candle.low,
                "close": candle.close,
                "volume": candle.volume,
            }
            for candle in candles
        )


def load_candles_csv(path: Path) -> tuple[Candle, ...]:
    """Load saved normalized candles and reject malformed or duplicate rows."""
    try:
        with path.open(newline="", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            if reader.fieldnames is None or tuple(reader.fieldnames) != CSV_FIELDS:
                raise BacktestError(f"CSV must have exactly these columns: {', '.join(CSV_FIELDS)}")
            candles = tuple(
                _row_to_candle(row, line_number) for line_number, row in enumerate(reader, 2)
            )
    except OSError as error:
        raise BacktestError(f"Could not read candle CSV {path}: {error}") from error
    if not candles:
        raise BacktestError("Candle CSV contains no data rows")
    chronological = tuple(sorted(candles, key=lambda candle: candle.timestamp))
    if len({candle.timestamp for candle in chronological}) != len(chronological):
        raise BacktestError("Candle CSV contains duplicate timestamps")
    return chronological


def _row_to_candle(row: dict[str, str | None], line_number: int) -> Candle:
    try:
        return Candle(
            timestamp=parse_utc_datetime(_required(row, "timestamp", line_number)),
            open=float(_required(row, "open", line_number)),
            high=float(_required(row, "high", line_number)),
            low=float(_required(row, "low", line_number)),
            close=float(_required(row, "close", line_number)),
            volume=float(_required(row, "volume", line_number)),
        )
    except (TypeError, ValueError) as error:
        raise BacktestError(f"Invalid candle data on CSV line {line_number}: {error}") from error


def _required(row: dict[str, str | None], field: str, line_number: int) -> str:
    value = row.get(field)
    if value is None or not value.strip():
        raise BacktestError(f"CSV line {line_number} has no {field} value")
    return value

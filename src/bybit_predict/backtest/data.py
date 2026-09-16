# SPDX-FileCopyrightText: 2022-2026 CodeRyo Studio, Chien-Hsun Chang, and contributors
# SPDX-License-Identifier: GPL-2.0-or-later
"""CSV persistence and UTC date parsing for reproducible backtest inputs."""

from __future__ import annotations

import csv
import hashlib
import io
import json
from collections.abc import Mapping
from datetime import UTC, date, datetime, time
from pathlib import Path

from bybit_predict.backtest.intervals import normalize_backtest_interval
from bybit_predict.backtest.models import (
    DATASET_MANIFEST_SCHEMA_VERSION,
    DATASET_MANIFEST_SOURCE,
    DatasetManifest,
)
from bybit_predict.exceptions import BacktestError
from bybit_predict.models import Candle

CSV_FIELDS = ("timestamp", "open", "high", "low", "close", "volume")
MANIFEST_SUFFIX = ".manifest.json"


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


def save_candles_csv(
    path: Path,
    candles: tuple[Candle, ...],
    *,
    symbol: str,
    category: str,
    interval: str,
    requested_start: datetime,
    requested_end: datetime,
) -> DatasetManifest:
    """Save normalized candles and their immutable provenance manifest."""
    metadata = _build_expected_manifest(
        symbol=symbol,
        category=category,
        interval=interval,
        requested_start=requested_start,
        requested_end=requested_end,
    )
    csv_bytes = _serialize_candles_csv(candles)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(csv_bytes)
    content_sha256 = hashlib.sha256(csv_bytes).hexdigest()
    manifest = DatasetManifest(
        schema_version=DATASET_MANIFEST_SCHEMA_VERSION,
        symbol=metadata.symbol,
        category=metadata.category,
        interval=metadata.interval,
        source=DATASET_MANIFEST_SOURCE,
        requested_start=metadata.requested_start,
        requested_end=metadata.requested_end,
        generated_at=datetime.now(UTC),
        content_sha256=content_sha256,
    )
    manifest_path_for_csv(path).write_bytes(_serialize_manifest(manifest))
    return manifest


def load_candles_csv(
    path: Path,
    *,
    symbol: str,
    category: str,
    interval: str,
    requested_start: datetime,
    requested_end: datetime,
) -> tuple[Candle, ...]:
    """Validate provenance metadata and load saved normalized candles."""
    expected = _build_expected_manifest(
        symbol=symbol,
        category=category,
        interval=interval,
        requested_start=requested_start,
        requested_end=requested_end,
    )
    manifest = _load_manifest(manifest_path_for_csv(path))
    _validate_manifest_matches(manifest, expected)
    try:
        csv_bytes = path.read_bytes()
        actual_content_sha256 = hashlib.sha256(csv_bytes).hexdigest()
    except OSError as error:
        raise BacktestError(f"Could not read candle CSV {path}: {error}") from error
    if actual_content_sha256 != manifest.content_sha256:
        raise BacktestError(
            "Dataset content hash mismatch: "
            f"manifest={manifest.content_sha256} actual={actual_content_sha256}"
        )
    return _parse_candles_csv_bytes(csv_bytes, path)


def manifest_path_for_csv(path: Path) -> Path:
    """Return the required sidecar path for a CSV filename."""
    return path.with_name(f"{path.name}{MANIFEST_SUFFIX}")


def _serialize_candles_csv(candles: tuple[Candle, ...]) -> bytes:
    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=CSV_FIELDS)
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
    return output.getvalue().encode("utf-8")


def _serialize_manifest(manifest: DatasetManifest) -> bytes:
    return (json.dumps(manifest.to_dict(), indent=2, sort_keys=True) + "\n").encode("utf-8")


def _parse_candles_csv_bytes(content: bytes, path: Path) -> tuple[Candle, ...]:
    try:
        text = content.decode("utf-8")
    except UnicodeError as error:
        raise BacktestError(f"Could not read candle CSV {path}: {error}") from error
    reader = csv.DictReader(io.StringIO(text, newline=""))
    if reader.fieldnames is None or tuple(reader.fieldnames) != CSV_FIELDS:
        raise BacktestError(f"CSV must have exactly these columns: {', '.join(CSV_FIELDS)}")
    candles = tuple(_row_to_candle(row, line_number) for line_number, row in enumerate(reader, 2))
    if not candles:
        raise BacktestError("Candle CSV contains no data rows")
    chronological = tuple(sorted(candles, key=lambda candle: candle.timestamp))
    if len({candle.timestamp for candle in chronological}) != len(chronological):
        raise BacktestError("Candle CSV contains duplicate timestamps")
    return chronological


def _build_expected_manifest(
    *,
    symbol: str,
    category: str,
    interval: str,
    requested_start: datetime,
    requested_end: datetime,
) -> DatasetManifest:
    try:
        return DatasetManifest(
            schema_version=DATASET_MANIFEST_SCHEMA_VERSION,
            symbol=symbol,
            category=category,
            interval=normalize_backtest_interval(interval),
            source=DATASET_MANIFEST_SOURCE,
            requested_start=requested_start,
            requested_end=requested_end,
            generated_at=datetime.now(UTC),
            content_sha256="0" * 64,
        )
    except (TypeError, ValueError, BacktestError) as error:
        raise BacktestError(f"Invalid expected dataset metadata: {error}") from error


def _load_manifest(path: Path) -> DatasetManifest:
    try:
        with path.open(encoding="utf-8") as file:
            raw_manifest = json.load(file)
    except FileNotFoundError as error:
        raise BacktestError(
            f"Dataset manifest is required at {path}; save the CSV with --save-data"
        ) from error
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise BacktestError(f"Could not read dataset manifest JSON {path}: {error}") from error
    return _parse_manifest(raw_manifest, path)


def _parse_manifest(raw_manifest: object, path: Path) -> DatasetManifest:
    if not isinstance(raw_manifest, Mapping):
        raise BacktestError(f"Dataset manifest JSON {path} must contain an object")
    try:
        return DatasetManifest.from_mapping(raw_manifest)
    except (TypeError, ValueError) as error:
        raise BacktestError(f"Invalid dataset manifest metadata in {path}: {error}") from error


def _validate_manifest_matches(manifest: DatasetManifest, expected: DatasetManifest) -> None:
    for field in ("symbol", "interval", "category"):
        actual_value = getattr(manifest, field)
        expected_value = getattr(expected, field)
        if actual_value != expected_value:
            raise BacktestError(
                f"Dataset manifest {field} mismatch: expected={expected_value!r} "
                f"actual={actual_value!r}"
            )
    if (
        manifest.requested_start != expected.requested_start
        or manifest.requested_end != expected.requested_end
    ):
        raise BacktestError(
            "Dataset manifest requested range mismatch: "
            "expected="
            f"[{expected.requested_start.isoformat()}, {expected.requested_end.isoformat()}) "
            f"actual=[{manifest.requested_start.isoformat()}, {manifest.requested_end.isoformat()})"
        )


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

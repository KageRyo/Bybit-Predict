from __future__ import annotations

import hashlib
import json
from dataclasses import FrozenInstanceError, fields
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import TypedDict, cast

import pytest

from bybit_predict.backtest.data import (
    filter_candles,
    load_candles_csv,
    parse_utc_datetime,
    save_candles_csv,
)
from bybit_predict.exceptions import BacktestError
from bybit_predict.models import Candle


class ManifestArguments(TypedDict):
    symbol: str
    category: str
    interval: str
    requested_start: datetime
    requested_end: datetime


def _manifest_arguments() -> ManifestArguments:
    return {
        "symbol": "BTCUSDT",
        "category": "linear",
        "interval": "240",
        "requested_start": datetime(2026, 1, 1, tzinfo=UTC),
        "requested_end": datetime(2026, 1, 10, tzinfo=UTC),
    }


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

    save_candles_csv(path, candles, **_manifest_arguments())

    assert load_candles_csv(path, **_manifest_arguments()) == candles
    assert filter_candles(candles, start=candles[1].timestamp, end=candles[2].timestamp) == (
        candles[1],
    )


def test_csv_save_writes_a_stable_manifest_for_the_exact_csv_bytes(
    candles: tuple[Candle, ...], tmp_path: Path
) -> None:
    path = tmp_path / "candles.csv"

    saved_manifest = save_candles_csv(path, candles, **_manifest_arguments())
    assert tuple(field.name for field in fields(saved_manifest)) == (
        "schema_version",
        "symbol",
        "category",
        "interval",
        "source",
        "requested_start",
        "requested_end",
        "generated_at",
        "content_sha256",
    )
    with pytest.raises(FrozenInstanceError):
        saved_manifest.symbol = "ETHUSDT"  # type: ignore[misc]

    manifest_path = tmp_path / "candles.csv.manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert list(manifest) == sorted(manifest)
    assert set(manifest) == {
        "category",
        "content_sha256",
        "generated_at",
        "interval",
        "requested_end",
        "requested_start",
        "schema_version",
        "source",
        "symbol",
    }
    assert manifest["schema_version"] == 1
    assert manifest["source"] == "Bybit V5"
    assert manifest["symbol"] == "BTCUSDT"
    assert manifest["category"] == "linear"
    assert manifest["interval"] == "240"
    assert manifest["requested_start"] == "2026-01-01T00:00:00Z"
    assert manifest["requested_end"] == "2026-01-10T00:00:00Z"
    assert manifest["generated_at"].endswith("Z")
    assert manifest["content_sha256"] == hashlib.sha256(path.read_bytes()).hexdigest()
    assert path.read_text(encoding="utf-8").splitlines()[0] == (
        "timestamp,open,high,low,close,volume"
    )


@pytest.mark.parametrize(
    ("field", "replacement", "message"),
    [
        ("symbol", "ETHUSDT", "symbol mismatch"),
        ("interval", "60", "interval mismatch"),
        ("category", "spot", "category mismatch"),
        (
            "requested_start",
            datetime(2026, 1, 2, tzinfo=UTC),
            "requested range mismatch",
        ),
    ],
)
def test_load_rejects_manifest_metadata_mismatch(
    candles: tuple[Candle, ...],
    tmp_path: Path,
    field: str,
    replacement: object,
    message: str,
) -> None:
    path = tmp_path / "candles.csv"
    save_candles_csv(path, candles, **_manifest_arguments())
    expected = cast(ManifestArguments, {**_manifest_arguments(), field: replacement})

    with pytest.raises(BacktestError, match=message):
        load_candles_csv(path, **expected)


def test_load_requires_the_csv_sidecar_manifest(
    candles: tuple[Candle, ...], tmp_path: Path
) -> None:
    path = tmp_path / "candles.csv"
    save_candles_csv(path, candles, **_manifest_arguments())
    (tmp_path / "candles.csv.manifest.json").unlink()
    expected = _manifest_arguments()

    with pytest.raises(BacktestError, match="manifest.*required"):
        load_candles_csv(path, **expected)


def test_load_rejects_malformed_manifest_json(candles: tuple[Candle, ...], tmp_path: Path) -> None:
    path = tmp_path / "candles.csv"
    save_candles_csv(path, candles, **_manifest_arguments())
    (tmp_path / "candles.csv.manifest.json").write_text("{not json", encoding="utf-8")
    expected = _manifest_arguments()

    with pytest.raises(BacktestError, match="manifest.*JSON"):
        load_candles_csv(path, **expected)


def test_load_rejects_unsupported_manifest_schema_version(
    candles: tuple[Candle, ...], tmp_path: Path
) -> None:
    path = tmp_path / "candles.csv"
    save_candles_csv(path, candles, **_manifest_arguments())
    manifest_path = tmp_path / "candles.csv.manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["schema_version"] = 2
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    expected = _manifest_arguments()

    with pytest.raises(BacktestError, match="Unsupported.*schema"):
        load_candles_csv(path, **expected)


def test_load_rejects_tampered_csv_content_hash(
    candles: tuple[Candle, ...], tmp_path: Path
) -> None:
    path = tmp_path / "candles.csv"
    save_candles_csv(path, candles, **_manifest_arguments())
    path.write_bytes(path.read_bytes() + b"\n")
    expected = _manifest_arguments()

    with pytest.raises(BacktestError, match="content hash mismatch"):
        load_candles_csv(path, **expected)


def test_csv_rejects_duplicate_timestamps(tmp_path: Path) -> None:
    path = tmp_path / "duplicate.csv"
    path.write_text(
        "timestamp,open,high,low,close,volume\n"
        "2024-01-01T00:00:00Z,1,2,0.5,1.5,1\n"
        "2024-01-01T00:00:00Z,1,2,0.5,1.5,1\n"
    )
    manifest = {
        "category": "linear",
        "content_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "generated_at": "2026-01-01T00:00:00Z",
        "interval": "240",
        "requested_end": "2026-01-10T00:00:00Z",
        "requested_start": "2026-01-01T00:00:00Z",
        "schema_version": 1,
        "source": "Bybit V5",
        "symbol": "BTCUSDT",
    }
    (tmp_path / "duplicate.csv.manifest.json").write_text(
        json.dumps(manifest, sort_keys=True), encoding="utf-8"
    )
    expected = _manifest_arguments()

    with pytest.raises(BacktestError, match="duplicate"):
        load_candles_csv(path, **expected)


def test_parse_utc_datetime_handles_dates_and_rejects_naive_timestamps() -> None:
    assert parse_utc_datetime("2024-01-02") == datetime(2024, 1, 2, tzinfo=UTC)
    assert parse_utc_datetime("2024-01-02T08:00:00+08:00") == datetime(2024, 1, 2, tzinfo=UTC)
    with pytest.raises(ValueError, match="UTC offset"):
        parse_utc_datetime("2024-01-02T00:00:00")

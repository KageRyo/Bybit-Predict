from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from bybit_predict.backtest import safe_data
from bybit_predict.backtest.data import save_candles_csv
from bybit_predict.cli import build_parser, main
from bybit_predict.models import Candle
from bybit_predict.presentation import format_result_text
from bybit_predict.services.predictor import PredictionService


def _historical_candles(candles: tuple[Candle, ...]) -> tuple[Candle, ...]:
    next_candle = Candle(
        timestamp=candles[-1].timestamp + timedelta(hours=4),
        open=candles[-1].close,
        high=candles[-1].close + 2,
        low=candles[-1].close - 1,
        close=candles[-1].close + 1,
        volume=candles[-1].volume + 1,
    )
    return candles + (next_candle,)


def _save_cli_dataset(path: Path, candles: tuple[Candle, ...]) -> None:
    save_candles_csv(
        path,
        _historical_candles(candles),
        symbol="BTCUSDT",
        category="linear",
        interval="240",
        requested_start=datetime(2026, 1, 1, tzinfo=UTC),
        requested_end=datetime(2026, 1, 10, tzinfo=UTC),
    )


def test_cli_prints_shared_service_result(candles: tuple) -> None:
    class Market:
        def is_valid_symbol(self, symbol: str) -> bool:
            return True

        def get_candles(self, symbol: str, interval: str, limit: int) -> tuple:
            return candles

    status = main(
        ["analyze", "BTCUSDT", "--limit", "42"],
        service_factory=lambda: PredictionService(Market()),
    )

    assert status == 0


def test_cli_description_matches_the_analysis_and_backtesting_positioning() -> None:
    description = build_parser().description
    assert description is not None
    assert "reproducible backtesting" in description


def test_cli_rejects_limits_the_legacy_strategy_cannot_analyze(capsys: object) -> None:
    assert main(["analyze", "BTCUSDT", "--limit", "41"]) == 2
    assert "between 42 and 1000" in capsys.readouterr().err  # type: ignore[attr-defined]


def test_presentation_labels_rule_based_results(candles: tuple) -> None:
    class Market:
        def is_valid_symbol(self, symbol: str) -> bool:
            return True

        def get_candles(self, symbol: str, interval: str, limit: int) -> tuple:
            return candles

    result = PredictionService(Market()).analyze("BTCUSDT", limit=42)

    assert "rule-based, not ML" in format_result_text(result)
    assert "not financial advice" in format_result_text(result)


def test_backtest_cli_downloads_and_optionally_saves_reproducible_data(
    candles: tuple[Candle, ...], tmp_path: Path, capsys: object, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    historical = _historical_candles(candles)

    class Market:
        def is_valid_symbol(self, symbol: str) -> bool:
            return symbol == "BTCUSDT"

        def get_candles(self, symbol: str, interval: str, limit: int) -> tuple[Candle, ...]:
            raise AssertionError("Live analysis data should not be requested by backtest")

        def get_historical_candles(
            self, symbol: str, *, interval: str, start: object, end: object
        ) -> tuple[Candle, ...]:
            assert symbol == "BTCUSDT"
            assert interval == "240"
            return historical

    saved = Path("data/btc-2026.csv")
    status = main(
        [
            "backtest",
            "BTCUSDT",
            "--start",
            "2026-01-01",
            "--end",
            "2026-01-10",
            "--window",
            "42",
            "--save-data",
            str(saved),
        ],
        market_factory=lambda: Market(),  # type: ignore[return-value]
    )

    assert status == 0
    assert saved.is_file()
    manifest_path = saved.with_name(f"{saved.name}.manifest.json")
    assert manifest_path.is_file()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["symbol"] == "BTCUSDT"
    assert manifest["category"] == "linear"
    assert manifest["interval"] == "240"
    assert manifest["requested_start"] == "2026-01-01T00:00:00Z"
    assert manifest["requested_end"] == "2026-01-10T00:00:00Z"
    assert "Performance:" in capsys.readouterr().out  # type: ignore[attr-defined]

    class NoNetworkMarket:
        def is_valid_symbol(self, symbol: str) -> bool:
            raise AssertionError("A saved-data backtest must not validate against the live API")

        def get_candles(self, symbol: str, interval: str, limit: int) -> tuple[Candle, ...]:
            raise AssertionError("A saved-data backtest must not fetch live candles")

        def get_historical_candles(
            self, symbol: str, *, interval: str, start: object, end: object
        ) -> tuple[Candle, ...]:
            raise AssertionError("A saved-data backtest must not fetch historical candles")

    offline_status = main(
        [
            "backtest",
            "BTCUSDT",
            "--start",
            "2026-01-01",
            "--end",
            "2026-01-10",
            "--window",
            "42",
            "--data",
            str(saved),
        ],
        market_factory=lambda: NoNetworkMarket(),  # type: ignore[return-value]
    )

    assert offline_status == 0
    assert "Performance:" in capsys.readouterr().out  # type: ignore[attr-defined]

    manifest_path.unlink()
    rejected_status = main(
        [
            "backtest",
            "BTCUSDT",
            "--start",
            "2026-01-01",
            "--end",
            "2026-01-10",
            "--window",
            "42",
            "--data",
            str(saved),
        ],
        market_factory=lambda: NoNetworkMarket(),  # type: ignore[return-value]
    )

    assert rejected_status == 1
    assert "manifest" in capsys.readouterr().err.lower()  # type: ignore[attr-defined]


def test_backtest_cli_save_rolls_back_when_manifest_replacement_fails(
    candles: tuple[Candle, ...], tmp_path: Path, capsys: object, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    data_dir = tmp_path / "data"
    data_path = data_dir / "candles.csv"
    data_dir.mkdir()
    _save_cli_dataset(data_path, candles)
    manifest_path = data_path.with_name(f"{data_path.name}.manifest.json")
    original_csv = data_path.read_bytes()
    original_manifest = manifest_path.read_bytes()

    class Market:
        def is_valid_symbol(self, symbol: str) -> bool:
            return symbol == "BTCUSDT"

        def get_candles(self, symbol: str, interval: str, limit: int) -> tuple[Candle, ...]:
            raise AssertionError("Live analysis data should not be requested by backtest")

        def get_historical_candles(
            self, symbol: str, *, interval: str, start: object, end: object
        ) -> tuple[Candle, ...]:
            return _historical_candles(candles)

    original_rename = safe_data._rename_relative
    failed = False

    def fail_manifest_replacement(parent_fd: int, source: str, destination: str) -> None:
        nonlocal failed
        if (
            destination == manifest_path.name
            and source.startswith(safe_data._TEMP_FILE_PREFIX)
            and not failed
        ):
            failed = True
            raise OSError("injected manifest replacement failure")
        original_rename(parent_fd, source, destination)

    monkeypatch.setattr(safe_data, "_rename_relative", fail_manifest_replacement)

    try:
        status = main(
            [
                "backtest",
                "BTCUSDT",
                "--start",
                "2026-01-01",
                "--end",
                "2026-01-10",
                "--window",
                "42",
                "--save-data",
                "data/candles.csv",
            ],
            market_factory=lambda: Market(),  # type: ignore[return-value]
        )

        assert status == 1
        assert failed
        assert data_path.read_bytes() == original_csv
        assert manifest_path.read_bytes() == original_manifest
        assert not list(data_dir.glob(".bybit-predict-*"))
        assert "safely write" in capsys.readouterr().err.lower()  # type: ignore[attr-defined]
    finally:
        data_path.unlink(missing_ok=True)
        manifest_path.unlink(missing_ok=True)
        data_dir.rmdir()


@pytest.mark.parametrize("option", ("--data", "--save-data"))
def test_backtest_cli_rejects_dataset_path_traversal(
    candles: tuple[Candle, ...],
    tmp_path: Path,
    capsys: object,
    monkeypatch: pytest.MonkeyPatch,
    option: str,
) -> None:
    monkeypatch.chdir(tmp_path)
    filename = f"{tmp_path.name}-escape.csv"
    unsafe_path = f"../{filename}"

    class Market:
        def is_valid_symbol(self, symbol: str) -> bool:
            return True

        def get_candles(self, symbol: str, interval: str, limit: int) -> tuple[Candle, ...]:
            raise AssertionError("Backtest should not request live analysis candles")

        def get_historical_candles(
            self, symbol: str, *, interval: str, start: object, end: object
        ) -> tuple[Candle, ...]:
            return candles

    escaped_file = tmp_path.parent / filename
    escaped_manifest = tmp_path.parent / f"{filename}.manifest.json"
    try:
        status = main(
            [
                "backtest",
                "BTCUSDT",
                "--start",
                "2026-01-01",
                "--end",
                "2026-01-10",
                "--window",
                "42",
                option,
                unsafe_path,
            ],
            market_factory=lambda: Market(),  # type: ignore[return-value]
        )

        assert status == 1
        assert not escaped_file.exists()
        assert not escaped_manifest.exists()
        assert "trusted" in capsys.readouterr().err.lower()  # type: ignore[attr-defined]
    finally:
        escaped_file.unlink(missing_ok=True)
        escaped_manifest.unlink(missing_ok=True)


def test_backtest_cli_rejects_dataset_symlink_escape(
    tmp_path: Path, capsys: object, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    outside = tmp_path.parent / f"{tmp_path.name}-outside"
    outside.mkdir()
    data_link = tmp_path / "data"
    data_link.symlink_to(outside, target_is_directory=True)

    try:
        status = main(
            [
                "backtest",
                "BTCUSDT",
                "--start",
                "2026-01-01",
                "--end",
                "2026-01-10",
                "--window",
                "42",
                "--data",
                "data/escape.csv",
            ]
        )
    finally:
        data_link.unlink()
        outside.rmdir()

    assert status == 1
    assert "trusted" in capsys.readouterr().err.lower()  # type: ignore[attr-defined]


def test_backtest_cli_rejects_manifest_symlink_escape_on_load(
    candles: tuple[Candle, ...], tmp_path: Path, capsys: object, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    data_path = tmp_path / "data" / "candles.csv"
    data_path.parent.mkdir()
    _save_cli_dataset(data_path, candles)
    manifest_path = data_path.with_name(f"{data_path.name}.manifest.json")
    outside_manifest = tmp_path.parent / f"{tmp_path.name}-load-manifest.json"
    sentinel = manifest_path.read_bytes()
    outside_manifest.write_bytes(sentinel)
    manifest_path.unlink()
    manifest_path.symlink_to(outside_manifest)

    try:
        status = main(
            [
                "backtest",
                "BTCUSDT",
                "--start",
                "2026-01-01",
                "--end",
                "2026-01-10",
                "--window",
                "42",
                "--data",
                "data/candles.csv",
            ]
        )

        assert status == 1
        assert manifest_path.is_symlink()
        assert outside_manifest.read_bytes() == sentinel
        assert "safe" in capsys.readouterr().err.lower()  # type: ignore[attr-defined]
    finally:
        manifest_path.unlink(missing_ok=True)
        outside_manifest.unlink(missing_ok=True)
        data_path.unlink(missing_ok=True)
        data_path.parent.rmdir()


def test_backtest_cli_rejects_manifest_symlink_escape_on_save(
    candles: tuple[Candle, ...], tmp_path: Path, capsys: object, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    data_path = data_dir / "candles.csv"
    manifest_path = data_path.with_name(f"{data_path.name}.manifest.json")
    outside_manifest = tmp_path.parent / f"{tmp_path.name}-save-manifest.json"
    sentinel = b"keep this outside file unchanged\n"
    outside_manifest.write_bytes(sentinel)
    manifest_path.symlink_to(outside_manifest)

    class Market:
        def is_valid_symbol(self, symbol: str) -> bool:
            return symbol == "BTCUSDT"

        def get_candles(self, symbol: str, interval: str, limit: int) -> tuple[Candle, ...]:
            raise AssertionError("Live analysis data should not be requested by backtest")

        def get_historical_candles(
            self, symbol: str, *, interval: str, start: object, end: object
        ) -> tuple[Candle, ...]:
            return _historical_candles(candles)

    try:
        status = main(
            [
                "backtest",
                "BTCUSDT",
                "--start",
                "2026-01-01",
                "--end",
                "2026-01-10",
                "--window",
                "42",
                "--save-data",
                "data/candles.csv",
            ],
            market_factory=lambda: Market(),  # type: ignore[return-value]
        )

        assert status == 1
        assert manifest_path.is_symlink()
        assert outside_manifest.read_bytes() == sentinel
        assert "safe" in capsys.readouterr().err.lower()  # type: ignore[attr-defined]
    finally:
        manifest_path.unlink(missing_ok=True)
        outside_manifest.unlink(missing_ok=True)
        data_path.unlink(missing_ok=True)
        data_dir.rmdir()


@pytest.mark.skipif(
    not safe_data._SAFE_DESCRIPTOR_IO, reason="requires POSIX descriptor-relative dataset I/O"
)
def test_backtest_cli_rejects_parent_directory_swap_after_path_validation(
    candles: tuple[Candle, ...], tmp_path: Path, capsys: object, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    data_path = data_dir / "candles.csv"
    _save_cli_dataset(data_path, candles)

    outside = tmp_path.parent / f"{tmp_path.name}-parent-swap-outside"
    outside.mkdir()
    outside_data_path = outside / "candles.csv"
    _save_cli_dataset(outside_data_path, candles)
    outside_csv_sentinel = outside_data_path.read_bytes()
    outside_manifest_path = outside_data_path.with_name(f"{outside_data_path.name}.manifest.json")
    outside_manifest_sentinel = outside_manifest_path.read_bytes()

    trusted_root = Path.resolve(tmp_path)
    original_resolve = Path.resolve
    original_open = os.open
    data_backup = tmp_path / "data-before-parent-swap"
    swapped = False

    def swap_parent_directory() -> None:
        nonlocal swapped
        if swapped:
            return
        data_dir.rename(data_backup)
        data_dir.symlink_to(outside, target_is_directory=True)
        swapped = True

    def racing_resolve(candidate: Path, strict: bool = False) -> Path:
        resolved = original_resolve(candidate, strict=strict)
        if not swapped and candidate == data_path:
            swap_parent_directory()
        return resolved

    def racing_open(
        path: str | os.PathLike[str],
        flags: int,
        mode: int = 0o777,
        *,
        dir_fd: int | None = None,
    ) -> int:
        file_descriptor = original_open(path, flags, mode, dir_fd=dir_fd)
        if not swapped and dir_fd is None and Path(path) == trusted_root:
            swap_parent_directory()
        return file_descriptor

    monkeypatch.setattr(Path, "resolve", racing_resolve)
    monkeypatch.setattr(os, "open", racing_open)

    try:
        status = main(
            [
                "backtest",
                "BTCUSDT",
                "--start",
                "2026-01-01",
                "--end",
                "2026-01-10",
                "--window",
                "42",
                "--data",
                "data/candles.csv",
            ]
        )

        assert status == 1
        assert swapped
        assert outside_data_path.read_bytes() == outside_csv_sentinel
        assert outside_manifest_path.read_bytes() == outside_manifest_sentinel
        assert "safe" in capsys.readouterr().err.lower()  # type: ignore[attr-defined]
    finally:
        if data_dir.is_symlink():
            data_dir.unlink()
        if data_backup.exists():
            data_backup.rename(data_dir)
        data_path.unlink(missing_ok=True)
        data_path.with_name(f"{data_path.name}.manifest.json").unlink(missing_ok=True)
        data_dir.rmdir()
        outside_data_path.unlink(missing_ok=True)
        outside_manifest_path.unlink(missing_ok=True)
        outside.rmdir()


@pytest.mark.skipif(
    not safe_data._SAFE_DESCRIPTOR_IO, reason="requires POSIX descriptor-relative dataset I/O"
)
def test_backtest_cli_rejects_parent_directory_moved_outside_after_open(
    candles: tuple[Candle, ...], tmp_path: Path, capsys: object, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    data_path = data_dir / "candles.csv"
    _save_cli_dataset(data_path, candles)
    manifest_path = data_path.with_name(f"{data_path.name}.manifest.json")

    outside = tmp_path.parent / f"{tmp_path.name}-moved-outside"
    outside_data_path = outside / data_path.name
    outside_manifest_path = outside / manifest_path.name
    outside_csv_sentinel = data_path.read_bytes()
    outside_manifest_sentinel = manifest_path.read_bytes()

    original_open = os.open
    moved = False

    def move_opened_directory(
        path: str | os.PathLike[str],
        flags: int,
        mode: int = 0o777,
        *,
        dir_fd: int | None = None,
    ) -> int:
        nonlocal moved
        file_descriptor = original_open(path, flags, mode, dir_fd=dir_fd)
        if not moved and dir_fd is not None and Path(path) == Path("data"):
            data_dir.rename(outside)
            moved = True
        return file_descriptor

    monkeypatch.setattr(os, "open", move_opened_directory)

    try:
        status = main(
            [
                "backtest",
                "BTCUSDT",
                "--start",
                "2026-01-01",
                "--end",
                "2026-01-10",
                "--window",
                "42",
                "--data",
                "data/candles.csv",
            ]
        )

        assert status == 1
        assert moved
        assert not data_dir.exists()
        assert outside.is_dir()
        assert not outside.is_symlink()
        assert outside_data_path.read_bytes() == outside_csv_sentinel
        assert outside_manifest_path.read_bytes() == outside_manifest_sentinel
        assert "safe" in capsys.readouterr().err.lower()  # type: ignore[attr-defined]
    finally:
        outside_data_path.unlink(missing_ok=True)
        outside_manifest_path.unlink(missing_ok=True)
        outside.rmdir()


def test_backtest_cli_rejects_hard_linked_csv_output_without_modifying_target(
    candles: tuple[Candle, ...], tmp_path: Path, capsys: object, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    data_path = data_dir / "candles.csv"
    outside_sentinel_path = tmp_path.parent / f"{tmp_path.name}-hard-link-sentinel.csv"
    sentinel = b"keep this hard-link target unchanged\n"
    outside_sentinel_path.write_bytes(sentinel)
    data_path.hardlink_to(outside_sentinel_path)

    class Market:
        def is_valid_symbol(self, symbol: str) -> bool:
            return symbol == "BTCUSDT"

        def get_candles(self, symbol: str, interval: str, limit: int) -> tuple[Candle, ...]:
            raise AssertionError("Live analysis data should not be requested by backtest")

        def get_historical_candles(
            self, symbol: str, *, interval: str, start: object, end: object
        ) -> tuple[Candle, ...]:
            return _historical_candles(candles)

    manifest_path = data_path.with_name(f"{data_path.name}.manifest.json")
    try:
        status = main(
            [
                "backtest",
                "BTCUSDT",
                "--start",
                "2026-01-01",
                "--end",
                "2026-01-10",
                "--window",
                "42",
                "--save-data",
                "data/candles.csv",
            ],
            market_factory=lambda: Market(),  # type: ignore[return-value]
        )

        assert status == 1
        assert outside_sentinel_path.read_bytes() == sentinel
        assert data_path.read_bytes() == sentinel
        assert "safe" in capsys.readouterr().err.lower()  # type: ignore[attr-defined]
    finally:
        manifest_path.unlink(missing_ok=True)
        data_path.unlink(missing_ok=True)
        outside_sentinel_path.unlink(missing_ok=True)
        data_dir.rmdir()


@pytest.mark.skipif(
    not safe_data._SAFE_DESCRIPTOR_IO or not hasattr(os, "mkfifo"),
    reason="requires POSIX descriptor-relative dataset I/O and FIFO support",
)
def test_backtest_cli_rejects_fifo_manifest_without_blocking(tmp_path: Path) -> None:
    monkeypatch_root = tmp_path / "data"
    monkeypatch_root.mkdir()
    csv_path = monkeypatch_root / "candles.csv"
    manifest_path = csv_path.with_name(f"{csv_path.name}.manifest.json")
    csv_path.write_bytes(b"")
    os.mkfifo(manifest_path)
    arguments = [
        "backtest",
        "BTCUSDT",
        "--start",
        "2026-01-01",
        "--end",
        "2026-01-10",
        "--window",
        "42",
        "--data",
        "data/candles.csv",
    ]
    script = f"from bybit_predict.cli import main; raise SystemExit(main({arguments!r}))"

    try:
        try:
            result = subprocess.run(
                [sys.executable, "-c", script],
                cwd=tmp_path,
                capture_output=True,
                text=True,
                timeout=1.0,
                check=False,
            )
        except subprocess.TimeoutExpired as error:
            pytest.fail(f"FIFO manifest open blocked: {error}")

        assert result.returncode == 1
        assert "backtest failed" in result.stderr.lower()
    finally:
        manifest_path.unlink(missing_ok=True)
        csv_path.unlink(missing_ok=True)
        monkeypatch_root.rmdir()

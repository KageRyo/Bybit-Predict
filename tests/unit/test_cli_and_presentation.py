from __future__ import annotations

from datetime import timedelta
from pathlib import Path

from bybit_predict.cli import main
from bybit_predict.models import Candle
from bybit_predict.presentation import format_result_text
from bybit_predict.services.predictor import PredictionService


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
    candles: tuple[Candle, ...], tmp_path: Path, capsys: object
) -> None:
    next_candle = Candle(
        timestamp=candles[-1].timestamp + timedelta(hours=4),
        open=candles[-1].close,
        high=candles[-1].close + 2,
        low=candles[-1].close - 1,
        close=candles[-1].close + 1,
        volume=candles[-1].volume + 1,
    )
    historical = candles + (next_candle,)

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

    saved = tmp_path / "btc-2026.csv"
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

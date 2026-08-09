from __future__ import annotations

from bybit_predict.cli import main
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

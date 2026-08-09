from __future__ import annotations

from datetime import UTC, datetime

import pytest

from bybit_predict.exceptions import InsufficientDataError
from bybit_predict.models import Candle, SignalTrend
from bybit_predict.strategies.legacy import CandleTrend, LegacyRuleBasedStrategy


def make_candle(*, open: float, high: float, low: float, close: float, volume: float = 1) -> Candle:
    return Candle(
        timestamp=datetime(2026, 1, 1, tzinfo=UTC),
        open=open,
        high=high,
        low=low,
        close=close,
        volume=volume,
    )


@pytest.mark.parametrize(
    ("candle", "expected"),
    [
        (make_candle(open=10, high=12, low=9, close=11), CandleTrend.BULLISH),
        (make_candle(open=11, high=12, low=9, close=10), CandleTrend.BEARISH),
        (make_candle(open=10, high=10, low=10, close=10), CandleTrend.DOJI),
        (make_candle(open=10, high=16, low=5, close=11), CandleTrend.DOJI),
    ],
)
def test_classify_candle_preserves_legacy_wick_rules(candle: Candle, expected: CandleTrend) -> None:
    assert LegacyRuleBasedStrategy.classify_candle(candle) is expected


def test_volume_power_uses_only_values_at_or_above_group_average() -> None:
    assert LegacyRuleBasedStrategy.volume_power((10.0, 20.0, 30.0)) == 25.0


def test_compare_power_uses_legacy_twenty_percent_threshold() -> None:
    assert LegacyRuleBasedStrategy.compare_power(121, 100) is SignalTrend.BULLISH
    assert LegacyRuleBasedStrategy.compare_power(100, 121) is SignalTrend.BEARISH
    assert LegacyRuleBasedStrategy.compare_power(120, 100) is SignalTrend.NEUTRAL


def test_analyze_returns_independent_results_without_global_state(
    candles: tuple[Candle, ...],
) -> None:
    strategy = LegacyRuleBasedStrategy()

    first = strategy.analyze(candles, symbol="BTCUSDT", interval="240")
    second = strategy.analyze(candles, symbol="ETHUSDT", interval="240")

    assert first.symbol == "BTCUSDT"
    assert second.symbol == "ETHUSDT"
    assert first.trend is SignalTrend.BULLISH
    assert first.reference_levels
    assert len(first.time_references) == 7
    assert first.reference_levels == second.reference_levels


def test_analyze_requires_enough_chronological_candles(candles: tuple[Candle, ...]) -> None:
    with pytest.raises(InsufficientDataError, match="requires at least"):
        LegacyRuleBasedStrategy().analyze(candles[:41], symbol="BTCUSDT", interval="240")

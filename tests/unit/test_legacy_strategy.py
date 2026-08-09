from __future__ import annotations

from datetime import UTC, datetime, timedelta

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


def test_legacy_reference_levels_and_time_references_have_stable_values(
    candles: tuple[Candle, ...],
) -> None:
    strategy = LegacyRuleBasedStrategy()
    result = strategy.analyze(candles, symbol="BTCUSDT", interval="240")

    assert strategy.position_target(candles, 99.0) == pytest.approx(135.4078)
    assert [level.price for level in result.reference_levels] == pytest.approx(
        [99.0, 107.5922, 112.9078, 117.2039, 121.5, 127.6165, 135.4078]
    )
    assert result.time_references[0].timestamp == datetime(
        2026, 1, 1, 9, 31, 40, 800000, tzinfo=UTC
    )
    assert result.time_references[-1].timestamp == datetime(2026, 1, 1, 16, tzinfo=UTC)


def test_v4_intentionally_uses_full_window_instead_of_v3_zero_or_six_candle_window() -> None:
    start = datetime(2026, 1, 1, tzinfo=UTC)
    candles = tuple(
        make_window_candle(
            timestamp=start + timedelta(hours=index * 4),
            bullish=index < 12,
            volume=100.0 if index < 12 else (10.0 if index < 18 else 1000.0),
        )
        for index in range(42)
    )
    strategy = LegacyRuleBasedStrategy()
    v3_window = strategy.v3_volume_window(candles)

    assert len(v3_window) == 6
    assert (
        strategy.compare_power(
            strategy.volume_power(tuple(candle.volume for candle in v3_window)), 0.0
        )
        is SignalTrend.BULLISH
    )
    assert strategy.analyze(candles, symbol="BTCUSDT", interval="240").trend is SignalTrend.BEARISH


def test_v3_volume_window_can_select_zero_candles() -> None:
    start = datetime(2026, 1, 1, tzinfo=UTC)
    candles = tuple(
        make_window_candle(
            timestamp=start + timedelta(hours=index * 4),
            bullish=True,
            volume=10.0 if index < 12 else 100.0,
        )
        for index in range(42)
    )

    assert LegacyRuleBasedStrategy.v3_volume_window(candles) == ()


def test_analyze_requires_enough_chronological_candles(candles: tuple[Candle, ...]) -> None:
    with pytest.raises(InsufficientDataError, match="requires at least"):
        LegacyRuleBasedStrategy().analyze(candles[:41], symbol="BTCUSDT", interval="240")


def make_window_candle(*, timestamp: datetime, bullish: bool, volume: float) -> Candle:
    if bullish:
        return Candle(
            timestamp=timestamp,
            open=100.0,
            high=102.0,
            low=99.0,
            close=101.0,
            volume=volume,
        )
    return Candle(
        timestamp=timestamp,
        open=101.0,
        high=102.0,
        low=99.0,
        close=100.0,
        volume=volume,
    )

# SPDX-FileCopyrightText: 2022-2026 CodeRyo Studio, Chien-Hsun Chang, and contributors
# SPDX-License-Identifier: GPL-2.0-or-later
"""The original candle, volume, percentile, and Fibonacci-inspired strategy.

This module preserves the intended rule-based semantics while making every
calculation local to a single invocation. It is deliberately not an ML model.

Version 4 intentionally fixes three observable v3 implementation defects:

* v3 selected zero or six candles for volume power because of an erroneous
  ``initial_trend_length`` slice; v4 evaluates the complete input window.
* v3 mixed London/local timestamps with a fixed UTC+8 offset; v4 uses UTC.
* v3 assigned ascending Fibonacci labels to descending bearish values; v4
  keeps each label aligned with its displayed reference value.

``v3_volume_window`` preserves the old selection calculation exclusively as a
migration baseline. ``analyze`` must never call it.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from statistics import fmean

from bybit_predict.exceptions import InsufficientDataError
from bybit_predict.models import (
    Candle,
    PredictionResult,
    ReferenceLevel,
    SignalTrend,
    TimeReference,
)

FIBONACCI_LABELS = ("0%", "23.6%", "38.2%", "50%", "61.8%", "78.6%", "100%")
FIBONACCI_RATIOS = (0.0, 0.236, 0.382, 0.5, 0.618, 0.786, 1.0)
TIME_RETRACEMENT_LABELS = ("138.2%", "150%", "161.8%", "200%", "238.2%", "261.8%", "300%")
TIME_RETRACEMENT_RATIOS = (1.382, 1.5, 1.618, 2.0, 2.382, 2.618, 3.0)


class CandleTrend(StrEnum):
    """The legacy strategy's per-candle classification."""

    BULLISH = "bullish"
    BEARISH = "bearish"
    DOJI = "doji"


@dataclass(frozen=True, slots=True)
class LegacyRuleBasedStrategy:
    """Stateless implementation of the original rule-based signal concepts."""

    name: str = "legacy-rule-based-v4"
    minimum_candles: int = 42

    def analyze(
        self, candles: tuple[Candle, ...], *, symbol: str, interval: str
    ) -> PredictionResult:
        """Evaluate the complete chronological candle window without shared state."""
        self._validate_candles(candles)
        classifications = tuple(self.classify_candle(candle) for candle in candles)
        bullish_volumes = tuple(
            candle.volume
            for candle, classification in zip(candles, classifications, strict=True)
            if classification is CandleTrend.BULLISH
        )
        bearish_volumes = tuple(
            candle.volume
            for candle, classification in zip(candles, classifications, strict=True)
            if classification is CandleTrend.BEARISH
        )
        bullish_power = self.volume_power(bullish_volumes)
        bearish_power = self.volume_power(bearish_volumes)
        trend = self.compare_power(bullish_power, bearish_power)
        reference_levels = self.reference_levels(candles, trend)
        time_references = self.time_references(candles)
        total_power = bullish_power + bearish_power
        strength = abs(bullish_power - bearish_power) / total_power if total_power else 0.0

        return PredictionResult(
            symbol=symbol.upper(),
            interval=interval,
            strategy=self.name,
            trend=trend,
            signal_strength=round(strength, 4),
            candle_count=len(candles),
            period_start=candles[0].timestamp,
            period_end=candles[-1].timestamp,
            bullish_power=round(bullish_power, 4),
            bearish_power=round(bearish_power, 4),
            reference_levels=reference_levels,
            time_references=time_references,
        )

    @staticmethod
    def v3_volume_window(candles: tuple[Candle, ...]) -> tuple[Candle, ...]:
        """Return the v3 ``calcAverage`` selection for migration regression tests.

        The historical implementation created six-candle volume averages, then
        used ``len(markers) - len(markers[markers[0]:])`` as a block count. Its
        result is necessarily zero or one, so v3 sent zero or the first six
        candles to ``backTestKline``. This compatibility helper is intentionally
        not used by the v4 analysis path.
        """
        average_volumes = tuple(
            fmean(candle.volume for candle in candles[index : index + 6])
            for index in range(0, len(candles), 6)
        )
        if any(average_volumes[index] == 0 for index in range(2, len(average_volumes))):
            return ()
        markers = tuple(
            1
            if (fmean(average_volumes[index - 2 : index]) - average_volumes[index])
            / average_volumes[index]
            > 0
            else 0
            for index in range(2, len(average_volumes))
        )
        if not markers:
            return ()
        initial_trend_length = len(markers) - len(markers[markers[0] :])
        return candles[: initial_trend_length * 6]

    @staticmethod
    def classify_candle(candle: Candle) -> CandleTrend:
        """Apply the legacy long-wick candle classification rule."""
        body = abs(candle.open - candle.close)
        if candle.open == candle.high == candle.low == candle.close:
            return CandleTrend.DOJI

        upper_wick = 0.0
        lower_wick = 0.0
        if candle.close > candle.open:
            upper_wick = candle.high - candle.close
            lower_wick = candle.open - candle.low
        elif candle.close < candle.open:
            upper_wick = candle.high - candle.open
            lower_wick = candle.close - candle.low
        else:
            return CandleTrend.DOJI

        long_upper = upper_wick > body * 4
        long_lower = lower_wick > body * 4
        if long_upper and long_lower:
            return CandleTrend.DOJI
        if long_upper or (candle.close < candle.open and not long_lower):
            return CandleTrend.BEARISH
        if long_lower or (candle.close > candle.open and not long_upper):
            return CandleTrend.BULLISH
        return CandleTrend.DOJI

    @staticmethod
    def volume_power(volumes: tuple[float, ...]) -> float:
        """Average only the volumes at or above the group average, as in v3."""
        if not volumes:
            return 0.0
        average = fmean(volumes)
        above_average = tuple(volume for volume in volumes if volume >= average)
        return fmean(above_average) if above_average else 0.0

    @staticmethod
    def compare_power(bullish_power: float, bearish_power: float) -> SignalTrend:
        """Keep the legacy 20% dominance threshold."""
        if bullish_power > bearish_power * 1.2:
            return SignalTrend.BULLISH
        if bearish_power > bullish_power * 1.2:
            return SignalTrend.BEARISH
        return SignalTrend.NEUTRAL

    @classmethod
    def reference_levels(
        cls, candles: tuple[Candle, ...], trend: SignalTrend
    ) -> tuple[ReferenceLevel, ...]:
        """Build IQR-adjusted Fibonacci reference levels when direction is clear."""
        if trend is SignalTrend.NEUTRAL:
            return ()
        if trend is SignalTrend.BULLISH:
            start = min(candle.low for candle in candles)
            end = cls.position_target(candles, start)
        else:
            start = cls.position_target(candles, max(candle.high for candle in candles))
            end = max(candle.high for candle in candles)
        return tuple(
            ReferenceLevel(label=label, price=round(start + (end - start) * ratio, 4))
            for label, ratio in zip(FIBONACCI_LABELS, FIBONACCI_RATIOS, strict=True)
        )

    @staticmethod
    def position_target(candles: tuple[Candle, ...], extreme: float) -> float:
        """Reproduce the legacy IQR-based extension calculation without globals."""
        closes = sorted(candle.close for candle in candles)
        lower_quartile = LegacyRuleBasedStrategy.percentile(closes, 25)
        upper_quartile = LegacyRuleBasedStrategy.percentile(closes, 75)
        iqr = upper_quartile - lower_quartile
        upper_limit = upper_quartile + iqr * 1.5
        lower_limit = lower_quartile - iqr * 1.5
        benchmark = ((upper_limit + lower_limit) / 2) - extreme
        extension = abs(
            benchmark
            + benchmark / 2
            + benchmark / 16
            + benchmark / 32
            + benchmark / 64
            + benchmark / 128
            + benchmark / 1068
        )
        if extreme == max(candle.high for candle in candles):
            return extreme - extension
        return extreme + extension

    @staticmethod
    def percentile(values: list[float], percentile: float) -> float:
        """Linearly interpolate a percentile, matching NumPy's common behavior."""
        if not values:
            raise ValueError("Cannot calculate a percentile from an empty sequence")
        if not 0 <= percentile <= 100:
            raise ValueError("Percentile must be within [0, 100]")
        index = (len(values) - 1) * percentile / 100
        lower_index = int(index)
        upper_index = min(lower_index + 1, len(values) - 1)
        fraction = index - lower_index
        return values[lower_index] * (1 - fraction) + values[upper_index] * fraction

    @staticmethod
    def time_references(candles: tuple[Candle, ...]) -> tuple[TimeReference, ...]:
        """Derive UTC time markers from the two largest bodies in the first 42 candles."""
        sample = candles[:42]
        largest = sorted(
            sample,
            key=lambda candle: abs(candle.open - candle.close),
            reverse=True,
        )[:2]
        earlier, later = sorted(largest, key=lambda candle: candle.timestamp)
        duration = later.timestamp - earlier.timestamp
        return tuple(
            TimeReference(label=label, timestamp=later.timestamp + duration * ratio)
            for label, ratio in zip(TIME_RETRACEMENT_LABELS, TIME_RETRACEMENT_RATIOS, strict=True)
        )

    def _validate_candles(self, candles: tuple[Candle, ...]) -> None:
        if len(candles) < self.minimum_candles:
            raise InsufficientDataError(
                f"{self.name} requires at least {self.minimum_candles} candles; got {len(candles)}"
            )
        if any(
            first.timestamp >= second.timestamp
            for first, second in zip(candles, candles[1:], strict=False)
        ):
            raise ValueError("Candles must be in strictly ascending chronological order")

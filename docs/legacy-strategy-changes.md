# Legacy strategy migration notes

`LegacyRuleBasedStrategy` preserves Bybit-Predict's original rule-based
concepts: candle classification, high-volume power, the 20% dominance
threshold, IQR-derived price extensions, Fibonacci-inspired reference levels,
and time references.

Version 4 changes v3's behavior in the three places below. Each change is a
bug fix covered by regression tests. They make the strategy's output suitable for
deterministic evaluation and the reproducible backtesting introduced in v4.1.0.

| Area | v3 behavior | v4 behavior | Reason |
| --- | --- | --- | --- |
| Volume analysis window | `calcAverage()` derived `initial_trend_length` with `len(markers) - len(markers[markers[0]:])`, then analyzed zero or the first six candles. | Analyze every supplied chronological candle. | The v3 slice cannot select more than one six-candle block, so a 180-candle request did not influence volume power as intended. |
| Timestamps | Mixed a London-local conversion, `time.mktime`, naive datetimes, and a fixed `+28800000` offset. | Use timezone-aware UTC datetimes end-to-end. | Avoid host timezone and daylight-saving-time dependent output. |
| Bearish Fibonacci labels | Generated descending values but Discord displayed them under ascending labels (`0%` through `100%`). | Each displayed label and reference price use the same ascending interpolation order. | Prevent a reference level from being presented under the wrong label. |

## Compatibility baseline

`LegacyRuleBasedStrategy.v3_volume_window()` is a migration-only helper that
reproduces v3's zero/six-candle window calculation. The production
`analyze()` method never calls it.

Regression tests fix the legacy semantics that remain stable:

- long-wick candle classification;
- high-volume power calculation;
- 20% bullish/bearish dominance threshold;
- IQR/percentile extension and Fibonacci reference levels; and
- UTC time-reference calculation.

With this baseline, a future strategy or algorithm change shows up as a
measurable difference from v4.

# Backtesting and evaluation

`bybit-predict backtest` measures a deterministic strategy against historical
OHLCV candles. It is an evaluation tool, not a trading system and not evidence
that a strategy will remain profitable.

## Reproducible inputs

Every run uses an explicit UTC half-open date range: `--start` is included and
`--end` is excluded. A date such as `2024-01-01` means `2024-01-01T00:00:00Z`.
Offset-aware ISO-8601 timestamps are converted to UTC; naive timestamps are
rejected.

Download a range from Bybit V5 and save its normalized input once:

```bash
bybit-predict backtest BTCUSDT \
  --interval 240 \
  --start 2024-01-01 \
  --end 2025-01-01 \
  --strategy legacy \
  --window 180 \
  --save-data data/btcusdt-2024-4h.csv
```

Run the exact same saved dataset later without a network request:

```bash
bybit-predict backtest BTCUSDT \
  --interval 240 \
  --start 2024-01-01 \
  --end 2025-01-01 \
  --strategy legacy \
  --window 180 \
  --data data/btcusdt-2024-4h.csv
```

The CSV is headered and normalized as `timestamp,open,high,low,close,volume`.
It is intentionally not created automatically or committed to Git. The caller
is responsible for retaining the input file, command, package version, and any
non-default fee or slippage settings needed to reproduce a report.

Bybit's [V5 K-line endpoint](https://bybit-exchange.github.io/docs/v5/market/kline)
supplies K-lines in reverse start-time order and limits each request to 1,000
candles; the client requests pages, normalizes them to UTC, removes overlaps,
and supplies chronological data to the engine. The public API may return a
still-open latest candle, so choose an `--end` safely in the past when
evaluating a completed period.

## Execution model

The engine uses a fixed trailing `--window` of closed candles. For each point
in the evaluation period:

1. The strategy receives only that trailing window and produces a signal at
   its final candle close.
2. A bullish or bearish signal enters at the **next candle open** and exits at
   that **same candle close**. Bearish signals are simulated as short
   positions.
3. A neutral signal holds cash for that candle.

This ordering prevents the strategy from seeing the candle used for simulated
execution. Positions never overlap because each simulated position ends before
the following signal can execute.

The selected date range also supplies the warm-up window: the first possible
execution is the candle immediately after `--window` candles have accumulated.
The report's candle period therefore includes warm-up data before the first
evaluated signal.

`--fee-rate` and `--slippage-rate` are proportional, per-side values and both
default to zero. Slippage worsens each entry and exit according to direction;
fees subtract `2 * fee_rate` from every non-neutral gross return. The report
prints both assumptions. It does **not** model funding, borrow costs,
liquidation, leverage limits, exchange-specific fee tiers, spread, partial
fills, market impact, order latency, taxes, or unavailable liquidity.

## Metrics

All reported returns are decimal ratios rendered as percentages.

| Metric | Definition |
| --- | --- |
| Directional accuracy | Share of non-neutral signals whose predicted direction agrees with the next candle close versus the signal candle close. A flat next close is not a correct directional prediction. |
| Win rate | Share of simulated trades with a strictly positive net return after declared fees and slippage. |
| Average trade return | Arithmetic mean of simulated trade net returns. |
| Strategy total return | Compounded return across every evaluation candle; neutral steps contribute zero return. |
| Maximum drawdown | Largest peak-to-trough fall in the compounded strategy equity curve. |
| Annualized Sharpe ratio | Mean per-candle strategy return divided by sample standard deviation, annualized with crypto's 365-day calendar. It is `N/A` when fewer than two returns exist or variation is zero. The risk-free rate is assumed to be zero. |

The engine also reports two baselines over the same execution period:

- **buy-and-hold:** buy at the first executable candle open and hold until the
  final close, using the same declared fee and slippage assumptions;
- **sma-10-20-direction:** go long when the 10-candle simple moving average is
  above the 20-candle average, short when it is below, and use the same
  next-open-to-close execution model.

Baselines make a result comparable; they are not benchmarks of investment
suitability. Do not compare runs that use different symbols, timeframes,
datasets, windows, costs, or execution assumptions as if they were equivalent.

## Limitations

Historical market data is not a guarantee of future market behavior. A strategy
can be overfit through repeated parameter selection even when every single run
is deterministic. The legacy rule-based strategy was created as market
analysis, not as a validated portfolio construction system. Treat results as
engineering evidence about a precisely stated historical simulation, not as a
recommendation to trade.

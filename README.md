# Bybit-Predict

[![License: GPL-2.0-or-later](https://img.shields.io/badge/License-GPL--2.0--or--later-blue.svg)](https://github.com/KageRyo/Bybit-Predict/blob/main/LICENSE)
[![CI](https://github.com/KageRyo/Bybit-Predict/actions/workflows/ci.yml/badge.svg)](https://github.com/KageRyo/Bybit-Predict/actions/workflows/ci.yml)

**Rule-based cryptocurrency market analysis and signals from public Bybit V5
market data, with optional Discord integration.**

> **Current release: v4.1.6.** This release fixes linear-contract short returns, includes starting equity in maximum drawdown, and makes live CLI/Discord analysis use only completed candles. It also includes earlier work: reliability fixes from v4.1.5, PyPI releases since v4.1.1, and reproducible backtesting since v4.1.0. The last legacy release was v3.1.

[正體中文](https://github.com/KageRyo/Bybit-Predict/blob/main/README-zh.md)

If you made backtests with an older version, rerun them with the same saved CSV/manifest, analysis window, fees, and slippage, and keep the original reports to compare. See the v4.1.6 upgrade notes in [CHANGELOG.md](https://github.com/KageRyo/Bybit-Predict/blob/main/CHANGELOG.md).

## What Bybit-Predict is — and is not

Bybit-Predict analyzes OHLCV candles from Bybit and produces market signals and
reference levels. The current `legacy-rule-based-v4` strategy uses candle
shapes, volume power, percentiles, IQR, and Fibonacci-inspired levels.

It **does not use a machine-learning model** and it is **not a trading bot**.
It never places orders or asks for Bybit API credentials.

> **Risk notice:** Cryptocurrency markets are volatile. Results are for
> information only. They are not financial advice or a guarantee of any outcome.

## Highlights

- Live analysis uses completed candles: the default 180-candle window normally needs one K-line page, while 1,000 completed candles may need one additional older page.
- Typed, UTC-normalized `Candle` and immutable `PredictionResult` models.
- Stateless legacy strategy: concurrent analyses cannot mix their data.
- CLI for local use and an optional non-blocking Discord slash command.
- Active symbols validated using Bybit instrument metadata, not a hard-coded
  coin list.
- Tests, Ruff, Pyright, GitHub Actions CI, and Dependabot.
- Reproducible historical backtesting with saved CSV inputs, validated dataset
  manifests, stated assumptions, performance metrics, and two simple baselines.

## Requirements

- Python 3.11 or later
- Internet access to Bybit public market endpoints

**No Bybit account, API key, or API secret is needed** for public market
analysis. The optional Discord interface needs only a Discord bot token.

## Install

### From PyPI

Install the CLI and its standard Bybit V5 dependency with:

```bash
python -m pip install bybit-predict
```

Install the optional Discord interface when you need it:

```bash
python -m pip install "bybit-predict[discord]"
```

For an isolated command-line installation, use [pipx](https://pipx.pypa.io/):

```bash
pipx install bybit-predict
```

### From source

```bash
git clone https://github.com/KageRyo/Bybit-Predict.git
cd Bybit-Predict
uv venv --python 3.11 .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
uv pip install .
```

For contributors, install development and optional Discord dependencies:

```bash
uv pip install -e ".[dev]"
```

## CLI

Analyze the default 180 four-hour candles:

```bash
bybit-predict analyze BTCUSDT
```

Choose another supported Bybit interval and candle count:

```bash
bybit-predict analyze ETHUSDT --interval 60 --limit 240
```

CLI `--limit` and Discord `candles` count completed candles, from 42 to 1,000 (default 180). The candle that is still open is left out until its UTC close time. For minute, daily, and weekly intervals, the close time is the candle start plus the interval; monthly candles close at the start of the next UTC calendar month, not after a fixed 30 days. All requests and retries in one analysis use the same UTC time. If two K-line pages still do not give enough completed candles, analysis fails and shows how many were requested and how many were available. There is no option to include the open candle. The reported data period still shows the start times of the first and last analyzed candles.

Example output:

```text
Symbol: BTCUSDT
Strategy: legacy-rule-based-v4 (rule-based, not ML)
Timeframe: 240
Candles: 180
Trend: Bullish
Signal strength: 68.00%

Reference levels:
     0%  ...
  23.6%  ...
```

The CLI returns a non-zero status for invalid symbols, invalid parameters, or
market-data failures. You can also run `python -m bybit_predict analyze
BTCUSDT`.

### Backtest a historical range

`backtest` replays a strategy over a past date range. The strategy sees only a
fixed window of earlier closed candles. Bullish or bearish signals enter at the
next candle open and exit at that candle's close. The output lists the
assumptions, metrics, and two baselines.

```bash
bybit-predict backtest BTCUSDT \
  --interval 240 \
  --start 2024-01-01 \
  --end 2025-01-01 \
  --strategy legacy \
  --window 180 \
  --save-data data/btcusdt-2024-4h.csv
```

Re-run against the saved, normalized CSV without downloading data again:

```bash
bybit-predict backtest BTCUSDT \
  --interval 240 \
  --start 2024-01-01 \
  --end 2025-01-01 \
  --strategy legacy \
  --window 180 \
  --data data/btcusdt-2024-4h.csv
```

`--start` is inclusive, `--end` is exclusive, and times are in UTC. Saving with
`--save-data` also writes `<csv-name>.manifest.json`; keep it next to the CSV,
because `--data` checks it before replaying. Dataset paths must be inside the
current working directory.

See [backtesting and evaluation](https://github.com/KageRyo/Bybit-Predict/blob/main/docs/backtesting.md) for the return model,
metric definitions, manifest format, path rules, and limitations.

## Discord slash commands

Install the Discord optional dependency, create a Discord application/bot, and
invite it with the `bot` and `applications.commands` scopes.

```bash
python -m pip install ".[discord]"
cp .env.example .env
```

Set environment variables securely (for example by sourcing `.env` locally or
using your deployment secret manager):

```bash
export DISCORD_BOT_TOKEN="your-token"
# Optional: immediately sync commands to one development guild.
export DISCORD_GUILD_ID="your-development-guild-id"
```

Then start the interface:

```bash
bybit-predict discord
```

Use the slash command in Discord:

```text
/predict symbol:BTCUSDT interval:240 candles:180
```

The command runs Bybit requests in a separate thread, so a slow request does
not block Discord's event loop. Responses include the strategy, trend, signal
strength, candle period, and neutral **reference levels**.

Never commit `.env`, bot tokens, API keys, or downloaded data. They are
ignored by default.

## Configuration

| Variable | Required | Purpose |
| --- | --- | --- |
| `DISCORD_BOT_TOKEN` | Discord only | Discord bot authentication token. |
| `DISCORD_GUILD_ID` | No | Development guild for immediate command syncing. |
| `BYBIT_TESTNET` | No | `true` opts into Bybit testnet public data; default is `false`. |

The market-data client has no Bybit credential settings, because public K-line
and instrument endpoints do not need authentication.

## Architecture

```text
Bybit V5 public API
        │
BybitV5MarketClient ──→ normalized UTC Candles
        │
        ├── PredictionService ──→ LegacyRuleBasedStrategy ──→ PredictionResult
        │         │                         │
        │         ├──────── CLI             └── future strategies
        │         └──────── Discord slash command
        │
        └── BacktestEngine ─────→ LegacyRuleBasedStrategy ──→ BacktestResult
                  │
                  ├──────── historical CLI
                  └──────── saved CSV input/output
```

- `market/` owns Bybit V5 requests, retry boundaries, pagination, and response
  normalization.
- `strategies/` contains pure, deterministic signal calculations and has no
  dependency on Bybit or Discord.
- `services/` composes market data with a strategy.
- `interfaces/` converts user input/output only.

## Strategy and evaluation

`LegacyRuleBasedStrategy` keeps the project's original core logic. It
classifies candle bodies and wicks, compares significant bullish and bearish
volume, and derives optional reference prices from IQR and percentile
calculations. It has its own name so later strategies can be compared with it
fairly. v4 fixes three v3 problems: the zero/six-candle volume window,
timezone handling, and bearish Fibonacci label order. The compatibility
baseline and the behavior kept from v3 are documented in
[legacy strategy migration notes](https://github.com/KageRyo/Bybit-Predict/blob/main/docs/legacy-strategy-changes.md).

The **v4.1.0** backtesting work ([#25](https://github.com/KageRyo/Bybit-Predict/issues/25)) defines a fixed trailing analysis window, next-open entry, same-candle-close exit, and neutral-as-cash behavior before calculating close-to-close directional accuracy, win rate, average return, maximum drawdown, and a Sharpe ratio with a zero risk-free rate. It compares the result with buy-and-hold and a 10/20 SMA directional baseline. See [backtesting and evaluation](https://github.com/KageRyo/Bybit-Predict/blob/main/docs/backtesting.md) for the exact rules and limitations.

## Development and quality checks

```bash
ruff check .
ruff format --check .
pyright
pytest
```

`pytest` fails when total coverage falls below **80%**. Pyright runs in basic
mode but treats missing imports as errors; the development extra installs the
dependencies these checks need.

Pull requests run these checks on Python 3.11, 3.12, and 3.13. See
[CONTRIBUTING.md](https://github.com/KageRyo/Bybit-Predict/blob/main/CONTRIBUTING.md) for local setup and the required
`feature/<issue>-<description>` branch convention.

## Publishing

Pushing a final release tag builds an sdist and universal wheel, validates them,
publishes through PyPI Trusted Publishing, then creates a GitHub Release with
the same artifacts. See
[PyPI publishing](https://github.com/KageRyo/Bybit-Predict/blob/main/docs/pypi-publishing.md) for the maintainer-only setup and
release procedure. No long-lived PyPI API token is stored in this repository or
its GitHub Actions secrets.

## Release history and roadmap

- **v4.0.0:** package architecture, public Bybit V5 client, stateless legacy
  strategy, CLI, Discord slash command, configuration, quality gates, and
  documentation.
- **v4.1.0:** reproducible backtesting and evaluation ([#25](https://github.com/KageRyo/Bybit-Predict/issues/25)).
- **v4.1.1:** PyPI distribution, Trusted Publishing, and package-release
  automation ([#37](https://github.com/KageRyo/Bybit-Predict/issues/37)).
- **v4.1.2:** documentation and PyPI metadata corrections
  ([#40](https://github.com/KageRyo/Bybit-Predict/issues/40)).
- **v4.1.3:** CI dependency maintenance and restoration of the complete GPL v2
  license text.
- **v4.1.4:** standard GPL v2 distribution license, recognized by GitHub as
  GPL-2.0.
- **v4.1.5:** candle and API robustness, interval and dataset replay
  validation, linear-time SMA baseline computation, explicit metric semantics,
  enforced quality gates, and main-branch protection.
- **v4.1.6:** corrected linear short returns and initial-equity drawdown, plus completed-candle live analysis with bounded pagination ([#64](https://github.com/KageRyo/Bybit-Predict/issues/64)–[#66](https://github.com/KageRyo/Bybit-Predict/issues/66)).
- **Later:** more strategies can implement the same strategy contract; ML is
  one possible future direction.

## Contributing and history

The repository keeps its original name, issues, forks, stars, merged pull
requests, and Git history. Thanks to prior contributors, including
[RRAaru](https://github.com/RRAaru). New contributors are welcome—start with
[good first issues](https://github.com/KageRyo/Bybit-Predict/labels/good%20first%20issue)
or read [CONTRIBUTING.md](https://github.com/KageRyo/Bybit-Predict/blob/main/CONTRIBUTING.md).

## License and copyright

Bybit-Predict is licensed under the
[GNU General Public License v2.0 or later](https://github.com/KageRyo/Bybit-Predict/blob/main/LICENSE).

Copyright © 2022–2026 **CodeRyo Studio**, **Chien-Hsun Chang**, and
[contributors](https://github.com/KageRyo/Bybit-Predict/blob/main/CONTRIBUTORS.md). CodeRyo Studio is the project maintainer. See
[NOTICE](https://github.com/KageRyo/Bybit-Predict/blob/main/NOTICE) for the complete attribution notice.

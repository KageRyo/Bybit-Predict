# Bybit-Predict

[![License: GPL-2.0-only](https://img.shields.io/badge/License-GPL--2.0--only-blue.svg)](LICENSE)
[![CI](https://github.com/KageRyo/Bybit-Predict/actions/workflows/ci.yml/badge.svg)](https://github.com/KageRyo/Bybit-Predict/actions/workflows/ci.yml)

**Rule-based cryptocurrency market analysis, signal generation, and Discord
integration powered by public Bybit V5 market data.**

> **v4 is in development.** The latest released legacy version is v3.1. This
> branch modernizes the project without discarding its repository, issues,
> merged contributions, or Git history.

[繁體中文](README-zh.md)

## What Bybit-Predict is — and is not

Bybit-Predict analyzes OHLCV candles from Bybit and produces informational
market signals and reference levels. The current `legacy-rule-based-v4`
strategy uses candle shapes, volume power, percentiles, IQR, and
Fibonacci-inspired levels.

It **does not use a machine-learning model** and it is **not a trading bot**.
It never places orders, asks for Bybit API credentials, or promises a market
outcome.

> **Risk notice:** Cryptocurrency markets are volatile. Results are
> informational only, are not financial advice, and must not be treated as a
> recommendation or guarantee to trade.

## Highlights

- One Bybit V5 K-line request retrieves up to 1,000 candles; the default
  analysis uses 180 instead of sending 180 individual requests.
- Typed, UTC-normalized `Candle` and immutable `PredictionResult` models.
- Stateless legacy strategy: concurrent analyses cannot mix their data.
- CLI for local use and an optional non-blocking Discord slash command.
- Active symbols validated using Bybit instrument metadata, not a hard-coded
  coin list.
- Tests, Ruff, Pyright, GitHub Actions CI, and Dependabot.

## Requirements

- Python 3.11 or later
- Internet access to Bybit public market endpoints

**No Bybit account, API key, or API secret is needed** for public market
analysis. The optional Discord interface needs only a Discord bot token.

## Install

```bash
git clone https://github.com/KageRyo/Bybit-Predict.git
cd Bybit-Predict
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
python -m pip install --upgrade pip
python -m pip install .
```

For contributors, install development tools and the Discord extra:

```bash
python -m pip install -e ".[dev]"
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

The command defers external market work to a thread, so a slow Bybit request
does not block Discord's event loop. Responses include the strategy, trend,
signal strength, candle period, and neutral **reference levels** rather than
trading instructions.

Never commit `.env`, bot tokens, API keys, or downloaded data. They are
ignored by default.

## Configuration

| Variable | Required | Purpose |
| --- | --- | --- |
| `DISCORD_BOT_TOKEN` | Discord only | Discord bot authentication token. |
| `DISCORD_GUILD_ID` | No | Development guild for immediate command syncing. |
| `BYBIT_TESTNET` | No | `true` opts into Bybit testnet public data; default is `false`. |

The market-data client intentionally exposes no Bybit credential settings:
public K-line and instrument endpoints do not require authentication.

## Architecture

```text
Bybit V5 public API
        │
BybitV5MarketClient ──→ normalized UTC Candles
        │
PredictionService ──→ LegacyRuleBasedStrategy ──→ PredictionResult
        │                         │
        ├──────── CLI             └── future strategies / v4.1 backtesting
        └──────── Discord slash command
```

- `market/` owns Bybit V5 requests, retry boundaries, pagination, and response
  normalization.
- `strategies/` contains pure, deterministic signal calculations and has no
  dependency on Bybit or Discord.
- `services/` composes market data with a strategy.
- `interfaces/` converts user input/output only.

## Strategy and evaluation

`LegacyRuleBasedStrategy` is deliberately retained as the project’s historical
core. It classifies candle bodies and wicks, compares significant bullish and
bearish volume, and derives optional reference prices from IQR and percentile
calculations. It is explicitly named so later strategies can be compared
fairly.

The planned **v4.1.0** backtesting work ([#25](https://github.com/KageRyo/Bybit-Predict/issues/25)) will define entry/exit semantics and measure directional accuracy, win rate, average return, maximum drawdown, and appropriate baselines. Until then, this project makes no quantitative claim that its signals predict future prices.

## Development and quality checks

```bash
ruff check .
ruff format --check .
pyright
pytest
```

Pull requests run these checks on Python 3.11, 3.12, and 3.13. See
[CONTRIBUTING.md](CONTRIBUTING.md) for local setup and the required
`feature/<issue>-<description>` branch convention.

## Roadmap

- **v4.0.0:** package architecture, public Bybit V5 client, stateless legacy
  strategy, CLI, Discord slash command, configuration, quality gates, and
  documentation.
- **v4.1.0:** reproducible backtesting and evaluation ([#25](https://github.com/KageRyo/Bybit-Predict/issues/25)).
- **Later:** additional strategies may implement the same strategy contract;
  ML is a future option, not an implied feature.

## Contributing and history

The repository name, issues, forks, stars, merged pull requests, and Git
history are intentionally preserved. Thanks to prior contributors, including
[RRAaru](https://github.com/RRAaru). New contributors are welcome—start with
[good first issues](https://github.com/KageRyo/Bybit-Predict/labels/good%20first%20issue)
or read [CONTRIBUTING.md](CONTRIBUTING.md).

## License and copyright

Bybit-Predict is licensed under the
[GNU General Public License v2.0 only](LICENSE).

Copyright © 2022–2026 **CodeRyo Studio**, **Chien-Hsun Chang**, and
[contributors](CONTRIBUTORS.md). CodeRyo Studio is the project maintainer. See
[NOTICE](NOTICE) for the complete attribution notice.

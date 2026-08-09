# SPDX-FileCopyrightText: 2022-2026 CodeRyo Studio, Chien-Hsun Chang, and contributors
# SPDX-License-Identifier: GPL-2.0-or-later
"""Command-line interface for public Bybit market analysis."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Callable, Sequence
from pathlib import Path

from bybit_predict.backtest.data import (
    filter_candles,
    load_candles_csv,
    parse_utc_datetime,
    save_candles_csv,
)
from bybit_predict.backtest.engine import BacktestEngine
from bybit_predict.config import bybit_testnet_enabled
from bybit_predict.exceptions import BybitPredictError, SymbolNotFoundError
from bybit_predict.market.base import HistoricalMarketDataClient
from bybit_predict.market.bybit import BybitV5MarketClient
from bybit_predict.presentation import format_backtest_result_text, format_result_text
from bybit_predict.services.predictor import PredictionService
from bybit_predict.strategies.legacy import LegacyRuleBasedStrategy


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI parser without starting any network client."""
    parser = argparse.ArgumentParser(
        prog="bybit-predict",
        description=(
            "Rule-based cryptocurrency market analysis and reproducible backtesting "
            "using public Bybit V5 data."
        ),
    )
    subcommands = parser.add_subparsers(dest="command", required=True)
    analyze = subcommands.add_parser("analyze", help="Analyze a Bybit trading symbol")
    analyze.add_argument("symbol", help="Bybit symbol, for example BTCUSDT")
    analyze.add_argument(
        "--interval",
        default="240",
        help="Bybit K-line interval (default: 240, or four hours)",
    )
    analyze.add_argument(
        "--limit",
        type=int,
        default=180,
        help="Number of candles to fetch, from 42 to 1000 (default: 180)",
    )
    backtest = subcommands.add_parser(
        "backtest", help="Evaluate a strategy on a historical UTC date range"
    )
    backtest.add_argument("symbol", help="Bybit symbol, for example BTCUSDT")
    backtest.add_argument("--start", required=True, help="Inclusive UTC ISO-8601 date or timestamp")
    backtest.add_argument("--end", required=True, help="Exclusive UTC ISO-8601 date or timestamp")
    backtest.add_argument("--interval", default="240", help="Bybit K-line interval (default: 240)")
    backtest.add_argument(
        "--window",
        type=int,
        default=180,
        help="Closed candles used for each strategy signal (default: 180)",
    )
    backtest.add_argument(
        "--strategy",
        choices=("legacy",),
        default="legacy",
        help="Strategy to evaluate (default: legacy)",
    )
    backtest.add_argument(
        "--data",
        type=Path,
        help="Use a previously saved normalized candle CSV instead of downloading data",
    )
    backtest.add_argument(
        "--save-data",
        type=Path,
        help="Save downloaded normalized candles as CSV for a reproducible rerun",
    )
    backtest.add_argument(
        "--fee-rate",
        type=float,
        default=0.0,
        help="Per-side proportional fee used in simulated trades (default: 0)",
    )
    backtest.add_argument(
        "--slippage-rate",
        type=float,
        default=0.0,
        help="Per-side proportional slippage used in simulated trades (default: 0)",
    )
    subcommands.add_parser("discord", help="Run the optional Discord slash-command bot")
    return parser


def main(
    argv: Sequence[str] | None = None,
    *,
    service_factory: Callable[[], PredictionService] | None = None,
    market_factory: Callable[[], HistoricalMarketDataClient] | None = None,
) -> int:
    """Run the CLI and return a process status without leaking tracebacks to users."""
    parser = build_parser()
    arguments = parser.parse_args(argv)

    if arguments.command == "discord":
        from bybit_predict.interfaces.discord import run_discord_bot

        try:
            run_discord_bot()
        except BybitPredictError as error:
            print(f"Configuration error: {error}", file=sys.stderr)
            return 1
        return 0

    if arguments.command == "backtest":
        return _run_backtest(arguments, market_factory=market_factory)

    if arguments.limit < 42 or arguments.limit > 1000:
        print(
            "Error: --limit must be between 42 and 1000 for the legacy strategy.",
            file=sys.stderr,
        )
        return 2

    try:
        service = service_factory() if service_factory is not None else _default_service()
        result = service.analyze(
            arguments.symbol, interval=arguments.interval, limit=arguments.limit
        )
    except (BybitPredictError, ValueError) as error:
        print(f"Analysis failed: {error}", file=sys.stderr)
        return 1
    print(format_result_text(result))
    return 0


def _default_service() -> PredictionService:
    return PredictionService(BybitV5MarketClient(testnet=bybit_testnet_enabled()))


def _run_backtest(
    arguments: argparse.Namespace,
    *,
    market_factory: Callable[[], HistoricalMarketDataClient] | None,
) -> int:
    """Run one explicit historical evaluation and present only measured outcomes."""
    try:
        start = parse_utc_datetime(arguments.start)
        end = parse_utc_datetime(arguments.end)
        if arguments.data is not None and arguments.save_data is not None:
            raise ValueError("--data and --save-data cannot be used together")
        if arguments.data is not None:
            candles = filter_candles(load_candles_csv(arguments.data), start=start, end=end)
        else:
            market = market_factory() if market_factory is not None else _default_market_client()
            symbol = arguments.symbol.strip().upper()
            if not market.is_valid_symbol(symbol):
                subject = symbol or "The requested symbol"
                raise SymbolNotFoundError(f"{subject} is not an active Bybit symbol")
            candles = market.get_historical_candles(
                symbol, interval=arguments.interval, start=start, end=end
            )
            if arguments.save_data is not None:
                save_candles_csv(arguments.save_data, candles)
        engine = BacktestEngine(
            LegacyRuleBasedStrategy(),
            analysis_window=arguments.window,
            fee_rate=arguments.fee_rate,
            slippage_rate=arguments.slippage_rate,
        )
        result = engine.run(candles, symbol=arguments.symbol, interval=arguments.interval)
    except (BybitPredictError, OSError, ValueError) as error:
        print(f"Backtest failed: {error}", file=sys.stderr)
        return 1
    print(format_backtest_result_text(result))
    return 0


def _default_market_client() -> BybitV5MarketClient:
    return BybitV5MarketClient(testnet=bybit_testnet_enabled())

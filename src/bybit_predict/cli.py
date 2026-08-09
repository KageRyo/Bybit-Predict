# SPDX-FileCopyrightText: 2022-2026 CodeRyo Studio, Chien-Hsun Chang, and contributors
# SPDX-License-Identifier: GPL-2.0-only
"""Command-line interface for public Bybit market analysis."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Callable, Sequence

from bybit_predict.config import bybit_testnet_enabled
from bybit_predict.exceptions import BybitPredictError
from bybit_predict.market.bybit import BybitV5MarketClient
from bybit_predict.presentation import format_result_text
from bybit_predict.services.predictor import PredictionService


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI parser without starting any network client."""
    parser = argparse.ArgumentParser(
        prog="bybit-predict",
        description="Rule-based cryptocurrency market analysis using public Bybit V5 data.",
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
    subcommands.add_parser("discord", help="Run the optional Discord slash-command bot")
    return parser


def main(
    argv: Sequence[str] | None = None,
    *,
    service_factory: Callable[[], PredictionService] | None = None,
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

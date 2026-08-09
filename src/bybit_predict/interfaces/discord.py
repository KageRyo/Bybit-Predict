# SPDX-FileCopyrightText: 2022-2026 CodeRyo Studio, Chien-Hsun Chang, and contributors
# SPDX-License-Identifier: GPL-2.0-only
"""Discord slash-command adapter.

The module imports discord.py only when the optional interface is started, so
core analysis remains usable in automation and tests without a Discord client.
"""

from __future__ import annotations

import asyncio
from importlib import import_module
from typing import Any

from bybit_predict.config import DiscordSettings, bybit_testnet_enabled, load_discord_settings
from bybit_predict.exceptions import BybitPredictError
from bybit_predict.market.bybit import BybitV5MarketClient
from bybit_predict.models import PredictionResult
from bybit_predict.presentation import DISPLAY_TRENDS
from bybit_predict.services.predictor import PredictionService


def create_bot(service: PredictionService, settings: DiscordSettings) -> Any:
    """Create a Discord bot whose commands delegate work to ``PredictionService``."""
    try:
        discord: Any = import_module("discord")
        app_commands: Any = import_module("discord.app_commands")
        commands: Any = import_module("discord.ext.commands")
    except ImportError as error:  # pragma: no cover - installation concern
        raise BybitPredictError("discord.py is required for the Discord interface") from error

    class BybitPredictBot(commands.Bot):
        async def setup_hook(self) -> None:
            if settings.guild_id is None:
                await self.tree.sync()
                return
            guild = discord.Object(id=settings.guild_id)
            self.tree.copy_global_to(guild=guild)
            await self.tree.sync(guild=guild)

    intents = discord.Intents.none()
    intents.guilds = True
    bot = BybitPredictBot(command_prefix="!", intents=intents)

    @bot.tree.command(
        name="predict", description="Analyze a Bybit symbol with the legacy rule-based strategy"
    )
    @app_commands.describe(
        symbol="Bybit trading symbol, for example BTCUSDT",
        interval="K-line interval, for example 240 for four hours",
        candles="Number of candles to analyze (42-1000)",
    )
    async def predict(
        interaction: Any,
        symbol: str,
        interval: str = "240",
        candles: int = 180,
    ) -> None:
        if not 42 <= candles <= 1000:
            await interaction.response.send_message(
                "`candles` must be between 42 and 1000.", ephemeral=True
            )
            return
        await interaction.response.defer(thinking=True)
        try:
            result = await asyncio.to_thread(
                service.analyze, symbol, interval=interval, limit=candles
            )
        except (BybitPredictError, ValueError) as error:
            await interaction.followup.send(f"Analysis failed: {error}", ephemeral=True)
            return
        await interaction.followup.send(embed=_result_embed(discord, result))

    return bot


def run_discord_bot() -> None:
    """Load environment settings and start the slash-command interface."""
    settings = load_discord_settings()
    service = PredictionService(BybitV5MarketClient(testnet=bybit_testnet_enabled()))
    create_bot(service, settings).run(settings.token)


def _result_embed(discord: Any, result: PredictionResult) -> Any:
    """Keep Discord rendering separate from the market-analysis domain."""
    embed = discord.Embed(
        title=f"{result.symbol} · {result.interval} Analysis",
        description="Rule-based signal for reference only — not financial advice.",
        color=0x7CEEFF,
    )
    embed.add_field(name="Trend", value=DISPLAY_TRENDS[result.trend].title(), inline=True)
    embed.add_field(name="Signal strength", value=f"{result.signal_strength:.2%}", inline=True)
    embed.add_field(name="Strategy", value=result.strategy, inline=False)
    embed.add_field(name="Candles", value=str(result.candle_count), inline=True)
    embed.add_field(
        name="Data period (UTC)",
        value=f"{result.period_start:%Y-%m-%d %H:%M} → {result.period_end:%Y-%m-%d %H:%M}",
        inline=False,
    )
    if result.reference_levels:
        value = "\n".join(
            f"{level.label}: `{level.price:.4f}`" for level in result.reference_levels
        )
    else:
        value = "Neutral signal — no directional price levels."
    embed.add_field(name="Reference levels", value=value, inline=False)
    time_value = "\n".join(
        f"{reference.label}: {reference.timestamp:%Y-%m-%d %H:%M UTC}"
        for reference in result.time_references
    )
    embed.add_field(name="Time references", value=time_value, inline=False)
    return embed

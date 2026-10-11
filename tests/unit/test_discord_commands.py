from __future__ import annotations

import asyncio
from collections.abc import Callable
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from bybit_predict.config import DiscordSettings
from bybit_predict.interfaces.discord import create_bot
from bybit_predict.market.bybit import BybitV5MarketClient
from bybit_predict.services.predictor import PredictionService


@pytest.mark.parametrize("count", [43, 42])
def test_discord_predict_uses_closed_candles_or_reports_shortage(
    count: int, live_market_factory: Callable[[int], BybitV5MarketClient]
) -> None:
    interaction = SimpleNamespace(
        response=SimpleNamespace(defer=AsyncMock(), send_message=AsyncMock()),
        followup=SimpleNamespace(send=AsyncMock()),
    )

    async def predict() -> None:
        service = PredictionService(live_market_factory(count))
        bot = create_bot(service, DiscordSettings(token="offline-test-placeholder"))
        try:
            command = bot.tree.get_command("predict")
            assert command is not None
            await command.callback(interaction, "BTCUSDT", candles=42)
        finally:
            await bot.close()

    asyncio.run(predict())
    reply = interaction.followup.send.await_args
    assert reply is not None
    if count == 43:
        fields = {field.name: field.value for field in reply.kwargs["embed"].fields}
        assert fields["Candles"] == "42"
        assert fields["Data period (UTC)"].endswith("2026-10-08 08:00")
    else:
        assert reply.kwargs["ephemeral"] is True
        assert "requested=42 available=41" in reply.args[0]

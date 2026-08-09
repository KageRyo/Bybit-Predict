from __future__ import annotations

from typing import Any

from bybit_predict.interfaces.discord import _result_embed
from bybit_predict.services.predictor import PredictionService


class FakeEmbed:
    def __init__(self, **kwargs: object) -> None:
        self.kwargs = kwargs
        self.fields: list[dict[str, object]] = []

    def add_field(self, **kwargs: object) -> None:
        self.fields.append(kwargs)


class FakeDiscord:
    Embed = FakeEmbed


def test_discord_embed_uses_neutral_reference_language(candles: tuple[Any, ...]) -> None:
    class Market:
        def is_valid_symbol(self, symbol: str) -> bool:
            return True

        def get_candles(self, symbol: str, interval: str, limit: int) -> tuple[Any, ...]:
            return candles

    result = PredictionService(Market()).analyze("BTCUSDT", limit=42)
    embed = _result_embed(FakeDiscord, result)

    assert embed.kwargs["title"] == "BTCUSDT · 240 Analysis"
    assert any(field["name"] == "Reference levels" for field in embed.fields)
    assert all("order" not in str(field).lower() for field in embed.fields)

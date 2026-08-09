from __future__ import annotations

import pytest

from bybit_predict.config import bybit_testnet_enabled, load_discord_settings
from bybit_predict.exceptions import ConfigurationError


def test_load_discord_settings_reads_required_token_and_optional_guild() -> None:
    settings = load_discord_settings({"DISCORD_BOT_TOKEN": "token", "DISCORD_GUILD_ID": "123"})

    assert settings.token == "token"
    assert settings.guild_id == 123


def test_load_discord_settings_rejects_missing_token() -> None:
    with pytest.raises(ConfigurationError, match="DISCORD_BOT_TOKEN"):
        load_discord_settings({})


@pytest.mark.parametrize("value", ["1", "true", "YES", "on"])
def test_bybit_testnet_enabled_accepts_truthy_values(value: str) -> None:
    assert bybit_testnet_enabled({"BYBIT_TESTNET": value})


def test_bybit_testnet_enabled_rejects_invalid_values() -> None:
    with pytest.raises(ConfigurationError, match="BYBIT_TESTNET"):
        bybit_testnet_enabled({"BYBIT_TESTNET": "perhaps"})

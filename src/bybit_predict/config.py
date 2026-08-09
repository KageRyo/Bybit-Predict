# SPDX-FileCopyrightText: 2022-2026 CodeRyo Studio, Chien-Hsun Chang, and contributors
# SPDX-License-Identifier: GPL-2.0-only
"""Environment-based runtime configuration."""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass

from bybit_predict.exceptions import ConfigurationError


@dataclass(frozen=True, slots=True)
class DiscordSettings:
    """Runtime settings required by the optional Discord interface."""

    token: str
    guild_id: int | None = None


def load_discord_settings(environ: Mapping[str, str] | None = None) -> DiscordSettings:
    """Read Discord settings without ever loading a tracked configuration file."""
    environment = os.environ if environ is None else environ
    token = environment.get("DISCORD_BOT_TOKEN", "").strip()
    if not token:
        raise ConfigurationError(
            "DISCORD_BOT_TOKEN is required to run Discord. Copy .env.example and "
            "provide the token through your environment."
        )

    guild_id_text = environment.get("DISCORD_GUILD_ID", "").strip()
    if not guild_id_text:
        return DiscordSettings(token=token)

    try:
        guild_id = int(guild_id_text)
    except ValueError as error:
        raise ConfigurationError("DISCORD_GUILD_ID must be an integer") from error
    if guild_id <= 0:
        raise ConfigurationError("DISCORD_GUILD_ID must be positive")
    return DiscordSettings(token=token, guild_id=guild_id)


def bybit_testnet_enabled(environ: Mapping[str, str] | None = None) -> bool:
    """Return the explicit opt-in testnet setting for public market data."""
    environment = os.environ if environ is None else environ
    value = environment.get("BYBIT_TESTNET", "false").strip().lower()
    if value in {"1", "true", "yes", "on"}:
        return True
    if value in {"0", "false", "no", "off", ""}:
        return False
    raise ConfigurationError("BYBIT_TESTNET must be true or false")

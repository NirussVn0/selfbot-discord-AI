# whitelist

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from selfbot_discord.config.models import WhitelistConfig

if TYPE_CHECKING:
    import discord


@dataclass(frozen=True)
class WhitelistEvaluation:
    allow: bool
    reason: str | None = None


class WhitelistService:

    def __init__(self, config: WhitelistConfig) -> None:
        self._config = config

    @property
    def config(self) -> WhitelistConfig:
        return self._config

    def _is_user_allowed(self, user_id: int) -> bool:
        if not self._config.user_ids:
            return True
        return user_id in self._config.user_ids or user_id in self._config.admin_ids

    def _is_guild_allowed(self, guild_id: int) -> bool:
        if not self._config.guild_ids:
            return True
        return guild_id in self._config.guild_ids

    def _is_channel_allowed(self, channel_id: int) -> bool:
        if not self._config.channel_ids:
            return True
        return channel_id in self._config.channel_ids

    def evaluate(self, message: "discord.Message") -> WhitelistEvaluation:

        if not self._config.enabled:
            return WhitelistEvaluation(allow=True)

        author_id = message.author.id
        if author_id in self._config.admin_ids:
            return WhitelistEvaluation(allow=True)
        if not self._is_user_allowed(author_id):
            return WhitelistEvaluation(allow=False, reason="user not whitelisted")

        if message.guild is None:
            if self._config.allow_direct_messages:
                return WhitelistEvaluation(allow=True)
            return WhitelistEvaluation(allow=False, reason="direct messages disabled")

        guild_id = message.guild.id
        if not self._is_guild_allowed(guild_id):
            return WhitelistEvaluation(allow=False, reason="guild not whitelisted")

        channel_id = message.channel.id
        if not self._is_channel_allowed(channel_id):
            return WhitelistEvaluation(allow=False, reason="channel not whitelisted")

        return WhitelistEvaluation(allow=True)

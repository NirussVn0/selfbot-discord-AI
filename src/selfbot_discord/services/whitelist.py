# whitelist

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Iterable

from selfbot_discord.config.manager import ConfigManager
from selfbot_discord.config.models import WhitelistConfig

if TYPE_CHECKING:
    import discord


@dataclass(frozen=True)
class WhitelistEvaluation:
    allow: bool
    reason: str | None = None


class WhitelistService:

    def __init__(self, manager: ConfigManager) -> None:
        self._manager = manager

    @property
    def config(self) -> WhitelistConfig:
        return self._manager.config.whitelist

    def _is_user_allowed(self, user_id: int) -> bool:
        config = self.config
        if not config.user_ids:
            return True
        return user_id in config.user_ids or user_id in config.admin_ids

    def _is_guild_allowed(self, guild_id: int) -> bool:
        config = self.config
        if not config.guild_ids:
            return True
        return guild_id in config.guild_ids

    def _is_channel_allowed(self, channel_id: int) -> bool:
        config = self.config
        if not config.channel_ids:
            return True
        return channel_id in config.channel_ids

    def evaluate(self, message: "discord.Message") -> WhitelistEvaluation:
        config = self.config
        if not config.enabled:
            return WhitelistEvaluation(allow=True)

        author_id = message.author.id
        if author_id in config.admin_ids:
            return WhitelistEvaluation(allow=True)
        if not self._is_user_allowed(author_id):
            return WhitelistEvaluation(allow=False, reason="user not whitelisted")

        if message.guild is None:
            if config.allow_direct_messages:
                return WhitelistEvaluation(allow=True)
            return WhitelistEvaluation(allow=False, reason="direct messages disabled")

        guild_id = message.guild.id
        if not self._is_guild_allowed(guild_id):
            return WhitelistEvaluation(allow=False, reason="guild not whitelisted")

        channel_id = message.channel.id
        if not self._is_channel_allowed(channel_id):
            return WhitelistEvaluation(allow=False, reason="channel not whitelisted")

        return WhitelistEvaluation(allow=True)

    def summary(self) -> dict[str, list[int] | bool]:
        config = self.config
        return {
            "enabled": config.enabled,
            "admin_ids": list(config.admin_ids),
            "user_ids": list(config.user_ids),
            "guild_ids": list(config.guild_ids),
            "channel_ids": list(config.channel_ids),
            "allow_direct_messages": config.allow_direct_messages,
        }

    def toggle(self, enabled: bool) -> bool:
        config = self.config
        if config.enabled == enabled:
            return False
        config.enabled = enabled
        self._manager.save()
        return True

    def add_entries(self, field: str, values: Iterable[int]) -> list[int]:
        whitelist = self.config
        try:
            target_list = getattr(whitelist, field)
        except AttributeError as exc:
            raise ValueError(f"Unknown whitelist field '{field}'.") from exc
        if not isinstance(target_list, list):
            raise ValueError(f"Field '{field}' is not a list.")
        added: list[int] = []
        for value in values:
            if value not in target_list:
                target_list.append(value)
                added.append(value)
        if added:
            self._manager.save()
        return added

    def remove_entries(self, field: str, values: Iterable[int]) -> list[int]:
        whitelist = self.config
        try:
            target_list = getattr(whitelist, field)
        except AttributeError as exc:
            raise ValueError(f"Unknown whitelist field '{field}'.") from exc
        if not isinstance(target_list, list):
            raise ValueError(f"Field '{field}' is not a list.")
        removed: list[int] = []
        for value in values:
            if value in target_list:
                target_list.remove(value)
                removed.append(value)
        if removed:
            self._manager.save()
        return removed

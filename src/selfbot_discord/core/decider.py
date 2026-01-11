from __future__ import annotations

import logging
import random
import time
from dataclasses import dataclass
from typing import TYPE_CHECKING

import discord

if TYPE_CHECKING:
    from discord import ClientUser, Message
    from selfbot_discord.config.models import AppConfig

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class ResponseDecision:
    should_reply: bool
    reason: str | None = None


class ResponseDecider:
    # Apply response heuristics such as mention detection and cooldowns
    
    def __init__(self, config: AppConfig) -> None:
        self._config = config
        self._cooldowns: dict[int, float] = {}

    def _has_cooldown(self, channel_id: int) -> bool:
        cooldown = self._config.discord.auto_reply_cooldown_seconds
        if cooldown <= 0:
            return False
        last_reply = self._cooldowns.get(channel_id)
        if last_reply is None:
            return False
        elapsed = time.monotonic() - last_reply
        return elapsed < cooldown

    def _should_auto_reply(self, channel_id: int) -> bool:
        probability = self._config.discord.auto_reply_probability
        if probability <= 0:
            return False
        if self._has_cooldown(channel_id):
            return False
        roll = random.random()
        if roll <= probability:
            logger.debug("Auto-reply roll passed for channel %s (roll=%.3f).", channel_id, roll)
            return True
        return False

    def register_reply(self, channel_id: int) -> None:
        self._cooldowns[channel_id] = time.monotonic()

    def decide(self, message: Message, bot_user: ClientUser) -> ResponseDecision:
        config = self._config.discord
        mention_ids = {user.id for user in message.mentions}
        is_direct_mention = bot_user.id in mention_ids

        if is_direct_mention:
            return ResponseDecision(should_reply=True, reason="mentioned")

        if config.mention_required:
            return ResponseDecision(should_reply=False, reason="mention required")

        if isinstance(message.channel, discord.Thread) and not config.allow_thread_messages:
            return ResponseDecision(should_reply=False, reason="thread messages disabled")
            
        if self._should_auto_reply(message.channel.id):
            return ResponseDecision(should_reply=True, reason="auto reply triggered")

        return ResponseDecision(should_reply=False, reason="auto reply roll failed")

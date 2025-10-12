from __future__ import annotations

import asyncio
import logging
import random
import time
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

import discord
from rich.markup import escape

from selfbot_discord.ai.gemini import GeminiAIService
from selfbot_discord.config.models import AppConfig
from selfbot_discord.services.context import ConversationStore
from selfbot_discord.services.whitelist import WhitelistService
from selfbot_discord.ui import ConsoleUI

if TYPE_CHECKING:
    from discord import Message


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

    def decide(self, message: Message, bot_user: discord.ClientUser) -> ResponseDecision:
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

class DiscordSelfBot(discord.Client):
    # Discord self-bot powered by Gemini responses and rich CLI feedback.

    def __init__(
        self,
        config: AppConfig,
        *,
        whitelist: WhitelistService,
        ai_service: GeminiAIService,
        conversation_store: ConversationStore | None = None,
        ui: ConsoleUI | None = None,
    ) -> None:
        kwargs: dict[str, Any] = {}
        intents_cls = getattr(discord, "Intents", None)
        if intents_cls is not None:
            intents = intents_cls.default()
            if hasattr(intents, "message_content"):
                intents.message_content = True
            kwargs["intents"] = intents
        else:
            logger.debug("discord.Intents unavailable; falling back to default discord.Client configuration.")
        super().__init__(**kwargs)
        self._config = config
        self._whitelist = whitelist
        self._ai_service = ai_service
        self._conversation_store = conversation_store or ConversationStore()
        self._decider = ResponseDecider(config)
        self._ui = ui

    @staticmethod
    def _describe_channel(message: "Message") -> str:
        if message.guild is None:
            return "Direct Message"
        channel = message.channel
        if isinstance(channel, discord.Thread):
            parent = getattr(channel, "parent", None)
            parent_name = getattr(parent, "name", "thread")
            return f"{message.guild.name}#{parent_name}/{channel.name}"
        channel_name = getattr(channel, "name", None)
        if channel_name:
            return f"{message.guild.name}#{channel_name}"
        return message.guild.name

    async def safe_set_presence(self) -> None:
        # Apply the configured presence once the gateway is ready.

        presence = self._config.discord.presence_message
        if not presence:
            return
        await self.wait_until_ready()
        ws = getattr(self, "ws", None)
        if ws is None:
            logger.debug("Gateway websocket unavailable; skipping presence update.")
            if self._ui:
                self._ui.notify_event(
                    "Skipping presence update until gateway is ready.",
                    icon="⚠",
                    style="yellow",
                    force=True,
                )
            return
        activity = discord.Activity(type=discord.ActivityType.listening, name=presence)
        applied = False
        try:
            await self.change_presence(activity=activity)
            applied = True
        except AttributeError:
            logger.debug("Gateway not ready during presence update; retrying once.")
            await asyncio.sleep(1)
            ws = getattr(self, "ws", None)
            if ws is None:
                logger.debug("Gateway websocket still unavailable; skipping presence update.")
                return
            await self.change_presence(activity=activity)
            applied = True
        if applied and self._ui:
            self._ui.notify_event(
                f"Presence set to [italic]{presence}[/]",
                icon="🎧",
                style="magenta",
                force=True,
            )

    async def on_ready(self) -> None:
        if self.user is None:
            return
        logger.info("Logged in as %s (%s).", self.user.name, self.user.id)
        if self._ui:
            self._ui.mark_ready(self.user.name, self.user.id, len(self.guilds))
            self._ui.notify_event(
                f"Connected as [bold]{self.user.name}[/] ({self.user.id})",
                icon="✅",
                style="green",
                force=True,
            )
        asyncio.create_task(self.safe_set_presence())

    async def on_message(self, message: Message) -> None:  # noqa: D401 - discord signature
        if self.user is None:
            logger.debug("Client user not yet ready; skipping message processing.")
            return
        if message.author.id == self.user.id:
            self._conversation_store.append(message.channel.id, "me", message.content)
            return
        if message.author.bot:
            return

        author_display = message.author.display_name or message.author.name
        author_markup = escape(author_display)
        channel_label = escape(self._describe_channel(message))

        if self._ui:
            self._ui.increment_messages()
            self._ui.notify_event(
                f"Message from [bold]{author_markup}[/] in [italic]{channel_label}[/]",
                icon="✉️",
                style="cyan",
            )

        whitelist_result = self._whitelist.evaluate(message)
        if not whitelist_result.allow:
            logger.debug(
                "Whitelist rejected message %s in channel %s: %s",
                message.id,
                message.channel.id,
                whitelist_result.reason,
            )
            if self._ui:
                reason = escape(whitelist_result.reason or "blocked")
                self._ui.notify_event(
                    f"Blocked message from [bold]{author_markup}[/] — {reason}.",
                    icon="🔒",
                    style="yellow",
                )
            return

        decision = self._decider.decide(message, self.user)
        if not decision.should_reply:
            logger.debug(
                "Skipping reply for message %s: %s",
                message.id,
                decision.reason,
            )
            self._conversation_store.append(message.channel.id, author_display, message.content)
            if self._ui:
                reason = escape(decision.reason or "no trigger")
                self._ui.notify_event(
                    f"Ignored message from [bold]{author_markup}[/] — {reason}.",
                    icon="💤",
                    style="grey50",
                )
            return

        try:
            reply = await self._generate_reply(message)
        except Exception as exc:  # pragma: no cover - runtime API failures
            logger.exception("Failed to produce reply: %s", exc)
            if self._ui:
                self._ui.notify_event(
                    f"Failed to produce reply for [bold]{author_markup}[/].",
                    icon="⚠",
                    style="red",
                    force=True,
                )
            return

        if not reply.strip():
            logger.debug("AI returned empty reply for message %s.", message.id)
            if self._ui:
                self._ui.notify_event(
                    f"AI returned an empty reply for [bold]{author_markup}[/].",
                    icon="⚠",
                    style="yellow",
                    force=True,
                )
            return

        await message.channel.send(reply)
        self._decider.register_reply(message.channel.id)
        self._conversation_store.append(message.channel.id, "bot", reply)
        if self._ui:
            self._ui.increment_replies()
            self._ui.notify_event(
                f"Responded to [bold]{author_markup}[/] in [italic]{channel_label}[/]",
                icon="🤖",
                style="green",
                force=True,
            )

    async def _generate_reply(self, message: Message) -> str:
        author_name = message.author.display_name or message.author.name
        conversation = self._conversation_store.snapshot(message.channel.id)
        self._conversation_store.append(message.channel.id, author_name, message.content)
        if self._ui:
            style = self._ui.STATUS_STYLES.get("BUSY", "magenta")
            with self._ui.activity("BUSY", style=style):
                return await self._ai_service.generate_reply(
                    author_name=author_name,
                    message_content=message.content,
                    conversation=conversation,
                )
        return await self._ai_service.generate_reply(
            author_name=author_name,
            message_content=message.content,
            conversation=conversation,
        )

    async def close(self) -> None:
        logger.info("Shutting down self-bot.")
        if self._ui:
            self._ui.notify_event("Disconnecting from Discord...", icon="⏻", style="yellow", force=True)
        await super().close()

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(persona={self._config.ai.persona!r})"

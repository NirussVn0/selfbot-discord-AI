import logging
import asyncio
from typing import TYPE_CHECKING
import discord
from rich.markup import escape

from selfbot_discord.utils.formatting import TextStyler

if TYPE_CHECKING:
    from selfbot_discord.core.bot import DiscordSelfBot
    from discord import Message

logger = logging.getLogger(__name__)

class MessageHandler:
    def __init__(self, bot: "DiscordSelfBot"):
        self.bot = bot

    @staticmethod
    async def _safe_send(channel, content: str):
        """Send message with auto-chunking for Discord's 2000 char limit."""
        chunks = TextStyler.chunk_message(content)
        last_msg = None
        for chunk in chunks:
            last_msg = await channel.send(chunk)
        return last_msg

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

    async def _generate_reply(self, message: "Message") -> str:
        author_name = message.author.display_name or message.author.name
        conversation = self.bot._conversation_store.snapshot(message.channel.id)
        self.bot._conversation_store.append(message.channel.id, author_name, message.content)
        if self.bot._ui:
            style = self.bot._ui.STATUS_STYLES.get("BUSY", "magenta")
            with self.bot._ui.activity("BUSY", style=style):
                return await self.bot._ai_service.generate_reply(
                    author_name=author_name,
                    message_content=message.content,
                    conversation=conversation,
                )
        return await self.bot._ai_service.generate_reply(
            author_name=author_name,
            message_content=message.content,
            conversation=conversation,
        )

    async def handle_message(self, message: "Message") -> None:
        if self.bot.user is None:
            logger.debug("Client user not yet ready; skipping message processing.")
            return
            
        if message.author.id == self.bot.user.id:
            self.bot._conversation_store.append(message.channel.id, "me", message.content)
            if self.bot._config.discord.allow_self_commands:
                if await self.bot._handle_command(message):
                    return
            return
            
        if message.author.bot:
            if message.author.id == 408785106942164992 and self.bot._owo_cog:
                await self.bot._owo_cog.process_owo_message(message)
            return

        # Copycat Logic
        action_cog = getattr(self.bot, "_action_cog", None)
        if action_cog and action_cog.copycat_user_id == message.author.id:
            if message.content:
                await message.channel.send(message.content)
            return

        # AFK Logic
        if self.bot._config.discord.afk_enabled and not message.author.bot:
            is_dm = isinstance(message.channel, discord.DMChannel)
            is_mentioned = self.bot.user in message.mentions
            if is_dm or is_mentioned:
                afk_msg = self.bot._config.discord.afk_message
                if afk_msg:
                    await message.channel.send(f"[AFK] {afk_msg}")
                return

        author_display = message.author.display_name or message.author.name
        author_markup = escape(author_display)
        channel_label = escape(self._describe_channel(message))

        if self.bot._ui:
            self.bot._ui.increment_messages()
            self.bot._ui.notify_event(
                f"Message from [bold]{author_markup}[/] in [italic]{channel_label}[/]",
                icon="✉️",
                style="cyan",
            )

        whitelist_result = self.bot._whitelist.evaluate(message)
        if not whitelist_result.allow:
            logger.debug(
                "Whitelist rejected message %s in channel %s: %s",
                message.id,
                message.channel.id,
                whitelist_result.reason,
            )
            if self.bot._ui:
                reason = escape(whitelist_result.reason or "blocked")
                self.bot._ui.notify_event(
                    f"Blocked message from [bold]{author_markup}[/] — {reason}.",
                    icon="🔒",
                    style="yellow",
                )
            return

        if await self.bot._handle_command(message):
            return

        decision = self.bot._decider.decide(message, self.bot.user)
        if not decision.should_reply:
            logger.debug(
                "Skipping reply for message %s: %s",
                message.id,
                decision.reason,
            )
            self.bot._conversation_store.append(message.channel.id, author_display, message.content)
            if self.bot._ui:
                reason = escape(decision.reason or "no trigger")
                self.bot._ui.notify_event(
                    f"Ignored message from [bold]{author_markup}[/] — {reason}.",
                    icon="💤",
                    style="grey50",
                )
            return

        try:
            reply = await self._generate_reply(message)
        except Exception as exc: 
            logger.exception("Failed to produce reply: %s", exc)
            if self.bot._ui:
                self.bot._ui.notify_event(
                    f"Failed to produce reply for [bold]{author_markup}[/].",
                    icon="⚠",
                    style="red",
                    force=True,
                )
            fallback = "Sorry, the AI service is unavailable right now."
            await self._safe_send(message.channel, fallback)
            self.bot._decider.register_reply(message.channel.id)
            self.bot._conversation_store.append(message.channel.id, "bot", fallback)
            if self.bot._ui:
                self.bot._ui.increment_replies()
                self.bot._ui.notify_event(
                    f"Sent fallback reply to [bold]{author_markup}[/].",
                    icon="🛟",
                    style="yellow",
                    force=True,
                )
            return

        if not reply.strip():
            logger.debug("AI returned empty reply for message %s.", message.id)
            if self.bot._ui:
                self.bot._ui.notify_event(
                    f"AI returned an empty reply for [bold]{author_markup}[/].",
                    icon="⚠",
                    style="yellow",
                    force=True,
                )
            fallback = self.bot._config.ai.empty_reply_fallback or ""
            fallback = fallback.strip()
            if fallback:
                await self._safe_send(message.channel, fallback)
                self.bot._decider.register_reply(message.channel.id)
                self.bot._conversation_store.append(message.channel.id, "bot", fallback)
                if self.bot._ui:
                    self.bot._ui.increment_replies()
                    self.bot._ui.notify_event(
                        f"Sent fallback reply to [bold]{author_markup}[/].",
                        icon="🛟",
                        style="yellow",
                        force=True,
                    )
            else:
                logger.debug("Skipping fallback reply; no fallback message configured.")
                if self.bot._ui:
                    self.bot._ui.notify_event(
                        f"Skipped fallback reply to [bold]{author_markup}[/].",
                        icon="🛟",
                        style="grey50",
                        force=True,
                    )
            return

        await self._safe_send(message.channel, reply)
        self.bot._decider.register_reply(message.channel.id)
        self.bot._conversation_store.append(message.channel.id, "bot", reply)
        if self.bot._ui:
            self.bot._ui.increment_replies()
            self.bot._ui.notify_event(
                f"Responded to [bold]{author_markup}[/] in [italic]{channel_label}[/]",
                icon="🤖",
                style="green",
                force=True,
            )

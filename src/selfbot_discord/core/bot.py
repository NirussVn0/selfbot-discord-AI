# Copyright (c) [2025] NirrussVn0

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
from selfbot_discord.commands.base import CommandContext, CommandError
from selfbot_discord.commands.cogs.claimowo import ClaimOWOCog
from selfbot_discord.commands.cogs.general import GeneralCog
from selfbot_discord.commands.cogs.whitelist import WhitelistCog
from selfbot_discord.commands.registry import CommandRegistry
from selfbot_discord.config.manager import ConfigManager
from selfbot_discord.config.models import AppConfig
from selfbot_discord.services.config_watcher import ConfigWatcher
from selfbot_discord.services.context import ConversationStore
from selfbot_discord.services.owo import OWOGameService, OWOStatsTracker
from selfbot_discord.services.whitelist import WhitelistService
from selfbot_discord.ui import ConsoleUI
from selfbot_discord.core.decider import ResponseDecider
from selfbot_discord.core.handlers import MessageHandler

if TYPE_CHECKING:
    from discord import Message


logger = logging.getLogger(__name__)



class DiscordSelfBot(discord.Client):
    # Discord self-bot powered by Gemini responses and rich CLI feedback.

    def __init__(
        self,
        config: AppConfig,
        *,
        config_manager: ConfigManager,
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
        self._config_manager = config_manager
        self._whitelist = whitelist
        self._ai_service = ai_service
        self._conversation_store = conversation_store or ConversationStore()
        self._decider = ResponseDecider(config)
        self._ui = ui
        self._started_at = time.monotonic()
        self._command_registry = CommandRegistry()
        self._owo_cog = None
        self._register_cogs()
        self._config_watcher = ConfigWatcher(
            config_manager,
            on_reload=self.apply_configuration,
            ui=self._ui,
        )
        self._handler = MessageHandler(self)

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
        except TypeError as exc:
            logger.warning("Discord client rejected presence update: %s", exc)
            if self._ui:
                self._ui.notify_event(
                    "Presence update unsupported by this Discord client build.",
                    icon="⚠",
                    style="yellow",
                    force=True,
                )
            return
        except AttributeError:
            logger.debug("Gateway not ready during presence update; retrying once.")
            await asyncio.sleep(1)
            ws = getattr(self, "ws", None)
            if ws is None:
                logger.debug("Gateway websocket still unavailable; skipping presence update.")
                return
            try:
                await self.change_presence(activity=activity)
                applied = True
            except TypeError as exc:
                logger.warning("Discord client rejected presence update on retry: %s", exc)
                if self._ui:
                    self._ui.notify_event(
                        "Presence update unsupported by this Discord client build.",
                        icon="⚠",
                        style="yellow",
                        force=True,
                    )
                return
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
        self._config_watcher.start()
        asyncio.create_task(self.safe_set_presence())

    async def on_message(self, message: Message) -> None:  # noqa: D401 - discord signature
        await self._handler.handle_message(message)

    # _generate_reply moved to MessageHandler

    async def close(self) -> None:
        logger.info("Shutting down self-bot.")
        if self._ui:
            self._ui.notify_event("Disconnecting from Discord...", icon="⏻", style="yellow", force=True)
        await self._config_watcher.stop()
        await super().close()

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(persona={self._config.ai.persona!r})"

    @property
    def uptime_seconds(self) -> float:
        return time.monotonic() - self._started_at

    async def schedule_ephemeral_cleanup(self, *messages: discord.Message, delay: float = 5.0) -> None:
        targets = [message for message in messages if message is not None]
        if not targets:
            return

        async def _cleanup() -> None:
            await asyncio.sleep(delay)
            for message in targets:
                try:
                    await message.delete()
                except (discord.HTTPException, AttributeError):
                    continue

        asyncio.create_task(_cleanup())

    @staticmethod
    def format_duration(seconds: float) -> str:
        seconds = int(max(seconds, 0))
        days, rem = divmod(seconds, 86400)
        hours, rem = divmod(rem, 3600)
        minutes, secs = divmod(rem, 60)
        parts: list[str] = []
        if days:
            parts.append(f"{days}d")
        if days or hours:
            parts.append(f"{hours}h")
        if days or hours or minutes:
            parts.append(f"{minutes}m")
        parts.append(f"{secs}s")
        return " ".join(parts)

    def _register_cogs(self) -> None:
        stats_tracker = OWOStatsTracker()
        game_service = OWOGameService(stats_tracker)
        self._owo_cog = ClaimOWOCog(self, game_service, stats_tracker)
        cogs = [
            GeneralCog(self),
            WhitelistCog(self),
            self._owo_cog,
        ]
        for cog in cogs:
            self._command_registry.register_cog(cog)

    async def apply_configuration(self, config: AppConfig) -> None:
        self._config = config
        self._decider = ResponseDecider(config)
        if self._ui:
            self._ui.notify_event(
                message="Configuration reloaded",
                icon="🔄",
                style="cyan"
            )
        asyncio.create_task(self.safe_set_presence())

    async def on_message_edit(self, before: Message, after: Message) -> None:
        if after.author.bot:
            if after.author.id == 408785106942164992 and self._owo_cog:
                await self._owo_cog.process_owo_message(after)
            return

    async def _handle_command(self, message: Message) -> bool:
        if self.user is None:
            return False
        content = message.content or ""
        prefix = self._config.discord.command_prefix
        if not prefix or not content.startswith(prefix):
            return False

        command_line = content[len(prefix) :].strip()
        if not command_line:
            return False

        parts = command_line.split()
        command_name = parts[0].lower()
        args = parts[1:]

        author_id = message.author.id
        is_admin = author_id in self._config.whitelist.admin_ids or author_id == self.user.id
        if not is_admin:
            response = await message.channel.send("You do not have permission to use self-bot commands.")
            await self.schedule_ephemeral_cleanup(message, response, delay=5.0)
            return True

        context = CommandContext(
            bot=self,
            message=message,
            args=args,
            config_manager=self._config_manager,
            whitelist=self._whitelist,
            registry=self._command_registry,
            ui=self._ui,
        )

        try:
            handled = await self._command_registry.execute(command_name, context)
        except CommandError as exc:
            response = await context.respond(str(exc))
            await self.schedule_ephemeral_cleanup(message, response, delay=5.0)
            return True

        if not handled:
            response = await message.channel.send(f"Unknown command `{command_name}`. Try `{prefix}help`.")
            await self.schedule_ephemeral_cleanup(message, response, delay=5.0)
            return True

        if self._ui:
            self._ui.increment_commands()
            self._ui.notify_event(
                f"Executed command `{command_name}` for [bold]{escape(message.author.display_name or message.author.name)}[/].",
                icon="🛠",
                style="green",
                force=True,
            )
        return True

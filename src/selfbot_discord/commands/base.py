from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Protocol, Sequence, TYPE_CHECKING

import discord

from selfbot_discord.utils.formatting import TextStyler

if TYPE_CHECKING:
    from selfbot_discord.config.manager import ConfigManager
    from selfbot_discord.core.bot import DiscordSelfBot
    from selfbot_discord.commands.registry import CommandRegistry
    from selfbot_discord.services.whitelist import WhitelistService
    from selfbot_discord.ui.console import ConsoleUI


class CommandError(Exception):
    pass


@dataclass(slots=True)
class CommandContext:
    bot: DiscordSelfBot
    message: discord.Message
    args: list[str]
    config_manager: ConfigManager
    whitelist: WhitelistService
    registry: CommandRegistry
    ui: ConsoleUI | None = None

    @property
    def author(self) -> discord.Member | discord.User:
        return self.message.author

    async def respond(self, content: str, *, delete_after: float | None = None) -> discord.Message:
        if not content or not content.strip():
            content = "⚠️ Empty response"
            
        chunks = TextStyler.chunk_message(content)
        
        if not chunks:
            chunks = ["⚠️ Invalid message format"]
        
        last_response: discord.Message | None = None
        for chunk in chunks:
            last_response = await self.message.channel.send(chunk)
            
        if delete_after is not None and last_response:
            await self.bot.schedule_ephemeral_cleanup(self.message, last_response, delay=delete_after)
            
        if not last_response:
            raise CommandError("Failed to send response")
            
        return last_response


class Command(Protocol):
    name: str
    description: str
    aliases: Sequence[str]

    def bind(self, registry: CommandRegistry) -> None:
        ...

    async def run(self, ctx: CommandContext) -> None:
        ...


@dataclass(slots=True)
class CommandMeta:
    name: str
    description: str
    aliases: Sequence[str]


def command(name: str, *, description: str, aliases: Sequence[str] | None = None) -> Callable[[Callable], Callable]:
    def decorator(func: Callable) -> Callable:
        func.__command_meta__ = CommandMeta(name=name, description=description, aliases=tuple(aliases or ()))  # type: ignore[attr-defined]
        return func

    return decorator


class Cog:
    def __init__(self, bot: "DiscordSelfBot") -> None:
        self.bot = bot

    def iter_commands(self) -> list["BoundCommand"]:
        commands: list[BoundCommand] = []
        for attribute in dir(self):
            value = getattr(self, attribute)
            meta = getattr(value, "__command_meta__", None)
            if meta is None:
                continue
            commands.append(BoundCommand(self, value, meta))
        return commands


class BoundCommand:
    def __init__(self, cog: Cog, func: Callable, meta: CommandMeta) -> None:
        self._cog = cog
        self._func = func
        self.name = meta.name
        self.description = meta.description
        self.aliases = meta.aliases
        self._registry: CommandRegistry | None = None

    def bind(self, registry: CommandRegistry) -> None:
        self._registry = registry

    async def run(self, ctx: CommandContext) -> None:
        await self._func(ctx)

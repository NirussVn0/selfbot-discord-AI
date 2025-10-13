# Command registry responsible for dispatching command handlers.

from __future__ import annotations

from collections import OrderedDict
from typing import Dict, Iterable

from .base import Cog, Command, CommandContext


class CommandRegistry:

    def __init__(self) -> None:
        self._commands: Dict[str, Command] = {}
        self._primary: "OrderedDict[str, Command]" = OrderedDict()

    def register(self, command: Command) -> None:
        key = command.name.lower()
        self._primary[key] = command
        self._commands[key] = command
        for alias in getattr(command, "aliases", []):
            self._commands[alias.lower()] = command
        command.bind(self)

    def register_cog(self, cog: Cog) -> None:
        for command in cog.iter_commands():
            self.register(command)

    def commands(self) -> Iterable[Command]:
        return self._primary.values()

    async def execute(self, name: str, ctx: CommandContext) -> bool:
        command = self._commands.get(name.lower())
        if command is None:
            return False
        await command.run(ctx)
        return True

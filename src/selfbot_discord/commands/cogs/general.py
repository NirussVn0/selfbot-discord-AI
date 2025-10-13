# General command cog for self-bot.

from __future__ import annotations

from pathlib import Path
from typing import Sequence

import json

from selfbot_discord.commands.base import Cog, CommandContext, CommandError, command


class GeneralCog(Cog):
    @command("ping", description="Check if the self-bot is responsive.")
    async def ping(self, ctx: CommandContext) -> None:
        latency_ms = getattr(ctx.bot, "latency", 0.0) * 1000
        await ctx.respond(f"Pong! 🏓 `{latency_ms:.0f} ms`")

    @command("status", description="Display runtime status and uptime information.")
    async def status(self, ctx: CommandContext) -> None:
        bot = ctx.bot
        latency_ms = getattr(bot, "latency", 0.0) * 1000
        uptime_seconds = bot.uptime_seconds
        persona = ctx.config_manager.config.ai.persona
        guilds = len(bot.guilds)
        if bot.user is None:
            raise CommandError("Bot user not ready.")
        user_display = f"{bot.user.name} ({bot.user.id})"
        status_text = (
            "🤖 **Self-Bot Status**\n"
            f"• User: `{user_display}`\n"
            f"• Persona: `{persona}`\n"
            f"• Servers: `{guilds}`\n"
            f"• Latency: `{latency_ms:.0f} ms`\n"
            f"• Uptime: `{bot.format_duration(uptime_seconds)}`"
        )
        await ctx.respond(status_text)

    @command("help", description="Display available commands.")
    async def help(self, ctx: CommandContext) -> None:
        prefix = ctx.config_manager.config.discord.command_prefix
        lines = ["**Available Commands**"]
        for command in ctx.registry.commands():
            lines.append(f"- `{prefix}{command.name}` — {command.description}")
        await ctx.respond("\n".join(lines))

    @command("setting", description="Show the current configuration snapshot.")
    async def setting(self, ctx: CommandContext) -> None:
        config_dict = ctx.config_manager.as_dict()
        payload = json.dumps(config_dict, indent=2, default=str)
        message = await ctx.respond(f"```json\n{payload}\n```")
        await ctx.bot.schedule_ephemeral_cleanup(ctx.message, message, delay=5.0)

    @command("log", description="Show recent log entries.")
    async def log(self, ctx: CommandContext) -> None:
        logging_config = ctx.config_manager.config.logging
        log_dir = logging_config.log_dir or Path("logs")
        log_dir_path = Path(log_dir)
        log_file = log_dir_path / "selfbot.log"
        if not log_file.exists():
            message = await ctx.respond("No log file found.")
            await ctx.bot.schedule_ephemeral_cleanup(ctx.message, message, delay=5.0)
            return

        lines = log_file.read_text(encoding="utf-8").splitlines()
        recent = lines[-10:] if lines else []
        if not recent:
            message = await ctx.respond("Log file is empty.")
            await ctx.bot.schedule_ephemeral_cleanup(ctx.message, message, delay=5.0)
            return

        snippet = "\n".join(recent)
        message = await ctx.respond(f"```text\n{snippet}\n```")
        await ctx.bot.schedule_ephemeral_cleanup(ctx.message, message, delay=5.0)

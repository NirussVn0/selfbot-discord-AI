# General command cog for self-bot.

from __future__ import annotations

from typing import Sequence

import yaml

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
        yaml_dump = yaml.safe_dump(config_dict, sort_keys=False)
        message = await ctx.respond(f"```yaml\n{yaml_dump}\n```")
        await ctx.bot.schedule_ephemeral_cleanup(ctx.message, message, delay=3.0)

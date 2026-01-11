# General command cog for self-bot.

from __future__ import annotations

from pathlib import Path
from typing import Sequence

import asyncio
import json

from selfbot_discord.commands.base import Cog, CommandContext, CommandError, command
from selfbot_discord.services.cleanup import MessageCleaner
from selfbot_discord.services.diagnostics import DiagnosticsService
from selfbot_discord.services.diagnostics import DiagnosticsService


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
        
        user_name = bot.user.name if bot.user else "Unknown"
        user_id = str(bot.user.id) if bot.user else "N/A"
        duration = bot.format_duration(uptime_seconds)

        await ctx.respond(
            f"# 🤖 Hikari Status\n"
            f"**User:** `{user_name}` (`{user_id}`)\n"
            f"**Persona:** `{persona}`\n"
            f"**Uptime:** `{duration}`\n"
            f"**Latency:** `{latency_ms:.0f} ms` | **Servers:** `{guilds}`"
        )

    @command("help", description="Display available commands.")
    async def help(self, ctx: CommandContext) -> None:
        prefix = ctx.config_manager.config.discord.command_prefix
        
        lines = ["# 📜 Available Commands"]
        for cmd in ctx.registry.commands():
            cmd_name = f"{prefix}{cmd.name}"
            desc = cmd.description
            lines.append(f"- `{cmd_name}` : {desc}")
            
        await ctx.respond("\n".join(lines))

    @command("setting", description="View or modify configuration.")
    async def setting(self, ctx: CommandContext) -> None:
        if not ctx.args:
            config_dict = ctx.config_manager.as_dict()
            payload = json.dumps(config_dict, indent=2, default=str)
            message = await ctx.respond(f"```json\n{payload}\n```")
            await ctx.bot.schedule_ephemeral_cleanup(ctx.message, message, delay=5.0)
            return

        # Handle configuration updates
        key = ctx.args[0].lower()
        
        if key in ("selfcmds", "allow_self_commands", "self_commands"):
            # Toggle if no value provided, else set value
            if len(ctx.args) < 2:
                current = ctx.config_manager.config.discord.allow_self_commands
                new_value = not current
            else:
                val_str = ctx.args[1].lower()
                new_value = val_str in ("true", "1", "on", "yes", "enable", "enabled")
            
            # Apply and save
            ctx.config_manager.config.discord.allow_self_commands = new_value
            try:
                ctx.config_manager.save()
                status = "Enabled" if new_value else "Disabled"
                await ctx.respond(f"✅ Self-bot commands **{status}**. Configuration saved.")
            except Exception as e:
                await ctx.respond(f"❌ Failed to save configuration: {e}")
            return

        await ctx.respond(f"❌ Unknown setting key: `{key}`. Currently supported: `selfcmds`")

    @command("log", description="Show recent log entries.")
    async def log(self, ctx: CommandContext) -> None:
        logging_config = ctx.config_manager.config.logging
        log_dir = logging_config.log_dir or Path("logs")
        
        snippet = DiagnosticsService.get_recent_logs(log_dir)
        
        if snippet is None:
             message = await ctx.respond("No log file found.")
             await ctx.bot.schedule_ephemeral_cleanup(ctx.message, message, delay=5.0)
             return
             
        if not snippet:
             message = await ctx.respond("Log file is empty.")
             await ctx.bot.schedule_ephemeral_cleanup(ctx.message, message, delay=5.0)
             return
             
        message = await ctx.respond(f"```log\n{snippet}\n```")
        await ctx.bot.schedule_ephemeral_cleanup(ctx.message, message, delay=15.0)

    @command("clear", description="Clear messages from channel.")
    async def clear(self, ctx: CommandContext) -> None:
        if not ctx.args:
            await ctx.respond("Usage: `clear <amount> [-f] [@user]`")
            return
            
        amount = 0
        target_id: int | None = None
        is_self = False
        
        args = list(ctx.args)
        
        # Parse -f flag
        if "-f" in args:
            is_self = True
            args.remove("-f")

        # Parse valid args
        for arg in args:
            if arg.isdigit():
                amount = int(arg)
            elif arg.startswith("<@") and arg.endswith(">"):
                # Parse mention
                try:
                    target_id = int(arg[2:-1].replace("!", ""))
                except ValueError:
                    pass
        
        if is_self:
            if ctx.bot.user:
                target_id = ctx.bot.user.id
            
        if amount <= 0:
             await ctx.respond("Invalid amount.")
             return
             
        deleted = await MessageCleaner.cleanup_channel(
            ctx.message.channel, 
            amount, 
            target_ids=target_id
        )
            
        await ctx.respond(f"🧹 Cleared {deleted} messages.", delete_after=3.0)

# General command cog for self-bot.

from __future__ import annotations

from pathlib import Path
from typing import Sequence

import asyncio
import json

from selfbot_discord.commands.base import Cog, CommandContext, CommandError, command
from selfbot_discord.services.cleanup import MessageCleaner
from selfbot_discord.services.diagnostics import DiagnosticsService
from selfbot_discord.utils.formatting import TextStyler
from selfbot_discord.services.diagnostics import DiagnosticsService


class GeneralCog(Cog):
    @command("ping", description="Check if the self-bot is responsive.")
    async def ping(self, ctx: CommandContext) -> None:
        latency_ms = getattr(ctx.bot, "latency", 0.0) * 1000
        message = TextStyler.make_embed(
            title="System Latency",
            content=TextStyler.key_value("Gateway", f"{latency_ms:.0f}ms"),
            emoji="🏓"
        )
        await ctx.respond(message)

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



        stats = [
            ("👤 User", f"{user_name}"),
            ("🆔 ID", f"{user_id}"),
            ("🧠 Persona", persona),
            ("⏱️ Uptime", duration),
            ("📡 Latency", f"{latency_ms:.0f} ms"),
            ("🌐 Servers", guilds)
        ]
        
        # Breakdown into lines for cleaner look
        content = ""
        for k, v in stats:
            content += f"{TextStyler.key_value(k, v)}\n"
            
        response = TextStyler.make_embed(
            title="Hikari Status",
            content=content.strip(),
            emoji="🤖",
            footer="System Operational"
        )

        await ctx.respond(response)

    @command("help", description="Display available commands.")
    async def help(self, ctx: CommandContext) -> None:
        prefix = ctx.config_manager.config.discord.command_prefix
        commands = list(ctx.registry.commands())
        
        items_per_page = 10
        total_pages = (len(commands) + items_per_page - 1) // items_per_page
        
        page = 1
        if ctx.args and ctx.args[0].isdigit():
            page = max(1, min(int(ctx.args[0]), total_pages))
        
        start_idx = (page - 1) * items_per_page
        end_idx = start_idx + items_per_page
        page_commands = commands[start_idx:end_idx]
        
        lines = []
        for cmd in page_commands:
            lines.append(f"**{prefix}{cmd.name}** — {cmd.description}")
        
        content = "\n".join(lines)
        footer = f"Page {page}/{total_pages} • {prefix}help [page]"
        
        response = TextStyler.make_embed(
            title="Available Commands",
            content=content,
            emoji="📜",
            footer=footer
        )
        await ctx.respond(response)

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
            p = ctx.config_manager.config.discord.command_prefix
            await ctx.respond(f"Usage: `{p}clear <amount> [-f] [@user]`")
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
             
            
        await ctx.respond(f"🧹 Cleared {deleted} messages.", delete_after=3.0)

    @command("author", description="Show owner's social networks.")
    async def author(self, ctx: CommandContext) -> None:
        socials = [
            "**GitHub**: [NirussVn0](https://github.com/NirussVn0)",
            "**Discord**: `nirussvn0`",
            # Add more as needed
        ]
        await ctx.respond(TextStyler.make_embed("Author Socials", "\n".join(socials), emoji="🌐"))

    @command("changeprefix", description="Change the bot's prefix.")
    async def changeprefix(self, ctx: CommandContext) -> None:
        if not ctx.args:
            p = ctx.config_manager.config.discord.command_prefix
            await ctx.respond(TextStyler.make_embed("Prefix", f"Usage: `{p}changeprefix <new_prefix>`", emoji="⚙️"))
            return
            
        new_prefix = ctx.args[0]
        ctx.config_manager.config.discord.command_prefix = new_prefix
        ctx.config_manager.save()
        await ctx.respond(TextStyler.make_embed("Configuration", f"Prefix changed to `{new_prefix}`", emoji="✅"))

    @command("shutdown", description="Stop the selfbot.")
    async def shutdown(self, ctx: CommandContext) -> None:
        await ctx.respond(TextStyler.make_embed("Shutdown", "Shutting down... 👋", emoji="🛑"))
        await ctx.bot.close()

    @command("uptime", description="Returns how long the selfbot has been running.")
    async def uptime(self, ctx: CommandContext) -> None:
        uptime_seconds = ctx.bot.uptime_seconds
        duration = ctx.bot.format_duration(uptime_seconds)
        await ctx.respond(TextStyler.make_embed("Uptime", f"**Duration**: `{duration}`", emoji="⏱️"))
    
    @command("pingweb", description="Ping a website.")
    async def pingweb(self, ctx: CommandContext) -> None:
        import aiohttp
        if not ctx.args:
            p = ctx.config_manager.config.discord.command_prefix
            await ctx.respond(TextStyler.make_embed("Ping Web", f"Usage: `{p}pingweb <url>`", emoji="🌍"))
            return
            
        url = ctx.args[0]
        if not url.startswith("http"):
            url = f"http://{url}"
            
        try:
            async with aiohttp.ClientSession() as session:
                start = asyncio.get_event_loop().time()
                async with session.get(url, timeout=5) as resp:
                    end = asyncio.get_event_loop().time()
                    lat = (end - start) * 1000
                    status_icon = "✅" if resp.status < 400 else "❌"
                    content = f"**Status**: `{resp.status}`\n**Latency**: `{lat:.0f}ms`"
                    await ctx.respond(TextStyler.make_embed(f"Ping: {url}", content, emoji=status_icon))
        except Exception as e:
            await ctx.respond(TextStyler.make_embed("Error", f"Could not reach {url}", emoji="❌"))

    @command("firstmessage", description="Get the link to the first message in the channel.")
    async def firstmessage(self, ctx: CommandContext) -> None:
        try:
            async for msg in ctx.message.channel.history(limit=1, oldest_first=True):
                await ctx.respond(TextStyler.make_embed("First Message", f"[Jump to first message]({msg.jump_url})", emoji="⏮️"))
                return
            await ctx.respond(TextStyler.make_embed("Error", "No messages found.", emoji="❌"))
        except Exception as e:
            await ctx.respond(TextStyler.make_embed("Error", str(e), emoji="❌"))

    @command("fetchmembers", description="Retrieve list of members (debug).")
    async def fetchmembers(self, ctx: CommandContext) -> None:
        if not ctx.message.guild:
             await ctx.respond(TextStyler.make_embed("Error", "Guild only.", emoji="❌"))
             return
        
        await ctx.message.guild.chunk()
        await ctx.respond(TextStyler.make_embed("Members", f"Fetched members. Total: `{len(ctx.message.guild.members)}`", emoji="👥"))

    @command("guildicon", description="Get the icon of the current server.")
    async def guildicon(self, ctx: CommandContext) -> None:
        if not ctx.message.guild:
             await ctx.respond("Guild only.")
             return
             
        if ctx.message.guild.icon:
            await ctx.respond(ctx.message.guild.icon.url)
        else:
            await ctx.respond("No guild icon.")

    @command("usericon", description="Get profile picture of a user.")
    async def usericon(self, ctx: CommandContext) -> None:
        target = ctx.author
        if ctx.message.mentions:
            target = ctx.message.mentions[0]
            
        if target.avatar:
            await ctx.respond(target.avatar.url)
        else:
            await ctx.respond(target.default_avatar.url)

    @command("guildbanner", description="Get the banner of the current server.")
    async def guildbanner(self, ctx: CommandContext) -> None:
        if not ctx.message.guild:
             await ctx.respond("Guild only.")
             return
             
        if ctx.message.guild.banner:
            await ctx.respond(ctx.message.guild.banner.url)
        else:
            await ctx.respond("No guild banner.")

    @command("guildinfo", description="Get information about the current server.")
    async def guildinfo(self, ctx: CommandContext) -> None:
        g = ctx.message.guild
        if not g:
             await ctx.respond("Guild only.")
             return
             
        info = [
            TextStyler.key_value("Name", g.name, style="bold"),
            TextStyler.key_value("ID", str(g.id)),
            TextStyler.key_value("Owner", str(g.owner)),
            TextStyler.key_value("Members", str(g.member_count)),
            TextStyler.key_value("Roles", str(len(g.roles))),
            TextStyler.key_value("Created", g.created_at.strftime('%Y-%m-%d')),
        ]
        await ctx.respond(TextStyler.make_embed(f"Guild Info", "\n".join(info), emoji="🏰"))

    @command("tokeninfo", description="Scrape info with a token (Simulated).")
    async def tokeninfo(self, ctx: CommandContext) -> None:
        if not ctx.args:
            p = ctx.config_manager.config.discord.command_prefix
            await ctx.respond(TextStyler.make_embed("Token Info", f"Usage: `{p}tokeninfo <token>`", emoji="🕵️"))
            return
            
        token = ctx.args[0]
        try:
            import base64
            parts = token.split('.')
            if len(parts) >= 1:
                id_part = parts[0]
                missing_padding = len(id_part) % 4
                if missing_padding:
                    id_part += '=' * (4 - missing_padding)
                user_id = int(base64.b64decode(id_part).decode('utf-8'))
                await ctx.respond(TextStyler.make_embed("Token Info", f"Token belongs to User ID: `{user_id}`", emoji="🆔"))
                return
        except Exception:
            pass
        await ctx.respond(TextStyler.make_embed("Error", "Invalid token format.", emoji="❌"))

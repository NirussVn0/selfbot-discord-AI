from __future__ import annotations

import discord
from selfbot_discord.commands.base import Cog, CommandContext, command
from selfbot_discord.services.status import StatusService
from selfbot_discord.utils.formatting import TextStyler

class UserCog(Cog):
    def __init__(self, bot: "DiscordSelfBot", status_service: StatusService) -> None:
        super().__init__(bot)
        self.status = status_service

    @command("remoteuser", description="Authorize a user to execute commands remotely.")
    async def remoteuser(self, ctx: CommandContext) -> None:
        if not ctx.message.mentions:
            p = ctx.config_manager.config.discord.command_prefix
            await ctx.respond(TextStyler.make_embed("Remote Access", f"Usage: `{p}remoteuser <@user>`", emoji="🔑"))
            return
            
        target = ctx.message.mentions[0]
        added = ctx.whitelist.add_entries("user_ids", [target.id])
        
        if added:
            await ctx.respond(TextStyler.make_embed("Authorized", f"User {target.mention} can now control the bot.", emoji="✅"))
        else:
            await ctx.respond(TextStyler.make_embed("Already Authorized", f"{target.mention} is already in the whitelist.", emoji="ℹ️"))

    @command("hypesquad", description="Change your HypeSquad badge.")
    async def hypesquad(self, ctx: CommandContext) -> None:
        if not ctx.args:
            p = ctx.config_manager.config.discord.command_prefix
            await ctx.respond(TextStyler.make_embed("HypeSquad", f"Usage: `{p}hypesquad <bravery/brilliance/balance>`", emoji="🛡️"))
            return
            
        house = ctx.args[0]
        result = await self.status.set_hypesquad(house)
        await ctx.respond(TextStyler.make_embed("HypeSquad", result, emoji="🎌"))

    @command("afk", description="Enable or disable AFK mode.")
    async def afk(self, ctx: CommandContext) -> None:
        if not ctx.args:
            p = ctx.config_manager.config.discord.command_prefix
            await ctx.respond(TextStyler.make_embed("AFK Mode", f"Usage: `{p}afk <ON|OFF>`", emoji="💤"))
            return
            
        state = ctx.args[0].upper()
        if state == "ON":
            self.status.set_afk(True)
            msg = ctx.config_manager.config.discord.afk_message
            await ctx.respond(TextStyler.make_embed("AFK Enabled", f"Auto-response set to:\n`{msg}`", emoji="🌙"))
        elif state == "OFF":
            self.status.set_afk(False)
            await ctx.respond(TextStyler.make_embed("AFK Disabled", "Welcome back!", emoji="☀️"))
        else:
            p = ctx.config_manager.config.discord.command_prefix
            await ctx.respond(TextStyler.make_embed("AFK Mode", f"Usage: `{p}afk <ON|OFF>`", emoji="💤"))

    @command("autoreply", description="Enable or disable automatic replies.")
    async def autoreply(self, ctx: CommandContext) -> None:
        if not ctx.args:
            p = ctx.config_manager.config.discord.command_prefix
            await ctx.respond(TextStyler.make_embed("Auto-Reply", f"Usage: `{p}autoreply <ON|OFF>`", emoji="🤖"))
            return
            
        state = ctx.args[0].upper()
        if state == "ON":
            self.status.toggle_autoreply(True)
            await ctx.respond(TextStyler.make_embed("Auto-Reply", "System Enabled.", emoji="✅"))
        elif state == "OFF":
            self.status.toggle_autoreply(False)
            await ctx.respond(TextStyler.make_embed("Auto-Reply", "System Disabled.", emoji="⛔"))
        else:
            p = ctx.config_manager.config.discord.command_prefix
            await ctx.respond(TextStyler.make_embed("Auto-Reply", f"Usage: `{p}autoreply <ON|OFF>`", emoji="🤖"))

    @command("playing", description="Set activity to 'Playing'.")
    async def playing(self, ctx: CommandContext) -> None:
        if not ctx.args:
            p = ctx.config_manager.config.discord.command_prefix
            await ctx.respond(TextStyler.make_embed("Activity", f"Usage: `{p}playing <status>`", emoji="🎮"))
            return
            
        text = " ".join(ctx.args)
        await self.status.set_activity("playing", text)
        await ctx.respond(TextStyler.make_embed("Activity Updated", f"Playing **{text}**", emoji="🎮"))

    @command("watching", description="Set activity to 'Watching'.")
    async def watching(self, ctx: CommandContext) -> None:
        if not ctx.args:
            p = ctx.config_manager.config.discord.command_prefix
            await ctx.respond(TextStyler.make_embed("Activity", f"Usage: `{p}watching <status>`", emoji="📺"))
            return
            
        text = " ".join(ctx.args)
        await self.status.set_activity("watching", text)
        await ctx.respond(TextStyler.make_embed("Activity Updated", f"Watching **{text}**", emoji="📺"))

    @command("stopactivity", description="Clear activity status.")
    async def stopactivity(self, ctx: CommandContext) -> None:
        await self.status.stop_activity()
        await ctx.respond(TextStyler.make_embed("Activity Cleared", "Status reset to default.", emoji="⏹️"))

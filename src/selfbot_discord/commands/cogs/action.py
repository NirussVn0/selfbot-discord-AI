from __future__ import annotations

import asyncio
from selfbot_discord.commands.base import Cog, CommandContext, command
from selfbot_discord.services.action import ActionService
from selfbot_discord.utils.formatting import TextStyler

class ActionCog(Cog):
    def __init__(self, bot: "DiscordSelfBot", service: ActionService) -> None:
        super().__init__(bot)
        self.service = service
        self.copycat_user_id: int | None = None

    @command("whremove", description="Remove a webhook.")
    async def whremove(self, ctx: CommandContext) -> None:
        if not ctx.args:
            p = ctx.config_manager.config.discord.command_prefix
            await ctx.respond(TextStyler.make_embed("Webhook Remover", f"Usage: `{p}whremove <webhook_url>`", emoji="🗑️"))
            return
            
        url = ctx.args[0]
        success = await self.service.delete_webhook(url)
        if success:
            await ctx.respond(TextStyler.make_embed("Success", "Webhook deleted successfully.", emoji="✅"))
        else:
            await ctx.respond(TextStyler.make_embed("Error", "Failed to delete webhook.", emoji="❌"))

    @command("spam", description="Spam a message.")
    async def spam(self, ctx: CommandContext) -> None:
        if len(ctx.args) < 2:
            p = ctx.config_manager.config.discord.command_prefix
            await ctx.respond(TextStyler.make_embed("Spammer", f"Usage: `{p}spam <amount> <message>`", emoji="📨"))
            return
            
        if not ctx.args[0].isdigit():
             await ctx.respond(TextStyler.make_embed("Error", "Amount must be a number.", emoji="❌"))
             return
             
        amount = int(ctx.args[0])
        message = " ".join(ctx.args[1:])
        
        if amount > 50:
            await ctx.respond(TextStyler.make_embed("Warning", "Max spam amount is 50 for safety.", emoji="⚠️"))
            amount = 50
            
        await ctx.message.delete()
        count = await self.service.spam_messages(ctx.message.channel, message, amount)
        # No response to avoid interrupting spam

    @command("dmall", description="DM all members in the server.")
    async def dmall(self, ctx: CommandContext) -> None:
        if not ctx.message.guild:
            await ctx.respond(TextStyler.make_embed("Error", "This command can only be used in a server.", emoji="❌"))
            return
            
        if not ctx.args:
            p = ctx.config_manager.config.discord.command_prefix
            await ctx.respond(TextStyler.make_embed("DM All", f"Usage: `{p}dmall <message>`", emoji="📢"))
            return
            
        message = " ".join(ctx.args)
        await ctx.respond(TextStyler.make_embed("DM All", "🚀 Starting DMall... This may take a while.", emoji="⏳"))
        
        count = await self.service.dm_all_members(ctx.message.guild, message)
        await ctx.respond(TextStyler.make_embed("DM All", f"✅ Finished DMing {count} members.", emoji="📨"))

    @command("sendall", description="Send a message to all channels.")
    async def sendall(self, ctx: CommandContext) -> None:
        if not ctx.message.guild:
            await ctx.respond(TextStyler.make_embed("Error", "This command can only be used in a server.", emoji="❌"))
            return

        if not ctx.args:
            p = ctx.config_manager.config.discord.command_prefix
            await ctx.respond(TextStyler.make_embed("Send All", f"Usage: `{p}sendall <message>`", emoji="📢"))
            return

        message = " ".join(ctx.args)
        count = await self.service.send_to_all_channels(ctx.message.guild, message)
        await ctx.respond(TextStyler.make_embed("Send All", f"✅ Sent to {count} channels.", emoji="📡"))

    @command("guildrename", description="Rename the server.")
    async def guildrename(self, ctx: CommandContext) -> None:
        if not ctx.message.guild:
             await ctx.respond(TextStyler.make_embed("Error", "Server only.", emoji="❌"))
             return
             
        if not ctx.args:
            p = ctx.config_manager.config.discord.command_prefix
            await ctx.respond(TextStyler.make_embed("Rename Guild", f"Usage: `{p}guildrename <name>`", emoji="✏️"))
            return
            
        name = " ".join(ctx.args)
        success = await self.service.rename_guild(ctx.message.guild, name)
        if success:
            await ctx.respond(TextStyler.make_embed("Success", f"Renamed server to **{name}**", emoji="✅"))
        else:
            await ctx.respond(TextStyler.make_embed("Error", "Failed to rename server.", emoji="❌"))

    @command("hidemention", description="Hide message inside another.")
    async def hidemention(self, ctx: CommandContext) -> None:
        content = " ".join(ctx.args)
        if "|" in content:
            visible, hidden = content.split("|", 1)
        else:
            visible = "Hidden Message"
            hidden = content
            
        out = self.service.hide_message(visible.strip(), hidden.strip())
        await ctx.message.delete()
        await ctx.message.channel.send(out)

    @command("edit", description="Send a message and edit it.")
    async def edit(self, ctx: CommandContext) -> None:
        if not ctx.args:
            p = ctx.config_manager.config.discord.command_prefix
            await ctx.respond(TextStyler.make_embed("Edit", f"Usage: `{p}edit <message>`", emoji="✏️"))
            return
            
        text = " ".join(ctx.args)
        msg = await ctx.message.channel.send(text)
        await asyncio.sleep(1)
        await msg.edit(content=text + "\u200b")

    @command("quickdelete", description="Send a message and delete it immediately.")
    async def quickdelete(self, ctx: CommandContext) -> None:
        if not ctx.args:
            p = ctx.config_manager.config.discord.command_prefix
            await ctx.respond(TextStyler.make_embed("Quick Delete", f"Usage: `{p}quickdelete <message>`", emoji="👻"))
            return
        
        text = " ".join(ctx.args)
        await ctx.message.delete()
        await self.service.quick_delete(ctx.message.channel, text)

    @command("cleardm", description="Delete DMs with a user.")
    async def cleardm(self, ctx: CommandContext) -> None:
        amount = 100
        target_user = None
        
        if ctx.args:
            if ctx.args[0].isdigit():
                amount = int(ctx.args[0])
            
            if ctx.message.mentions:
                target_user = ctx.message.mentions[0]

        if isinstance(ctx.message.channel, discord.DMChannel) and not target_user:
            deleted = await self.service.clear_dm_context_aware(ctx.message.channel, amount, ctx.bot.user.id)
            await ctx.respond(TextStyler.make_embed("Cleaned", f"Removed {deleted} messages.", emoji="🧹"), delete_after=3)
            return

        if target_user:
             deleted = await self.service.clear_dm(target_user, amount)
             await ctx.respond(TextStyler.make_embed("Cleaned", f"Removed {deleted} messages with {target_user.name}.", emoji="🧹"), delete_after=3)
             return
             
        p = ctx.config_manager.config.discord.command_prefix
        await ctx.respond(TextStyler.make_embed("Clear DM", f"Usage: `{p}cleardm [amount] [@user]`", emoji="🧹"))

    @command("copycat", description="Mimic a user's messages.")
    async def copycat(self, ctx: CommandContext) -> None:
        if not ctx.args:
             p = ctx.config_manager.config.discord.command_prefix
             await ctx.respond(TextStyler.make_embed("Copycat", f"Usage: `{p}copycat ON|OFF <@user>`", emoji="🎭"))
             return
             
        action = ctx.args[0].upper()
        if action == "OFF":
            self.copycat_user_id = None
            await ctx.respond(TextStyler.make_embed("Copycat", "Disabled.", emoji="🛑"))
            return
            
        if action == "ON":
            if not ctx.message.mentions:
                 await ctx.respond(TextStyler.make_embed("Copycat", "Mention a user to copy.", emoji="🎭"))
                 return
            target = ctx.message.mentions[0]
            self.copycat_user_id = target.id
            await ctx.respond(TextStyler.make_embed("Copycat", f"Now copying **{target.name}**.", emoji="👯"))
            return
            
        p = ctx.config_manager.config.discord.command_prefix
        await ctx.respond(TextStyler.make_embed("Copycat", f"Usage: `{p}copycat ON|OFF <@user>`", emoji="🎭"))
        
    @command("purge", description="Purge messages (alias to clear).")
    async def purge(self, ctx: CommandContext) -> None:
        if not ctx.args:
            p = ctx.config_manager.config.discord.command_prefix
            await ctx.respond(TextStyler.make_embed("Purge", f"Usage: `{p}purge <amount>`", emoji="🧹"))
            return
        
        if not ctx.args[0].isdigit():
            await ctx.respond(TextStyler.make_embed("Error", "Invalid amount.", emoji="❌"))
            return
            
        amount = int(ctx.args[0])
        from selfbot_discord.services.cleanup import MessageCleaner
        deleted = await MessageCleaner.cleanup_channel(ctx.message.channel, amount)
        await ctx.respond(TextStyler.make_embed("Purged", f"Deleted {deleted} messages.", emoji="🗑️"), delete_after=3)

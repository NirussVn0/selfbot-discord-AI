from __future__ import annotations

import discord
from selfbot_discord.commands.base import Cog, CommandContext, command
from selfbot_discord.services.utility import UtilityService
from selfbot_discord.utils.formatting import TextStyler

class UtilityCog(Cog):
    def __init__(self, bot: "DiscordSelfBot", service: UtilityService) -> None:
        super().__init__(bot)
        self.service = service

    @command("geoip", description="Looks up the IP's location.")
    async def geoip(self, ctx: CommandContext) -> None:
        if not ctx.args:
            p = ctx.config_manager.config.discord.command_prefix
            await ctx.respond(TextStyler.make_embed("GeoIP", f"Usage: `{p}geoip <ip>`", emoji="🌍"))
            return
            
        ip = ctx.args[0]
        data = self.service.get_geoip(ip)
        
        if not data:
            await ctx.respond("❌ Could not fetch data for that IP.")
            return
            
        content = "\n".join([
            TextStyler.key_value("Country", data.get('country', 'N/A')),
            TextStyler.key_value("Region", data.get('regionName', 'N/A')),
            TextStyler.key_value("City", data.get('city', 'N/A')),
            TextStyler.key_value("ISP", data.get('isp', 'N/A')),
            TextStyler.key_value("Timezone", data.get('timezone', 'N/A')),
        ])
        
        embed = TextStyler.make_embed(
            title=f"GeoIP: {ip}",
            content=content,
            emoji="🌍"
        )
        await ctx.respond(embed)

    @command("tts", description="Converts text to speech.")
    async def tts(self, ctx: CommandContext) -> None:
        if not ctx.args:
            p = ctx.config_manager.config.discord.command_prefix
            await ctx.respond(TextStyler.make_embed("TTS", f"Usage: `{p}tts <text>`", emoji="🗣️"))
            return
            
        text = " ".join(ctx.args)
        fp = self.service.generate_tts(text)
        await ctx.message.channel.send(file=discord.File(fp, filename="tts.mp3"))

    @command("qr", description="Generate a QR code.")
    async def qr(self, ctx: CommandContext) -> None:
        if not ctx.args:
            p = ctx.config_manager.config.discord.command_prefix
            await ctx.respond(TextStyler.make_embed("QR Generator", f"Usage: `{p}qr <text>`", emoji="📱"))
            return
            
        text = " ".join(ctx.args)
        fp = self.service.generate_qr(text)
        await ctx.message.channel.send(file=discord.File(fp, filename="qr.png"))

    @command("gentoken", description="Generate an invalid but correctly patterned token.")
    async def gentoken(self, ctx: CommandContext) -> None:
        # No arg usage needed really, but consistent styling applied previously
        token = self.service.generate_token()
        await ctx.respond(TextStyler.make_embed("Fake Token", f"||{token}||", emoji="🪙"))

    @command("nitro", description="Generate a fake Nitro code.")
    async def nitro(self, ctx: CommandContext) -> None:
        code = self.service.generate_nitro()
        await ctx.respond(TextStyler.make_embed("Nitro Gift", f"{code}", emoji="🎁"))

    @command("ascii", description="Convert a message to ASCII art.")
    async def ascii(self, ctx: CommandContext) -> None:
        if not ctx.args:
            p = ctx.config_manager.config.discord.command_prefix
            await ctx.respond(TextStyler.make_embed("ASCII Art", f"Usage: `{p}ascii <text>`", emoji="🎨"))
            return
        
        text = " ".join(ctx.args)
        art = self.service.ascii_art(text)
        if len(art) > 1990:
            await ctx.respond(TextStyler.make_embed("Error", "Text too long for ASCII art.", emoji="❌"))
        else:
            await ctx.respond(f"```\n{art}\n```")

    @command("leetpeek", description="Speak like a hacker.")
    async def leetpeek(self, ctx: CommandContext) -> None:
        if not ctx.args:
            p = ctx.config_manager.config.discord.command_prefix
            await ctx.respond(TextStyler.make_embed("Leet Speak", f"Usage: `{p}leetpeek <text>`", emoji="👾"))
            return
            
        text = " ".join(ctx.args)
        leet = self.service.leet_speak(text)
        await ctx.respond(TextStyler.make_embed("Leet Output", leet, emoji="💻"))

    @command("reverse", description="Reverse the letters of a message.")
    async def reverse(self, ctx: CommandContext) -> None:
        if not ctx.args:
            p = ctx.config_manager.config.discord.command_prefix
            await ctx.respond(TextStyler.make_embed("Reverse", f"Usage: `{p}reverse <text>`", emoji="🔄"))
            return
        
        text = " ".join(ctx.args)
        rev = self.service.reverse_text(text)
        await ctx.respond(TextStyler.make_embed("Reversed", rev, emoji="↩️"))

    @command("minesweeper", description="Play a game of Minesweeper.")
    async def minesweeper(self, ctx: CommandContext) -> None:
        width = 8
        height = 8
        
        if len(ctx.args) >= 1 and ctx.args[0].isdigit():
            width = int(ctx.args[0])
        if len(ctx.args) >= 2 and ctx.args[1].isdigit():
            height = int(ctx.args[1])

            
        game = self.service.generate_minesweeper(width, height, bombs=int(width*height*0.15))
        await ctx.respond(TextStyler.make_embed("Minesweeper", f"\n{game}", emoji="💣"))

    @command("dick", description="Show the 'size' of a user's dick.")
    async def dick(self, ctx: CommandContext) -> None:
        target = ctx.author
        if ctx.message.mentions:
            target = ctx.message.mentions[0]
            
        size = self.service.get_dick_size(target.id)
        visual = "=" * size
        await ctx.respond(TextStyler.make_embed("Size Scanner", f"{target.display_name}'s is:\n8{visual}D ({size}cm)", emoji="📏"))

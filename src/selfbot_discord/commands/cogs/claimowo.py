from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING

from selfbot_discord.commands.base import Cog, CommandContext, CommandError, command
from selfbot_discord.services.owo import OWOGameService, OWOStatsTracker

if TYPE_CHECKING:
    from discord import Message

logger = logging.getLogger(__name__)


class ClaimOWOCog(Cog):
    def __init__(self, bot, game_service: OWOGameService, stats_tracker: OWOStatsTracker) -> None:
        super().__init__(bot)
        self.game_service = game_service
        self.stats_tracker = stats_tracker
        self._game_task: asyncio.Task | None = None

    @command("claimowo", description="Manage OWO coin flip automation", aliases=["cowo"])
    async def claimowo(self, ctx: CommandContext) -> None:
        if not ctx.args:
            await ctx.respond(
                "**ClaimOWO Usage:**\n"
                f"• `{ctx.bot._config.discord.command_prefix}claimowo <amount>` - Start betting with base amount\n"
                f"• `{ctx.bot._config.discord.command_prefix}claimowo stop` - Stop current session\n"
                f"• `{ctx.bot._config.discord.command_prefix}claimowo info` - View statistics"
            )
            return

        subcommand = ctx.args[0].lower()

        if subcommand == "stop":
            await self._handle_stop(ctx)
        elif subcommand == "info":
            await self._handle_info(ctx)
        else:
            try:
                amount = int(subcommand)
                await self._handle_start(ctx, amount)
            except ValueError:
                raise CommandError(f"Invalid amount: `{subcommand}`. Use a number, 'stop', or 'info'.")

    async def _handle_start(self, ctx: CommandContext, amount: int) -> None:
        if amount <= 0:
            raise CommandError("Bet amount must be greater than 0.")

        if self.game_service.state.name == "RUNNING":
            raise CommandError("A game is already running. Use `stop` to end it first.")

        self.game_service.start_game(ctx.message.channel, amount)

        response = await ctx.respond(
            f"🎰 **ClaimOWO Started!**\n"
            f"• Base Bet: `{amount}` cowoncy\n"
            f"• Multiplier: `3x` on loss\n"
            f"• Status: `Running`\n\n"
            f"Use `{ctx.bot._config.discord.command_prefix}claimowo stop` to stop."
        )
        await ctx.bot.schedule_ephemeral_cleanup(ctx.message, response, delay=10.0)

        self._game_task = asyncio.create_task(self.game_service.run_game_loop())

        if ctx.ui:
            ctx.ui.notify_event(
                f"ClaimOWO started with base bet {amount} cowoncy",
                icon="🎰",
                style="green",
                force=True,
            )

    async def _handle_stop(self, ctx: CommandContext) -> None:
        if self.game_service.state.name != "RUNNING":
            raise CommandError("No game is currently running.")

        self.game_service.stop_game()

        if self._game_task and not self._game_task.done():
            self._game_task.cancel()
            try:
                await self._game_task
            except asyncio.CancelledError:
                pass

        stats = self.stats_tracker.get_stats()
        response = await ctx.respond(
            f"🛑 **ClaimOWO Stopped**\n"
            f"• Games Played: `{stats.total_games}`\n"
            f"• Wins: `{stats.total_wins}` | Losses: `{stats.total_losses}`\n"
            f"• Net Profit: `{stats.net_profit:+,}` cowoncy"
        )
        await ctx.bot.schedule_ephemeral_cleanup(ctx.message, response, delay=10.0)

        if ctx.ui:
            ctx.ui.notify_event(
                "ClaimOWO stopped by user",
                icon="🛑",
                style="yellow",
                force=True,
            )

    async def _handle_info(self, ctx: CommandContext) -> None:
        stats = self.stats_tracker.get_stats()

        if stats.total_games == 0:
            response = await ctx.respond("📊 No games played yet. Start with `claimowo <amount>`.")
            await ctx.bot.schedule_ephemeral_cleanup(ctx.message, response, delay=5.0)
            return

        info_text = self._format_stats(stats)
        response = await ctx.respond(info_text)
        await ctx.bot.schedule_ephemeral_cleanup(ctx.message, response, delay=15.0)

    def _format_stats(self, stats) -> str:
        session_duration = "N/A"
        if stats.session_start and stats.session_end:
            duration = stats.session_end - stats.session_start
            session_duration = str(duration).split(".")[0]

        return (
            "📊 **ClaimOWO Statistics**\n\n"
            f"**Session Info**\n"
            f"• Games Played: `{stats.total_games}`\n"
            f"• Session Duration: `{session_duration}`\n\n"
            f"**Win/Loss Ratio**\n"
            f"• Wins: `{stats.total_wins}` ({stats.win_rate:.1f}%)\n"
            f"• Losses: `{stats.total_losses}` ({stats.loss_rate:.1f}%)\n"
            f"• Current Loss Streak: `{stats.current_loss_streak}`\n"
            f"• Highest Loss Streak: `{stats.highest_loss_streak}`\n\n"
            f"**Financial Summary**\n"
            f"• Total Won: `{stats.total_money_won:,}` cowoncy\n"
            f"• Total Lost: `{stats.total_money_lost:,}` cowoncy\n"
            f"• Net Profit: `{stats.net_profit:+,}` cowoncy\n"
            f"• Highest Win: `{stats.highest_win:,}` cowoncy"
        )

    async def process_owo_message(self, message: Message) -> None:
        if message.author.id != 408785106942164992:
            return

        if self.game_service.channel is None:
            return

        if message.channel.id != self.game_service.channel.id:
            return

        await self.game_service.process_result(message)
        await self.game_service.update_balance(message)

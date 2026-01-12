from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from typing import TYPE_CHECKING

from selfbot_discord.commands.base import Cog, CommandContext, CommandError, command
from selfbot_discord.services.owo import OWOGameService, OWOStatsTracker, MultiplierMode, BettingSide
from selfbot_discord.services.owo.presenter import OWOStatsPresenter
from selfbot_discord.services.owo.cli import OWOArgParser, OWOUsageError
from selfbot_discord.services.owo.settings import OWOSettingsManager, OWOGameConfig
from selfbot_discord.services.cleanup import MessageCleaner

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
        try:
            result = OWOArgParser.parse(ctx.args)
        except OWOUsageError as e:
            await ctx.respond(f"❌ {e}")
            await self._show_usage(ctx)
            return

        if result.action == "usage":
            await self._show_usage(ctx)
            return

        if result.action == "stop":
            await self._handle_stop(ctx)
            return

        if result.action == "info":
            await self._handle_info(ctx)
            return

        if result.action == "reset":
            await self._handle_reset(ctx)
            return

        if result.action == "clear":
            await self._handle_cleanup(ctx)
            return

        # Start Logic with Persistence
        if result.action == "start":
            params = result.start_params
            
            # Case 1: Params provided -> Use them & Save
            if params:
                config = OWOGameConfig(
                    amount=params.amount,
                    multiplier_mode=params.multiplier_mode,
                    static_multiplier=params.static_multiplier,
                    betting_side=params.betting_side
                )
                OWOSettingsManager.save(config)
            
            # Case 2: No params -> Try to Load
            else:
                config = OWOSettingsManager.load()
                if not config:
                    await ctx.respond("❌ No saved settings found. Please provide arguments first:\n`h!claimowo -b <amount>`")
                    return
            
            await self._handle_start(ctx, config)


    async def _show_usage(self, ctx: CommandContext) -> None:
        p = ctx.bot._config.discord.command_prefix
        await ctx.respond(
            f"# 🛠️ ClaimOWO Usage\n"
            f"**Start (New)**: `{p}claimowo -b <bet> [flags]`\n"
            f"**Start (Saved)**: `{p}claimowo`\n"
            f"**Stop**: `{p}claimowo -s`\n"
            f"**Info**: `{p}claimowo -i`\n"
            f"**Reset**: `{p}claimowo -reset`\n\n"
            f"### Flags\n"
            f"`-b <amt>` : Base bet amount\n"
            f"`-side <h/t/r>` : Side (`heads`, `tails`, `random`)\n"
            f"`-e <mode>` : Betting Strategy\n"
            f"> `maintain` : Aggressive. Keeps high bet on win streak. Drops 2 steps on break.\n"
            f"> `safe` : Conservative. Drops 2 steps if loss streak > 5.\n"
            f"> `random` : Subtly decays multiplier (x2.0 -> x1.5) as streak grows.\n"
            f"> `x2` : Standard Martingale.\n"
            f"`-clear` : Cleanup game messages"
        )

    async def _handle_start(self, ctx: CommandContext, config: OWOGameConfig) -> None:
        amount = config.amount
        
        if amount <= 0:
            raise CommandError("Bet amount must be greater than 0.")

        if self._game_task and not self._game_task.done():
            raise CommandError("A game is already running. Use `-s` to stop it first.")

        self.game_service.start_game(
            ctx.message.channel,
            amount,
            multiplier_mode=config.multiplier_mode,
            static_multiplier=config.static_multiplier,
            betting_side=config.betting_side
        )
        
        if config.multiplier_mode == MultiplierMode.AUTO:
            mode_str = "Auto"
        elif config.multiplier_mode == MultiplierMode.STATIC:
            mode_str = f"Static {config.static_multiplier}x"
        else:
            mode_str = f"{config.multiplier_mode.name.title()} {config.static_multiplier}x"
        side_str = config.betting_side.name.title()
        fmt_amount = f"{amount:,}"

        response = await ctx.respond(
            f"# 🎰 ClaimOWO Started\n"
            f"> **Strategy**: `{mode_str}`\n"
            f"> **Side**: `{side_str}`\n"
            f"> **Base Bet**: `{fmt_amount}` cowoncy\n"
            f"> **Status**: `Running`\n\n"
            f"Use `{ctx.bot._config.discord.command_prefix}claimowo -s` to stop."
        )
        await ctx.bot.schedule_ephemeral_cleanup(ctx.message, response, delay=10.0)

        self._game_task = asyncio.create_task(self.game_service.run_game_loop())

        if ctx.ui:
            ctx.ui.notify_event(
                f"ClaimOWO started: {amount} ({mode_str}, {side_str})",
                icon="🎰",
                style="green",
                force=True,
            )

    async def _handle_stop(self, ctx: CommandContext) -> None:
        if not self._game_task or self._game_task.done():
            raise CommandError("No game is currently running.")

        self.game_service.stop_game()

        if self._game_task and not self._game_task.done():
            self._game_task.cancel()
            try:
                await self._game_task
            except asyncio.CancelledError:
                pass

        stats = self.stats_tracker.get_stats()
        
        profit = f"{stats.net_profit:+,}"
        
        response = await ctx.respond(
            f"# 🛑 Session Stopped\n"
            f"**Games Played**: `{stats.total_games}`\n"
            f"**Win/Loss**: `{stats.total_wins}` / `{stats.total_losses}`\n"
            f"**Net Profit**: `{profit}` cowoncy"
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
        info_text = OWOStatsPresenter.format_stats(
            stats, 
            self.game_service.strategy, 
            self.game_service.state
        )
        response = await ctx.respond(info_text)
        await ctx.bot.schedule_ephemeral_cleanup(ctx.message, response, delay=15.0)

    async def _handle_reset(self, ctx: CommandContext) -> None:
        self.stats_tracker.reset_stats()
        response = await ctx.respond("✅ **Statistics have been reset.**")
        await ctx.bot.schedule_ephemeral_cleanup(ctx.message, response, delay=5.0)

    async def _handle_cleanup(self, ctx: CommandContext) -> None:
        """Clear recent messages from self and OWO bot."""
        targets = [ctx.bot.user.id, 408785106942164992]
        deleted = await MessageCleaner.cleanup_channel(ctx.message.channel, 50, target_ids=targets)
        await ctx.respond(f"🧹 Cleared {deleted} messages.", delete_after=3.0)




    async def process_owo_message(self, message: Message) -> None:
        if message.author.id != 408785106942164992:
            return

        if self.game_service.channel is None:
            return

        if message.channel.id != self.game_service.channel.id:
            return

        logger.info("Received OWO message: %r", message.content)
        await self.game_service.process_result(message)
        await self.game_service.update_balance(message)

from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from typing import TYPE_CHECKING

from selfbot_discord.commands.base import Cog, CommandContext, CommandError, command
from selfbot_discord.services.owo import OWOGameService, OWOStatsTracker, MultiplierMode, BettingSide
from selfbot_discord.services.owo.presenter import OWOStatsPresenter

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
            await self._show_usage(ctx)
            return

        # Check for legacy commands (no flags) vs new format
        args = ctx.args
        is_new_format = any(arg.startswith("-") for arg in args)

        if not is_new_format:
            # Legacy basic format: [amount] or [subcommand]
            subcommand = args[0].lower()
            if subcommand in ("stop", "s"):
                await self._handle_stop(ctx)
            elif subcommand in ("info", "i"):
                await self._handle_info(ctx)
            else:
                try:
                    amount = int(subcommand)
                    await self._handle_start(ctx, amount)
                except ValueError:
                    await self._show_usage(ctx)
            return

        # New format parsing
        base_bet: int | None = None
        multiplier_mode = MultiplierMode.STATIC
        base_bet: int | None = None
        multiplier_mode = MultiplierMode.STATIC
        static_multiplier: float = 3.0
        betting_side = BettingSide.RANDOM
        
        # Iteration for flags
        i = 0
        while i < len(args):
            arg = args[i].lower()
            
            if arg in ("-s", "-stop", "stop"):
                return await self._handle_stop(ctx)
                
            elif arg in ("-i", "-info", "info"):
                return await self._handle_info(ctx)
                
            elif arg in ("-clear", "--clear"):
                return await self._handle_cleanup(ctx)

            elif arg in ("-reset", "--reset"):
                return await self._handle_reset(ctx)
                
            elif arg in ("-b", "-bet"):
                if i + 1 >= len(args):
                    raise CommandError("Missing amount for `-b` flag.")
                try:
                    base_bet = int(args[i+1])
                    i += 1
                except ValueError:
                    raise CommandError(f"Invalid bet amount: {args[i+1]}")
                    
            elif arg in ("-e", "-mode"):
                if i + 1 >= len(args):
                    raise CommandError("Missing value for `-e` flag.")
                val = args[i+1].lower()
                i += 1
                
                if val == "auto":
                    multiplier_mode = MultiplierMode.AUTO
                elif val.startswith("x") or val.replace(".", "", 1).isdigit():
                    multiplier_mode = MultiplierMode.STATIC
                    # Remove 'x' prefix if present
                    mult_str = val[1:] if val.startswith("x") else val
                    try:
                        static_multiplier = float(mult_str)
                    except ValueError:
                        raise CommandError(f"Invalid multiplier: {val}")
                else:
                    raise CommandError(f"Invalid mode: {val}. Use 'auto', 'x2', 'x3', etc.")

            elif arg in ("-side", "--side", "-sd"):
                if i + 1 >= len(args):
                    raise CommandError("Missing value for `-side` flag.")
                val = args[i+1].lower()
                i += 1

                if val in ("h", "head", "heads"):
                    betting_side = BettingSide.HEADS
                elif val in ("t", "tail", "tails"):
                    betting_side = BettingSide.TAILS
                elif val in ("r", "rand", "random"):
                     betting_side = BettingSide.RANDOM
                else:
                     raise CommandError(f"Invalid side: {val}. Use h, t, or r.")
            else:
                # Ignore unknown flags or positional args
                pass
            
            i += 1

        if base_bet is not None:
            await self._handle_start(ctx, base_bet, multiplier_mode, static_multiplier, betting_side)
        else:
            await self._show_usage(ctx)

    async def _show_usage(self, ctx: CommandContext) -> None:
        p = ctx.bot._config.discord.command_prefix
        await ctx.respond(
            f"# 🛠️ ClaimOWO Usage\n"
            f"**Start**: `{p}claimowo -b <bet> [flags]`\n"
            f"**Stop**: `{p}claimowo -s`\n"
            f"**Info**: `{p}claimowo -i`\n"
            f"**Reset**: `{p}claimowo -reset`\n\n"
            f"### Flags\n"
            f"`-b <amt>` : Base bet amount\n"
            f"`-e <data> ` : Multiplier (`auto`, `x2`, `x3`)\n"
            f"`-side <h/t/r>` : Side (`heads`, `tails`, `random`)\n"
            f"`-clear` : Cleanup game messages"
        )

    async def _handle_start(
        self,
        ctx: CommandContext,
        amount: int,
        multiplier_mode: MultiplierMode = MultiplierMode.STATIC,
        static_multiplier: float = 3.0,
        betting_side: BettingSide = BettingSide.RANDOM
    ) -> None:
        if amount <= 0:
            raise CommandError("Bet amount must be greater than 0.")

        if self._game_task and not self._game_task.done():
            raise CommandError("A game is already running. Use `-s` to stop it first.")

        self.game_service.start_game(
            ctx.message.channel,
            amount,
            multiplier_mode=multiplier_mode,
            static_multiplier=static_multiplier,
            betting_side=betting_side
        )
        
        mode_str = "Auto" if multiplier_mode == MultiplierMode.AUTO else f"Static {static_multiplier}x"
        side_str = betting_side.name.title()
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
        # Simple implementation: purge last 100 messages if author is self or OWO
        channel = ctx.message.channel
        deleted = 0
        try:
            # Note: history() returns an async iterator
            async for msg in channel.history(limit=50):
                if msg.author == ctx.bot.user or msg.author.id == 408785106942164992:
                    try:
                        await msg.delete()
                        deleted += 1
                        await asyncio.sleep(0.5) # Rate limit protection
                    except Exception:
                        pass
        except Exception as e:
            logger.error(f"Failed to cleanup messages: {e}")
            
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

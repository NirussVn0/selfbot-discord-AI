from __future__ import annotations

import asyncio
import logging
import random
from typing import TYPE_CHECKING

from selfbot_discord.services.owo.models import (
    BetResult,
    BettingSide,
    MartingaleStrategy,
    StrategyFlag,
    OWOBet,
    OWOGameState,
)
from selfbot_discord.services.owo.parser import OWOMessageParser
from selfbot_discord.services.owo.stats_tracker import OWOStatsTracker

if TYPE_CHECKING:
    import discord

logger = logging.getLogger(__name__)


class OWOGameService:
    def __init__(
        self,
        stats_tracker: OWOStatsTracker,
        cooldown_seconds: int = 10,
        retry_delay_seconds: float = 1.5,
        max_retries: int = 3,
    ) -> None:
        self.stats_tracker = stats_tracker
        self.cooldown_seconds = cooldown_seconds
        self.retry_delay_seconds = retry_delay_seconds
        self.max_retries = max_retries

        self.state = OWOGameState.IDLE
        self.strategy: MartingaleStrategy | None = None
        self.channel: discord.TextChannel | None = None
        self.current_balance: int = 0
        self._pending_bet: OWOBet | None = None
        self._stop_requested = False
        self._result_received = asyncio.Event()
        self._cooldown_retry_needed = False

    def start_game(
        self,
        channel: discord.TextChannel,
        initial_bet: int,
        active_flags: set[StrategyFlag] | None = None,
        static_multiplier: float = 3.0,
        betting_side: BettingSide = BettingSide.RANDOM,
    ) -> None:
        if self.state == OWOGameState.RUNNING:
            msg = "Game is already running"
            raise RuntimeError(msg)

        if active_flags is None:
            active_flags = set()

        self.channel = channel
        self.strategy = MartingaleStrategy(
            base_bet=initial_bet,
            current_bet=initial_bet,
            active_flags=active_flags,
            static_multiplier=static_multiplier,
            betting_side=betting_side,
        )
        self.state = OWOGameState.RUNNING
        self._stop_requested = False
        self._cooldown_retry_needed = False
        self.stats_tracker.start_session()
        
        mode_str = ", ".join(f.name for f in active_flags) if active_flags else "STATIC"
        
        logger.info(
            "Started OWO game [bet=%d, mode=%s, mult=%.1f] in channel %s",
            initial_bet,
            mode_str,
            static_multiplier,
            channel.id
        )

    def stop_game(self) -> None:
        self._stop_requested = True
        self.state = OWOGameState.STOPPED
        self.stats_tracker.end_session()
        logger.info("OWO game stopped by user request")

    async def place_bet(self) -> bool:
        if self.state != OWOGameState.RUNNING or self._stop_requested:
            return False

        if self.channel is None or self.strategy is None:
            return False

        bet_amount = self.strategy.current_bet

        if bet_amount > self.current_balance and self.current_balance > 0:
            logger.warning("Insufficient balance (%d) for bet (%d)", self.current_balance, bet_amount)
            self.stop_game()
            return False

        self._pending_bet = OWOBet(amount=bet_amount, result=BetResult.PENDING)
        
        # Determine side based on strategy
        side = self.strategy.get_next_side()

        for attempt in range(self.max_retries):
            try:
                # Add a small random delay before typing (0.5 - 1.5s) to simulate human
                await asyncio.sleep(random.uniform(0.5, 1.5))
                
                await self.channel.send(f"owocf {bet_amount} {side}")
                logger.info("Placed bet of %d on %s (attempt %d/%d)", bet_amount, side, attempt + 1, self.max_retries)
                self.state = OWOGameState.COOLDOWN
                return True
            except Exception as exc:
                logger.exception("Failed to place bet (attempt %d/%d): %s", attempt + 1, self.max_retries, exc)
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay_seconds)

        logger.error("Failed to place bet after %d attempts", self.max_retries)
        self._pending_bet = None
        return False

    async def process_result(self, message: discord.Message) -> bool:
        if self._pending_bet is None:
            return False

        parse_result = OWOMessageParser.parse_coinflip_result(message)

        if not parse_result.is_owo_response:
            return False

        if parse_result.is_captcha:
            logger.critical("⚠️ CAPTCHA/VERIFICATION DETECTED! Stopping automation immediately for safety.")
            self.stop_game()
            self._result_received.set()
            return True

        if parse_result.is_cooldown:
            logger.warning("⏱️ Cooldown detected! Will retry in ~5s...")
            self._cooldown_retry_needed = True
            self._result_received.set()
            return False

        # Reset flag on valid response
        self._cooldown_retry_needed = False

        if parse_result.is_win:
            self._pending_bet.result = BetResult.WIN
            self._pending_bet.won_amount = parse_result.won_amount
            self.stats_tracker.record_bet(self._pending_bet)
            self.strategy.on_win()
            logger.info("Won %d cowoncy! Resetting to base bet.", parse_result.won_amount)
            self._pending_bet = None
            self.state = OWOGameState.RUNNING
            self._result_received.set()
            return True

        if parse_result.is_loss:
            self._pending_bet.result = BetResult.LOSS
            self.stats_tracker.record_bet(self._pending_bet)
            self.strategy.on_loss()
            logger.info("Lost bet. Next bet will be %d", self.strategy.current_bet)
            self._pending_bet = None
            self.state = OWOGameState.RUNNING
            self._result_received.set()
            return True

        return False

    async def update_balance(self, message: discord.Message) -> None:
        parse_result = OWOMessageParser.parse_balance(message)
        if parse_result.is_owo_response and parse_result.balance > 0:
            self.current_balance = parse_result.balance
            logger.info("Updated balance: %d cowoncy", self.current_balance)

    async def run_game_loop(self) -> None:
        if self.channel is None:
            return

        await self.channel.send("owocash")
        await asyncio.sleep(2)

        while (not self._stop_requested) and (self.state == OWOGameState.RUNNING or self.state == OWOGameState.COOLDOWN):
            bet_amount = self.strategy.current_bet if self.strategy else 0
            
            if bet_amount > self.current_balance and self.current_balance > 0:
                logger.warning("Insufficient balance (%d) for bet (%d). Stopping game.", self.current_balance, bet_amount)
                self.stop_game()
                break

            self._result_received.clear()
            self._cooldown_retry_needed = False # Reset before new round
            self.state = OWOGameState.RUNNING  # Ensure we are in running state before placing bet
            
            if not await self.place_bet():
                break

            try:
                await asyncio.wait_for(self._result_received.wait(), timeout=15.0)
            except asyncio.TimeoutError:
                logger.warning("Timeout waiting for OWO response, retrying...")
                self._pending_bet = None
                self.state = OWOGameState.RUNNING
                continue

            # Sleep Logic:
            await self._wait_for_next_round()

        logger.info("Game loop ended")

    async def _wait_for_next_round(self) -> None:
        """Determines shuffle/sleep time based on context (cooldown vs normal)."""
        if self._cooldown_retry_needed:
            # Quick retry for rate limits
            sleep_time = random.uniform(4.0, 6.0)
            logger.info("Cooldown retry wait: %.2fs", sleep_time)
        else:
            # Standard human-like delay
            sleep_time = 10.0 + random.uniform(0.0, 5.0)
            logger.info("Std round wait: %.2fs", sleep_time)
            
        await asyncio.sleep(sleep_time)

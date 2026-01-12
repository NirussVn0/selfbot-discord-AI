from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
import random
from typing import Literal


class OWOGameState(Enum):
    IDLE = auto()
    RUNNING = auto()
    COOLDOWN = auto()
    STOPPED = auto()


class BetResult(Enum):
    WIN = auto()
    LOSS = auto()
    PENDING = auto()
    ERROR = auto()


class StrategyFlag(Enum):
    SAFE = auto()
    MAINTAIN = auto()
    RANDOM = auto()
    AUTO_MULTIPLIER = auto()


class BettingSide(Enum):
    RANDOM = auto()
    HEADS = auto()
    TAILS = auto()

@dataclass(slots=True)
class MartingaleStrategy:
    base_bet: int
    current_bet: int
    # Replaces single mode. Default is empty set (Standard Static).
    active_flags: set[StrategyFlag] = field(default_factory=set)
    static_multiplier: float = 3.0
    consecutive_losses: int = 0
    max_bet: int = 250000
    betting_side: BettingSide = BettingSide.RANDOM
    
    # Track previous result for Maintain logic
    last_result: BetResult = BetResult.PENDING

    def on_win(self) -> None:
        self.last_result = BetResult.WIN
        self.consecutive_losses = 0
        if StrategyFlag.MAINTAIN in self.active_flags:
            return
        self.current_bet = self.base_bet

    def on_loss(self) -> None:
        self.consecutive_losses += 1

        if self._handle_strategy_breaks():
            return

        multiplier = self._calculate_next_multiplier()
        self._set_next_bet(multiplier)
        self.last_result = BetResult.LOSS

    def _handle_strategy_breaks(self) -> bool:
        """Checks for SAFE/MAINTAIN break conditions. Returns True if bet was modified."""
        if StrategyFlag.MAINTAIN in self.active_flags:
            if self.last_result == BetResult.WIN and self.current_bet > self.base_bet:
                self._apply_drop_bet()
                self.last_result = BetResult.LOSS
                return True

        if StrategyFlag.SAFE in self.active_flags and self.consecutive_losses > 5:
            self._apply_drop_bet()
            self.last_result = BetResult.LOSS
            return True
            
        return False

    def _calculate_next_multiplier(self) -> float:
        multiplier = self.static_multiplier
        
        if StrategyFlag.AUTO_MULTIPLIER in self.active_flags:
            multiplier = self._get_auto_multiplier()
            
        if StrategyFlag.RANDOM in self.active_flags:
            multiplier = self._apply_random_jitter(multiplier)
            
        return multiplier

    def _apply_random_jitter(self, base: float) -> float:
        decay_ceiling = max(0.0, 0.5 - (self.consecutive_losses * 0.05))
        return base + random.uniform(0.0, decay_ceiling)

    def _apply_drop_bet(self) -> None:
        next_bet = int(self.current_bet / 4)
        self.current_bet = max(next_bet, self.base_bet)

    def _set_next_bet(self, multiplier: float) -> None:
        next_bet = int(self.current_bet * multiplier)
        self.current_bet = min(next_bet, self.max_bet)
    
    def get_next_side(self) -> Literal["h", "t"]:
        if self.betting_side == BettingSide.HEADS:
            return "h"
        if self.betting_side == BettingSide.TAILS:
            return "t"
        return random.choice(["h", "t"])

    def _get_auto_multiplier(self) -> float:
        # "Start": 0-2 losses -> x2.0 - x2.5
        if self.consecutive_losses <= 2:
            return 2.0
            
        # "Middle": 3-5 losses -> x3.0 (Recover mode)
        if self.consecutive_losses <= 5:
            return 3.0
            
        # "End": 6+ losses -> x1.6 (Safety mode to prolong survival)
        return 1.6

    def reset(self) -> None:
        self.current_bet = self.base_bet
        self.consecutive_losses = 0
        self.last_result = BetResult.PENDING


@dataclass(slots=True)
class OWOBet:
    amount: int
    result: BetResult
    timestamp: datetime = field(default_factory=datetime.now)
    won_amount: int = 0

    @property
    def net_profit(self) -> int:
        if self.result == BetResult.WIN:
            return self.won_amount - self.amount
        elif self.result == BetResult.LOSS:
            return -self.amount
        return 0


@dataclass(slots=True)
class OWOStats:
    total_games: int = 0
    total_wins: int = 0
    total_losses: int = 0
    total_money_won: int = 0
    total_money_lost: int = 0
    highest_win: int = 0
    highest_loss_streak: int = 0
    current_loss_streak: int = 0
    session_start: datetime | None = None
    session_end: datetime | None = None

    @property
    def win_rate(self) -> float:
        if self.total_games == 0:
            return 0.0
        return (self.total_wins / self.total_games) * 100

    @property
    def loss_rate(self) -> float:
        if self.total_games == 0:
            return 0.0
        return (self.total_losses / self.total_games) * 100

    @property
    def net_profit(self) -> int:
        return self.total_money_won - self.total_money_lost

    def record_bet(self, bet: OWOBet) -> None:
        self.total_games += 1

        if bet.result == BetResult.WIN:
            self.total_wins += 1
            self.total_money_won += bet.won_amount
            if bet.won_amount > self.highest_win:
                self.highest_win = bet.won_amount
            self.current_loss_streak = 0
        elif bet.result == BetResult.LOSS:
            self.total_losses += 1
            self.total_money_lost += bet.amount
            self.current_loss_streak += 1
            if self.current_loss_streak > self.highest_loss_streak:
                self.highest_loss_streak = self.current_loss_streak

    def start_session(self) -> None:
        self.session_start = datetime.now()
        self.session_end = None

    def end_session(self) -> None:
        self.session_end = datetime.now()

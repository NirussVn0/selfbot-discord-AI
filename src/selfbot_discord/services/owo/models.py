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


class MultiplierMode(Enum):
    STATIC = auto()
    AUTO = auto()
    SAFE = auto()
    MAINTAIN = auto()
    RANDOM_DECAY = auto()


class BettingSide(Enum):
    RANDOM = auto()
    HEADS = auto()
    TAILS = auto()


@dataclass(slots=True)
class MartingaleStrategy:
    base_bet: int
    current_bet: int
    multiplier_mode: MultiplierMode = MultiplierMode.STATIC
    static_multiplier: float = 3.0
    consecutive_losses: int = 0
    max_bet: int = 250000
    betting_side: BettingSide = BettingSide.RANDOM
    
    # Track previous result for Maintain logic
    last_result: BetResult = BetResult.PENDING

    def on_win(self) -> None:
        self.last_result = BetResult.WIN
        self.consecutive_losses = 0
        
        # Maintain Logic: If we were betting high, KEEP it high on win
        if self.multiplier_mode == MultiplierMode.MAINTAIN:
            # If we won, we do NOT reset. We stay at current_bet.
            return

        self.current_bet = self.base_bet

    def on_loss(self) -> None:
        self.consecutive_losses += 1
        
        # Determine Multiplier
        multiplier = self.static_multiplier
        
        if self.multiplier_mode == MultiplierMode.AUTO:
            multiplier = self._get_auto_multiplier()
            
        elif self.multiplier_mode == MultiplierMode.RANDOM_DECAY:
             # Random Decay / Dynamic Random
             # User Request: "x1.5-random" -> 1.5 to 2.0
             # Logic: Base + Random(0.0 to 0.5)
             # Also applying slight decay based on streak for "stealth"
             
             base = self.static_multiplier
             # Decay factor: reduces the ceiling as streak grows
             decay_ceiling = max(0.0, 0.5 - (self.consecutive_losses * 0.05))
             
             jitter = random.uniform(0.0, decay_ceiling)
             multiplier = base + jitter

        elif self.multiplier_mode == MultiplierMode.MAINTAIN:
            # Maintain Logic Handle Loss
            # If we were Maintaining a Streak (High Bet) and LOST:
            # Drop 2 steps (approx /4)
            if self.last_result == BetResult.WIN and self.current_bet > self.base_bet:
                next_bet = int(self.current_bet / 4) 
                if next_bet < self.base_bet:
                    next_bet = self.base_bet
                self.current_bet = next_bet
                self.last_result = BetResult.LOSS
                return
            
            # Normal Loss: Use the configured multiplier (e.g. x1.5 or x2)
            multiplier = self.static_multiplier

        elif self.multiplier_mode == MultiplierMode.SAFE:
            # Safe Logic: If streak > 5, Panic Drop
            if self.consecutive_losses > 5:
                 next_bet = int(self.current_bet / 4)
                 if next_bet < self.base_bet:
                     next_bet = self.base_bet
                 self.current_bet = next_bet
                 self.last_result = BetResult.LOSS
                 return

            multiplier = self.static_multiplier

            
        # Calculate Next Bet
        next_bet = int(self.current_bet * multiplier)
        
        # Cap at max bet
        if next_bet > self.max_bet:
            next_bet = self.max_bet
            
        self.current_bet = next_bet
        self.last_result = BetResult.LOSS

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

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto


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


@dataclass(slots=True)
class MartingaleStrategy:
    base_bet: int
    current_bet: int
    loss_multiplier: float = 3.0
    consecutive_losses: int = 0

    def on_win(self) -> None:
        self.current_bet = self.base_bet
        self.consecutive_losses = 0

    def on_loss(self) -> None:
        self.consecutive_losses += 1
        self.current_bet = int(self.current_bet * self.loss_multiplier)

    def reset(self) -> None:
        self.current_bet = self.base_bet
        self.consecutive_losses = 0


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

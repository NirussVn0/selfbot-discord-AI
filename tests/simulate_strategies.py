# Start Mocking
from dataclasses import dataclass, field
from enum import Enum, auto
import random
from typing import Literal

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

class BetResult(Enum):
    WIN = auto()
    LOSS = auto()
    PENDING = auto()
    ERROR = auto()

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
             decay = min(0.5, self.consecutive_losses * 0.1)
             base = 2.0 - decay
             jitter = random.uniform(-0.1, 0.1)
             multiplier = max(1.5, base + jitter)

        elif self.multiplier_mode == MultiplierMode.MAINTAIN:
            if self.last_result == BetResult.WIN and self.current_bet > self.base_bet:
                next_bet = int(self.current_bet / 4) # Drop 2 levels (assuming x2)
                if next_bet < self.base_bet:
                    next_bet = self.base_bet
                self.current_bet = next_bet
                self.last_result = BetResult.LOSS
                return
            
            multiplier = 2.0

        elif self.multiplier_mode == MultiplierMode.SAFE:
            if self.consecutive_losses > 5:
                 next_bet = int(self.current_bet / 4)
                 if next_bet < self.base_bet:
                     next_bet = self.base_bet
                 self.current_bet = next_bet
                 self.last_result = BetResult.LOSS
                 return

            multiplier = 2.0

        next_bet = int(self.current_bet * multiplier)
        
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
        if self.consecutive_losses <= 2:
            return 2.0
        if self.consecutive_losses <= 5:
            return 3.0
        return 1.6

    def reset(self) -> None:
        self.current_bet = self.base_bet
        self.consecutive_losses = 0
        self.last_result = BetResult.PENDING
# End Mocking


def simulate_strategy(name: str, mode: MultiplierMode, num_rounds=20):
    print(f"\n--- Simulating Strategy: {name} ---")
    strategy = MartingaleStrategy(
        base_bet=100, 
        current_bet=100, 
        multiplier_mode=mode,
        max_bet=1000000
    )
    
    # Custom scenario: 
    # 1. Start (100) -> Win
    # 2. Start (100) -> Win (Maintain Check - should stay 100)
    # 3. Start (100) -> Loss (x2 -> 200)
    # 4. 200 -> Loss (x2 -> 400)
    # 5. 400 -> Loss (x2 -> 800)
    # 6. 800 -> Win (Should Reset or Maintain?)
    
    # Let's run a specific sequence for MAINTAIN to test the "Drop 2 steps" logic
    if mode == MultiplierMode.MAINTAIN:
        print("Sequence: Win, Win, Loss, Loss (x2), Win (Maintain High), Win (Maintain High), Loss (Drop 2)")
        
        # 1. 100 -> Win
        print(f"Bet: {strategy.current_bet} | Result: WIN")
        strategy.on_win()
        
        # 2. 100 -> Win
        print(f"Bet: {strategy.current_bet} | Result: WIN")
        strategy.on_win()
        
        # 3. 100 -> Loss
        print(f"Bet: {strategy.current_bet} | Result: LOSS")
        strategy.on_loss()
        
        # 4. 200 -> Loss
        print(f"Bet: {strategy.current_bet} | Result: LOSS")
        strategy.on_loss()
        
        # 5. 400 -> Win (Strategy: MAINTAIN implies we KEEP betting 400?)
        # Logic says: on_win -> if MAINTAIN -> return (don't reset). So next bet is 400.
        print(f"Bet: {strategy.current_bet} | Result: WIN")
        strategy.on_win()
        
        # 6. 400 -> Win (Still 400)
        print(f"Bet: {strategy.current_bet} | Result: WIN")
        strategy.on_win()
        
        # 7. 400 -> Loss. (Condition: last=WIN, current > base). Should drop 2 steps.
        # 400 / 4 = 100.
        print(f"Bet: {strategy.current_bet} | Result: LOSS (Expect Drop)")
        strategy.on_loss()
        
        print(f"Next Bet: {strategy.current_bet} (Expected: 100)")
        
    elif mode == MultiplierMode.SAFE:
        print("Sequence: 6 Losses in a row (Trigger Safety Drop)")
        for i in range(7):
            print(f"Bet: {strategy.current_bet} | Result: LOSS")
            strategy.on_loss()
        print(f"Next Bet: {strategy.current_bet}")

    else:
        # Generic flow
        pass

if __name__ == "__main__":
    simulate_strategy("MAINTAIN", MultiplierMode.MAINTAIN)
    simulate_strategy("SAFE", MultiplierMode.SAFE)

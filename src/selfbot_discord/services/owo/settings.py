from __future__ import annotations

from selfbot_discord.services.owo.models import BettingSide, StrategyFlag
import json
import logging
logger = logging.getLogger(__name__)
from pathlib import Path
from dataclasses import asdict, dataclass

@dataclass
class OWOGameConfig:
    amount: int
    active_flags: set[StrategyFlag]
    static_multiplier: float
    betting_side: BettingSide

    def to_dict(self) -> dict:
        return {
            "amount": self.amount,
            "strategies": [flag.name for flag in self.active_flags], # Save as list of strings
            "static_multiplier": self.static_multiplier,
            "betting_side": self.betting_side.name
        }

    @classmethod
    def from_dict(cls, data: dict) -> OWOGameConfig:
        # Backward compatibility for old "multiplier_mode"
        strategies = set()
        
        # New format
        if "strategies" in data:
            for s_name in data["strategies"]:
                try:
                    strategies.add(StrategyFlag[s_name])
                except KeyError:
                    pass
                    
        # Old format migration
        elif "multiplier_mode" in data:
            mode = data["multiplier_mode"]
            if mode == "SAFE":
                strategies.add(StrategyFlag.SAFE)
            elif mode == "MAINTAIN":
                strategies.add(StrategyFlag.MAINTAIN)
            elif mode == "RANDOM_DECAY":
                strategies.add(StrategyFlag.RANDOM)
            elif mode == "AUTO":
                strategies.add(StrategyFlag.AUTO_MULTIPLIER)

        return cls(
            amount=data.get("amount", 1000),
            active_flags=strategies,
            static_multiplier=data.get("static_multiplier", 2.0),
            betting_side=BettingSide[data.get("betting_side", "RANDOM")]
        )

class OWOSettingsManager:
    """Manages persistence of OWO game settings."""
    
    SETTINGS_FILE = Path("data/owo_config.json")

    @classmethod
    def save(cls, config: OWOGameConfig) -> None:
        try:
            cls.SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(cls.SETTINGS_FILE, "w") as f:
                json.dump(config.to_dict(), f, indent=2)
            logger.info("Saved OWO game settings.")
        except IOError as e:
            logger.error(f"Failed to save OWO settings: {e}")

    @classmethod
    def load(cls) -> OWOGameConfig | None:
        if not cls.SETTINGS_FILE.exists():
            return None
            
        try:
            with open(cls.SETTINGS_FILE, "r") as f:
                data = json.load(f)
                return OWOGameConfig.from_dict(data)
        except (IOError, json.JSONDecodeError, KeyError) as e:
            logger.error(f"Failed to load OWO settings: {e}")
            return None

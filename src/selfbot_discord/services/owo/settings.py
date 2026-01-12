from __future__ import annotations

import json
import logging
from pathlib import Path
from dataclasses import asdict, dataclass

from selfbot_discord.services.owo.models import BettingSide, MultiplierMode

logger = logging.getLogger(__name__)

@dataclass
class OWOGameConfig:
    amount: int
    multiplier_mode: MultiplierMode
    static_multiplier: float
    betting_side: BettingSide

    def to_dict(self) -> dict:
        return {
            "amount": self.amount,
            "multiplier_mode": self.multiplier_mode.name,
            "static_multiplier": self.static_multiplier,
            "betting_side": self.betting_side.name
        }

    @classmethod
    def from_dict(cls, data: dict) -> OWOGameConfig:
        return cls(
            amount=data.get("amount", 1000),
            multiplier_mode=MultiplierMode[data.get("multiplier_mode", "STATIC")],
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

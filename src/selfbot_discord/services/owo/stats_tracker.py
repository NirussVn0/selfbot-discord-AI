from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import TYPE_CHECKING

from selfbot_discord.services.owo.models import OWOStats

if TYPE_CHECKING:
    from selfbot_discord.services.owo.models import OWOBet

logger = logging.getLogger(__name__)


class OWOStatsTracker:
    def __init__(self, stats_file: Path | None = None) -> None:
        self.stats_file = stats_file or Path("data/owo_stats.json")
        self.stats = OWOStats()
        self._load()

    def record_bet(self, bet: OWOBet) -> None:
        self.stats.record_bet(bet)
        self._save()

    def get_stats(self) -> OWOStats:
        return self.stats

    def reset_stats(self) -> None:
        self.stats = OWOStats()
        self._save()
        logger.info("OWO statistics reset.")

    def start_session(self) -> None:
        self.stats.start_session()
        self._save()

    def end_session(self) -> None:
        self.stats.end_session()
        self._save()

    def _save(self) -> None:
        try:
            self.stats_file.parent.mkdir(parents=True, exist_ok=True)
            data = {
                "total_games": self.stats.total_games,
                "total_wins": self.stats.total_wins,
                "total_losses": self.stats.total_losses,
                "total_money_won": self.stats.total_money_won,
                "total_money_lost": self.stats.total_money_lost,
                "highest_win": self.stats.highest_win,
                "highest_loss_streak": self.stats.highest_loss_streak,
                "current_loss_streak": self.stats.current_loss_streak,
                "session_start": self.stats.session_start.isoformat() if self.stats.session_start else None,
                "session_end": self.stats.session_end.isoformat() if self.stats.session_end else None,
            }
            self.stats_file.write_text(json.dumps(data, indent=2), encoding="utf-8")
        except Exception as exc:
            logger.exception("Failed to save OWO statistics: %s", exc)

    def _load(self) -> None:
        if not self.stats_file.exists():
            logger.debug("No existing OWO statistics file found at %s", self.stats_file)
            return

        try:
            data = json.loads(self.stats_file.read_text(encoding="utf-8"))
            self.stats = OWOStats(
                total_games=data.get("total_games", 0),
                total_wins=data.get("total_wins", 0),
                total_losses=data.get("total_losses", 0),
                total_money_won=data.get("total_money_won", 0),
                total_money_lost=data.get("total_money_lost", 0),
                highest_win=data.get("highest_win", 0),
                highest_loss_streak=data.get("highest_loss_streak", 0),
                current_loss_streak=data.get("current_loss_streak", 0),
            )
            logger.info("Loaded OWO statistics from %s", self.stats_file)
        except Exception as exc:
            logger.exception("Failed to load OWO statistics: %s", exc)
            self.stats = OWOStats()

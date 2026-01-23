import discord
import logging
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from selfbot_discord.config.manager import ConfigManager
    from selfbot_discord.core.bot import DiscordSelfBot

logger = logging.getLogger(__name__)

class StatusService:
    """Service to manage bot status, presence, and AFK modes."""

    def __init__(self, config_manager: "ConfigManager", bot: "DiscordSelfBot"):
        self.config_manager = config_manager
        self.bot = bot

    async def set_activity(self, activity_type: str, name: str) -> None:
        type_map = {
            "playing": discord.ActivityType.playing,
            "watching": discord.ActivityType.watching,
            "listening": discord.ActivityType.listening,
            "streaming": discord.ActivityType.streaming,
            "competing": discord.ActivityType.competing,
        }
        
        act_type = type_map.get(activity_type.lower(), discord.ActivityType.playing)
        activity = discord.Activity(type=act_type, name=name)
        
        self.config_manager.config.discord.presence_message = name
        self.config_manager.save()

        await self.bot.change_presence(
            activity=activity,
            status=discord.Status.online
        )
        logger.info(f"Set activity to {activity_type}: {name}")

    async def stop_activity(self) -> None:
        """Clear the current activity."""
        self.config_manager.config.discord.presence_message = ""
        self.config_manager.save()
        await self.bot.change_presence(activity=None)

    def set_afk(self, enabled: bool, message: str | None = None) -> None:
        """Enable or disable AFK mode."""
        self.config_manager.config.discord.afk_enabled = enabled
        if message:
            self.config_manager.config.discord.afk_message = message
        self.config_manager.save()
        state = "enabled" if enabled else "disabled"
        logger.info(f"AFK mode {state}")

    def toggle_autoreply(self, enabled: bool) -> None:
        """Toggle global auto-reply."""
        self.config_manager.config.discord.auto_reply_enabled = enabled
        self.config_manager.save()

    async def set_hypesquad(self, house: str) -> str:
        """Change HypeSquad house. 
        Note: reliable libraries for self-bots might vary, using a direct API request wrapper 
        if the client library supports it, otherwise mimicking the request.
        """
        # HypeSquad Houses:
        # 1: Bravery
        # 2: Brilliance
        # 3: Balance
        
        house_map = {
            "bravery": 1,
            "brilliance": 2,
            "balance": 3
        }
        
        house_id = house_map.get(house.lower())
        if not house_id:
            return "Invalid house. Choose: bravery, brilliance, balance."

        # Discord.py-self might not expose this directly easily in the high level API 
        # for selfbots in a standard way, but we can try the http client.
        
        try:
             await self.bot.http.request(
                discord.http.Route('POST', '/hypesquad/online'),
                json={'house_id': house_id}
            )
             return f"HypeSquad house changed to {house.capitalize()}."
        except Exception as e:
            logger.error(f"Failed to change HypeSquad: {e}")
            return f"Failed to change HypeSquad: {e}"

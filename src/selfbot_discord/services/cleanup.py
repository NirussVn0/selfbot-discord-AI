import asyncio
import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from discord import TextChannel

logger = logging.getLogger(__name__)

class MessageCleaner:
    """Service for bulk message deletion/cleanup."""

    @staticmethod
    async def cleanup_channel(channel: "TextChannel", amount: int, target_ids: int | list[int] | None = None) -> int:
        """
        Deletes a specified amount of messages from a channel, optionally filtering by user ID(s).
        
        Args:
            channel: The text channel to clean.
            amount: Maximum number of messages to delete.
            target_ids: Optional user ID or list of IDs to filter messages by.
            
        Returns:
            int: The number of messages actually deleted.
        """
        deleted = 0
        scan_limit = min(amount * 3 + 50, 2000)
        
        targets = set()
        if target_ids is not None:
            if isinstance(target_ids, int):
                targets.add(target_ids)
            else:
                targets.update(target_ids)
        
        try:
            async for msg in channel.history(limit=scan_limit):
                if deleted >= amount:
                    break
                
                if targets and msg.author.id not in targets:
                    continue
                    
                try:
                    await msg.delete()
                    deleted += 1
                    await asyncio.sleep(0.7) # Rate limit protection
                except Exception:
                    # Ignore deletion errors
                    pass
        except Exception as e:
            logger.warning(f"Error during message cleanup: {e}")
            pass
            
        return deleted

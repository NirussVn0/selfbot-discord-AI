# Runtime wiring for the Discord self-bot

from __future__ import annotations

import asyncio
import logging

from selfbot_discord.ai.gemini import GeminiAIService
from selfbot_discord.config.manager import ConfigManager
from selfbot_discord.core.bot import DiscordSelfBot
from selfbot_discord.services.context import ConversationStore
from selfbot_discord.services.whitelist import WhitelistService
from selfbot_discord.utils.logging import configure_logging

logger = logging.getLogger(__name__)


def _ensure_closed(client: DiscordSelfBot) -> None:
    # Close the Discord client if it is still open

    if client.is_closed():
        return

    try:
        loop = client.loop
        if loop.is_closed():
            return
        if loop.is_running():
            loop.create_task(client.close())
        else:
            loop.run_until_complete(client.close())
    except RuntimeError:
        asyncio.run(client.close())
    except Exception:  # pragma: no cover - defensive cleanup
        logger.exception("Failed to close Discord client cleanly.")


def run_bot(manager: ConfigManager) -> None:
    # Bootstrap and run the Discord self-bot

    manager.validate()
    config = manager.config
    configure_logging(config.logging)

    discord_token = manager.resolve_discord_token()
    gemini_api_key = manager.resolve_gemini_api_key()

    whitelist = WhitelistService(config.whitelist)
    conversation_store = ConversationStore()
    ai_service = GeminiAIService(config.ai, gemini_api_key)

    client = DiscordSelfBot(
        config,
        whitelist=whitelist,
        ai_service=ai_service,
        conversation_store=conversation_store,
    )

    logger.info("Starting Discord self-bot runtime.")
    try:
        client.run(discord_token)
    except KeyboardInterrupt:
        logger.info("Interrupt received; shutting down self-bot.")
    finally:
        _ensure_closed(client)

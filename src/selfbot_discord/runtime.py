from __future__ import annotations

import asyncio
import logging
import os
from importlib.metadata import PackageNotFoundError, version

from selfbot_discord.ai.gemini import GeminiAIService
from selfbot_discord.config.manager import ConfigManager
from selfbot_discord.core.bot import DiscordSelfBot
from selfbot_discord.services.context import ConversationStore
from selfbot_discord.services.whitelist import WhitelistService
from selfbot_discord.utils.logging import configure_logging
from selfbot_discord.ui import ConsoleUI

logger = logging.getLogger(__name__)


def _resolve_version() -> str:
    try:
        return version("selfbot_discord")
    except PackageNotFoundError:
        return "dev"


def _ensure_closed(client: DiscordSelfBot) -> None:
    # Close the Discord client if it is still open.

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
    # Bootstrap and run the Discord self-bot with rich CLI output.

    verbose_events = os.getenv("SELF_BOT_VERBOSE_EVENTS", "").strip().lower() in {"1", "true", "yes", "on"}
    ui = ConsoleUI(verbose_events=verbose_events)
    ui.display_banner(title="Discord Self-Bot", version=_resolve_version(), author="NirussVn0")
    ui.begin_progress(total_steps=3)

    client: DiscordSelfBot | None = None
    interrupted = False
    error: Exception | None = None

    try:
        ui.update_progress("Validating configuration")
        with ui.status("Validating configuration"):
            manager.validate()
        ui.advance_progress()

        config = manager.config
        configure_logging(config.logging, console=ui.console)
        ui.log_success("Configuration loaded successfully.")

        discord_token = manager.resolve_discord_token()
        gemini_api_key = manager.resolve_gemini_api_key()

        ui.update_progress("Initialising runtime services")
        with ui.status("Initialising runtime services"):
            whitelist = WhitelistService(config.whitelist)
            conversation_store = ConversationStore()
            ai_service = GeminiAIService(config.ai, gemini_api_key)
        ui.advance_progress()
        ui.log_success("Runtime services initialised.")

        ui.update_progress("Preparing Discord client")
        client = DiscordSelfBot(
            config,
            whitelist=whitelist,
            ai_service=ai_service,
            conversation_store=conversation_store,
            ui=ui,
        )
        ui.advance_progress()
        ui.end_progress()

        ui.update_status("CONNECTING")
        ui.log_info("Connecting to Discord gateway...")
        ui.start_live()

        logger.info("Starting Discord self-bot runtime.")
        try:
            client.run(discord_token)
        except KeyboardInterrupt:
            interrupted = True
            logger.info("Interrupt received; shutting down self-bot.")
        except Exception as exc:  # pragma: no cover - run loop failures
            error = exc
            logger.exception("Unhandled exception in Discord runtime.")
            raise
    except Exception as exc:
        if error is None:
            error = exc
            logger.exception("Startup failed before client initialisation.")
        raise
    finally:
        ui.end_progress()
        if client is not None:
            _ensure_closed(client)
        ui.stop(interrupted=interrupted, error=error)

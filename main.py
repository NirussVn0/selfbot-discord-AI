"""Entry point for running the self Discord bot."""

from __future__ import annotations

import logging
from contextlib import suppress

from selfbot_discord import ConfigManager
from selfbot_discord.runtime import run_bot


def main() -> None:
    manager = ConfigManager()
    with suppress(KeyboardInterrupt):
        run_bot(manager)
    logging.getLogger(__name__).info("Bot shutdown complete.")


if __name__ == "__main__":
    main()

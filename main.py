#Entry point for running the self Discord bot

from __future__ import annotations

import asyncio

from selfbot_discord import ConfigManager


async def bootstrap() -> None:
    # Validate configuration before the bot core is initialised
    manager = ConfigManager()
    manager.validate()
    await asyncio.sleep(0)


def main() -> None:
    # Synchronously bootstrap the async entrypoint
    asyncio.run(bootstrap())


if __name__ == "__main__":
    main()

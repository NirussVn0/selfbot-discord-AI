# Entry point for running the self Discord bot
# Copyright (c) [2025] NirrussVn0

from __future__ import annotations

import asyncio

from self_discord_bot import ConfigManager


async def bootstrap() -> None:

    manager = ConfigManager()
    manager.validate()
    await asyncio.sleep(0)


def main() -> None:
    asyncio.run(bootstrap())


if __name__ == "__main__":
    main()

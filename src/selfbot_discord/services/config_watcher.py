# Configuration file watcher that reloads settings when the YAML file changes.

from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import Awaitable, Callable

from selfbot_discord.config.manager import ConfigManager
from selfbot_discord.config.models import AppConfig
from selfbot_discord.ui.console import ConsoleUI

logger = logging.getLogger(__name__)


class ConfigWatcher:

    def __init__(
        self,
        manager: ConfigManager,
        *,
        on_reload: Callable[[AppConfig], Awaitable[None]],
        ui: ConsoleUI | None = None,
        interval: float = 2.0,
    ) -> None:
        self._manager = manager
        self._on_reload = on_reload
        self._interval = interval
        self._ui = ui
        self._task: asyncio.Task[None] | None = None
        self._last_mtime: float | None = None

    @property
    def path(self) -> Path:
        return self._manager.path

    def start(self) -> None:
        if self._task is None:
            self._task = asyncio.create_task(self._run(), name="config-watcher")

    async def stop(self) -> None:
        task = self._task
        if task is None:
            return
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
        self._task = None

    async def _run(self) -> None:
        try:
            self._last_mtime = self._current_mtime()
            while True:
                await asyncio.sleep(self._interval)
                current_mtime = self._current_mtime()
                if current_mtime is None or self._last_mtime is None:
                    continue
                if current_mtime <= self._last_mtime:
                    continue

                try:
                    config = self._manager.reload()
                except Exception as exc:
                    logger.exception("Failed to reload configuration: %s", exc)
                    if self._ui:
                        self._ui.log_error(f"Config reload failed: {exc}")
                    continue

                self._last_mtime = current_mtime
                if self._ui:
                    self._ui.log_info("Configuration reloaded from disk.")
                try:
                    await self._on_reload(config)
                except Exception as exc:
                    logger.exception("Config reload callback failed: %s", exc)
                    if self._ui:
                        self._ui.log_error(f"Config reload callback failed: {exc}")
        except asyncio.CancelledError:
            pass

    def _current_mtime(self) -> float | None:
        try:
            return self.path.stat().st_mtime
        except FileNotFoundError:
            logger.warning("Configuration file %s not found.", self.path)
            return None

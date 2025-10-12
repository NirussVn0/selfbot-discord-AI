# Environment variable management utilities.

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from dotenv import dotenv_values, load_dotenv

from .exceptions import EnvironmentVariableError


class EnvironmentManager:
    # Loads and validates environment variables for the application.

    def __init__(self, dotenv_path: Path | None = Path(".env"), *, auto_load: bool = True, override: bool = False) -> None:
        # Create a new environment manager.
        self._dotenv_path = dotenv_path
        self._override = override
        if auto_load:
            self.load()

    @property
    def dotenv_path(self) -> Path | None:
        # Return the configured dotenv path.
        return self._dotenv_path

    def load(self) -> None:
        # Load environment variables from the configured `.env` file.
        load_dotenv(dotenv_path=self._dotenv_path, override=self._override)

    def get(self, key: str, default: str | None = None) -> str | None:
        # Return the value of an environment variable.
        return os.getenv(key, default)

    def require(self, key: str) -> str:
        # Return the value of a required environment variable.
        # Raises:
        #     EnvironmentVariableError: If the variable is missing or empty.
        value = self.get(key)
        if value is None or value == "":
            raise EnvironmentVariableError(key)
        return value

    def as_dict(self) -> dict[str, Any]:
        # Return environment variables from the `.env` file without modifying the OS environment.
        dotenv_path = self._dotenv_path
        if dotenv_path is None:
            return dict(os.environ)
        return {**dotenv_values(dotenv_path)}

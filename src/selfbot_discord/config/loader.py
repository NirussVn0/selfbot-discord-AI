# YAML configuration loader utilities.

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError

from .exceptions import ConfigFileNotFoundError, MalformedConfigurationError
from .models import AppConfig


class ConfigLoader:
    # Load application configuration from YAML files.

    def __init__(self, config_path: Path) -> None:
        # Create a loader bound to a specific YAML configuration file.
        self._config_path = config_path

    @property
    def path(self) -> Path:
        # Return the configured path of the YAML file.
        return self._config_path

    def load(self) -> AppConfig:
        # Load a configuration file and parse it into an `AppConfig` instance.
        raw_data = self._read_yaml()
        try:
            return AppConfig.model_validate(raw_data or {})
        except ValidationError as exc:
            raise MalformedConfigurationError(str(exc)) from exc

    def save(self, config: AppConfig) -> None:
        # Persist the provided configuration back to disk.
        payload = config.model_dump(mode="json")
        with self._config_path.open("w", encoding="utf-8") as config_file:
            yaml.safe_dump(payload, config_file, sort_keys=False)

    def _read_yaml(self) -> dict[str, Any]:
        # Read YAML content from the file system.
        path = self._config_path
        if not path.exists():
            raise ConfigFileNotFoundError(path)
        with path.open("r", encoding="utf-8") as config_file:
            return yaml.safe_load(config_file) or {}

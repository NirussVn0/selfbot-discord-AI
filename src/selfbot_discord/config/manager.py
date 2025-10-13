# High-level configuration manager that orchestrates file and environment loading.

from __future__ import annotations

from pathlib import Path
from typing import Any

from .environment import EnvironmentManager
from .exceptions import ConfigurationError
from .loader import ConfigLoader
from .models import AppConfig


class ConfigManager:
    # Coordinates configuration loading from YAML files and environment variables.

    def __init__(
        self,
        *,
        config_path: Path = Path("config/config.yaml"),
        dotenv_path: Path | None = Path(".env"),
        auto_load_env: bool = True,
    ) -> None:
        # Initialise the configuration manager.
        self._loader = ConfigLoader(config_path=config_path)
        self._environment = EnvironmentManager(dotenv_path=dotenv_path, auto_load=auto_load_env)
        self._cached_config: AppConfig | None = None

    @property
    def config(self) -> AppConfig:
        # Return the cached application configuration, loading it if necessary.
        if self._cached_config is None:
            self._cached_config = self._loader.load()
        return self._cached_config

    def reload(self) -> AppConfig:
        # Force reload of configuration from disk.
        self._cached_config = self._loader.load()
        return self._cached_config

    def require_secret(self, env_key: str) -> str:
        # Retrieve a required secret from the environment.
        return self._environment.require(env_key)

    def resolve_discord_token(self) -> str:
        # Return the Discord token using the configured environment variable name.
        env_key = self.config.secrets.discord_token
        return self.require_secret(env_key)

    def resolve_gemini_api_key(self) -> str:
        # Return the Gemini API key using the configured environment variable name.
        env_key = self.config.secrets.gemini_api_key
        return self.require_secret(env_key)

    def as_dict(self) -> dict[str, Any]:
        # Return a serialisable view of the loaded configuration.
        return self.config.model_dump()

    def is_whitelist_enabled(self) -> bool:
        # Determine whether whitelist enforcement should be active.
        override = self._environment.get("WHITELIST_ENABLED")
        if override is None:
            return self.config.whitelist.enabled
        return override.strip().lower() in {"1", "true", "yes", "on"}

    def validate(self) -> None:
        # Eagerly validate the configuration and mandatory secrets.
        config = self.config
        missing: list[str] = []
        for key in (config.secrets.discord_token, config.secrets.gemini_api_key):
            try:
                self._environment.require(key)
            except ConfigurationError:
                missing.append(key)
        if missing:
            missing_keys = ", ".join(missing)
            message = f"Missing required environment secrets: {missing_keys}"
            raise ConfigurationError(message)

    def save(self) -> None:
        # Persist the in-memory configuration to disk.
        if self._cached_config is None:
            raise ConfigurationError("Cannot save configuration before it has been loaded.")
        self._loader.save(self._cached_config)

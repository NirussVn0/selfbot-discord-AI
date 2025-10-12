# Custom exception hierarchy for configuration management.

from __future__ import annotations

from pathlib import Path


class ConfigurationError(Exception):
    """Base class for configuration-related errors."""


class ConfigFileNotFoundError(ConfigurationError):
    """Raised when the configuration file cannot be located."""

    def __init__(self, path: Path) -> None:
        message = f"Configuration file not found at path: {path}"
        super().__init__(message)
        self.path = path


class EnvironmentVariableError(ConfigurationError):
    """Raised when a required environment variable is missing or invalid."""

    def __init__(self, key: str) -> None:
        message = f"Required environment variable '{key}' is not set."
        super().__init__(message)
        self.key = key


class MalformedConfigurationError(ConfigurationError):
    """Raised when configuration data cannot be parsed or validated."""

    def __init__(self, detail: str) -> None:
        message = f"Malformed configuration: {detail}"
        super().__init__(message)
        self.detail = detail

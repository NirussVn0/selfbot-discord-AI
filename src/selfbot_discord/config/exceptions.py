# Custom exception hierarchy for configuration management.

from __future__ import annotations

from pathlib import Path


class ConfigurationError(Exception):
    # Base class for configuration-related errors
    pass


class ConfigFileNotFoundError(ConfigurationError):

    def __init__(self, path: Path) -> None:
        message = f"Configuration file not found at path: {path}"
        super().__init__(message)
        self.path = path


class EnvironmentVariableError(ConfigurationError):

    def __init__(self, key: str) -> None:
        message = f"Required environment variable '{key}' is not set."
        super().__init__(message)
        self.key = key


class MalformedConfigurationError(ConfigurationError):

    def __init__(self, detail: str) -> None:
        message = f"Malformed configuration: {detail}"
        super().__init__(message)
        self.detail = detail

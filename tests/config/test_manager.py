# Tests for the high-level configuration manager and environment utilities.

from __future__ import annotations

from pathlib import Path

import pytest

from self_discord_bot.config.environment import EnvironmentManager
from self_discord_bot.config.exceptions import ConfigurationError, EnvironmentVariableError
from self_discord_bot.config.manager import ConfigManager


def test_config_manager_resolves_secrets(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    config_yaml = """
    secrets:
      discord_token: CUSTOM_DISCORD_TOKEN
      gemini_api_key: CUSTOM_GEMINI_KEY
    """
    config_path = tmp_path / "config.yaml"
    config_path.write_text(config_yaml, encoding="utf-8")

    monkeypatch.setenv("CUSTOM_DISCORD_TOKEN", "discord-token-value")
    monkeypatch.setenv("CUSTOM_GEMINI_KEY", "gemini-key-value")

    manager = ConfigManager(config_path=config_path, dotenv_path=None, auto_load_env=False)

    assert manager.resolve_discord_token() == "discord-token-value"
    assert manager.resolve_gemini_api_key() == "gemini-key-value"
    assert str(manager.config.cache.redis_url) == "redis://redis:6379/0"
    assert manager.config.whitelist.enabled is True


def test_config_manager_validate_flags_missing_secrets(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    config_path = tmp_path / "config.yaml"
    config_path.write_text("{}", encoding="utf-8")

    monkeypatch.delenv("DISCORD_USER_TOKEN", raising=False)
    monkeypatch.delenv("GOOGLE_GEMINI_API_KEY", raising=False)

    manager = ConfigManager(config_path=config_path, dotenv_path=None, auto_load_env=False)

    with pytest.raises(ConfigurationError) as exc_info:
        manager.validate()

    missing_keys = exc_info.value.args[0]
    assert "DISCORD_USER_TOKEN" in missing_keys
    assert "GOOGLE_GEMINI_API_KEY" in missing_keys


def test_environment_manager_loads_dotenv(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    dotenv_path = tmp_path / ".env"
    dotenv_path.write_text("TEMP_KEY=temporary-secret\n", encoding="utf-8")

    monkeypatch.delenv("TEMP_KEY", raising=False)

    env_manager = EnvironmentManager(dotenv_path=dotenv_path, auto_load=False, override=True)
    env_manager.load()

    try:
        assert env_manager.require("TEMP_KEY") == "temporary-secret"
    finally:
        monkeypatch.delenv("TEMP_KEY", raising=False)


def test_environment_manager_require_raises_for_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("MISSING_KEY", raising=False)

    env_manager = EnvironmentManager(dotenv_path=None, auto_load=False)

    with pytest.raises(EnvironmentVariableError):
        env_manager.require("MISSING_KEY")


def test_config_manager_whitelist_override(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        """
        whitelist:
          enabled: false
        """,
        encoding="utf-8",
    )

    manager = ConfigManager(config_path=config_path, dotenv_path=None, auto_load_env=False)

    assert manager.is_whitelist_enabled() is False

    monkeypatch.setenv("WHITELIST_ENABLED", "true")
    assert manager.is_whitelist_enabled() is True

    monkeypatch.setenv("WHITELIST_ENABLED", "0")
    assert manager.is_whitelist_enabled() is False

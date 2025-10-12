# Tests for YAML configuration loading.

from __future__ import annotations

from pathlib import Path

import pytest

from self_discord_bot.config.exceptions import ConfigFileNotFoundError, MalformedConfigurationError
from self_discord_bot.config.loader import ConfigLoader


def test_loader_reads_valid_yaml(tmp_path: Path) -> None:
    yaml_content = """
    discord:
      auto_reply_probability: 0.4
    whitelist:
      enabled: true
      admin_ids: [987654321098765432]
      guild_ids: [123456789012345678]
    """
    config_path = tmp_path / "config.yaml"
    config_path.write_text(yaml_content, encoding="utf-8")

    loader = ConfigLoader(config_path=config_path)
    config = loader.load()

    assert config.discord.auto_reply_probability == pytest.approx(0.4)
    assert config.whitelist.guild_ids == [123456789012345678]
    assert config.whitelist.enabled is True
    assert config.whitelist.admin_ids == [987654321098765432]


def test_loader_raises_for_missing_file(tmp_path: Path) -> None:
    missing_path = tmp_path / "missing.yaml"
    loader = ConfigLoader(config_path=missing_path)

    with pytest.raises(ConfigFileNotFoundError):
        loader.load()


def test_loader_raises_for_invalid_yaml(tmp_path: Path) -> None:
    invalid_yaml = """
    discord:
      auto_reply_probability: 5
    """
    config_path = tmp_path / "config.yaml"
    config_path.write_text(invalid_yaml, encoding="utf-8")

    loader = ConfigLoader(config_path=config_path)

    with pytest.raises(MalformedConfigurationError):
        loader.load()

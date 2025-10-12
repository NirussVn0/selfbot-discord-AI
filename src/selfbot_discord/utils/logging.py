from __future__ import annotations

import json
import logging
from logging import Handler
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path
from typing import Final

from selfbot_discord.config.models import LoggingConfig


class JsonLogFormatter(logging.Formatter):
    # Formatter that emits structured JSON log records

    RESERVED_FIELDS: Final[tuple[str, ...]] = ("message", "asctime")

    def format(self, record: logging.LogRecord) -> str:
        asctime = self.formatTime(record, datefmt="%Y-%m-%dT%H:%M:%SZ")
        payload: dict[str, object] = {
            "timestamp": asctime,
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        for key, value in record.__dict__.items():
            if key.startswith("_") or key in self.RESERVED_FIELDS:
                continue
            if key in payload:
                continue
            payload[key] = value
        return json.dumps(payload, ensure_ascii=False)


def _build_handlers(config: LoggingConfig, formatter: logging.Formatter) -> list[Handler]:
    handlers: list[Handler] = []
    console = logging.StreamHandler()
    console.setFormatter(formatter)
    handlers.append(console)
    if config.log_dir:
        log_dir = Path(config.log_dir)
        log_dir.mkdir(parents=True, exist_ok=True)
        file_handler = TimedRotatingFileHandler(
            filename=str(log_dir / "selfbot.log"),
            when="midnight",
            backupCount=7,
            encoding="utf-8",
        )
        file_handler.setFormatter(formatter)
        handlers.append(file_handler)
    return handlers


def configure_logging(config: LoggingConfig) -> None:

    level = getattr(logging, config.level.upper(), logging.INFO)
    formatter: logging.Formatter
    if config.json_format:
        formatter = JsonLogFormatter()
    else:
        formatter = logging.Formatter(
            fmt="%(asctime)s %(levelname)s [%(name)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    handlers = _build_handlers(config, formatter)
    logging.basicConfig(level=level, handlers=handlers, force=True)
    logging.getLogger("discord").setLevel(logging.INFO)

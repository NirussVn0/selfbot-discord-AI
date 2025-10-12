from __future__ import annotations

import datetime as dt
import json
import logging
from logging import Handler
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path
from typing import Final

from rich.console import Console
from rich.logging import RichHandler
from rich.theme import Theme

from selfbot_discord.config.models import LoggingConfig

SUCCESS_LEVEL = logging.INFO + 5
logging.addLevelName(SUCCESS_LEVEL, "SUCCESS")


def _success(self: logging.Logger, message: object, *args: object, **kwargs: object) -> None:
    # Log a message with SUCCESS level severity

    if self.isEnabledFor(SUCCESS_LEVEL):
        self._log(SUCCESS_LEVEL, message, args, **kwargs)


setattr(logging.Logger, "success", _success)


class JsonLogFormatter(logging.Formatter):
    # Formatter that emits structured JSON log records

    RESERVED_FIELDS: Final[tuple[str, ...]] = ("message", "asctime")

    @staticmethod
    def _serialise(value: object) -> object:
        if isinstance(value, Exception):
            return str(value)
        try:
            json.dumps(value)
            return value
        except TypeError:
            return repr(value)

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
            payload[key] = self._serialise(value)
        return json.dumps(payload, ensure_ascii=False)


class RichConsoleFormatter(logging.Formatter):
    # Formatter that renders colourful Rich log messages

    LEVEL_STYLES: Final[dict[str, str]] = {
        "DEBUG": "[blue][DEBUG][/]",
        "INFO": "[cyan][INFO][/]",
        "SUCCESS": "[green][SUCCESS][/]",
        "WARNING": "[yellow][WARN][/]",
        "ERROR": "[red][ERROR][/]",
        "CRITICAL": "[bold red][CRITICAL][/]",
    }

    def __init__(self) -> None:
        super().__init__("%(message)s")

    def format(self, record: logging.LogRecord) -> str:
        message = super().format(record)
        timestamp = dt.datetime.now().strftime("%H:%M:%S")
        level = self.LEVEL_STYLES.get(record.levelname, f"[white][{record.levelname}][/]")
        return f"[dim]{timestamp}[/] {level} {message}"


def _build_console() -> Console:
    theme = Theme(
        {
            "log.level.info": "cyan",
            "log.level.success": "green",
            "log.level.warning": "yellow",
            "log.level.error": "red",
        }
    )
    return Console(theme=theme, highlight=False)


def _build_handlers(config: LoggingConfig, console: Console) -> list[Handler]:
    handlers: list[Handler] = []

    rich_handler = RichHandler(
        console=console,
        markup=True,
        rich_tracebacks=True,
        show_path=False,
        show_time=False,
        show_level=False,
    )
    rich_handler.setFormatter(RichConsoleFormatter())
    handlers.append(rich_handler)

    if config.log_dir:
        log_dir = Path(config.log_dir)
        log_dir.mkdir(parents=True, exist_ok=True)
        file_handler = TimedRotatingFileHandler(
            filename=str(log_dir / "selfbot.log"),
            when="midnight",
            backupCount=7,
            encoding="utf-8",
        )
        file_handler.setFormatter(JsonLogFormatter())
        handlers.append(file_handler)

    return handlers


def configure_logging(config: LoggingConfig, *, console: Console | None = None) -> Console:
    # Configure logging with colourful console output and JSON file rotation.

    console = console or _build_console()
    level = getattr(logging, config.level.upper(), logging.INFO)
    handlers = _build_handlers(config, console)
    logging.basicConfig(level=level, handlers=handlers, force=True)
    logging.getLogger("discord").setLevel(logging.INFO)
    return console

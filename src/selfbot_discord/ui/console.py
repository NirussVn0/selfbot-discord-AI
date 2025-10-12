# Rich-powered console interface for the Discord self-bot runtime.

from __future__ import annotations

import datetime as dt
import threading
import time
from contextlib import contextmanager
from typing import Generator

from rich import box
from rich.align import Align
from rich.console import Console, Group
from rich.live import Live
from rich.markup import escape
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TaskID,
    TextColumn,
    TimeElapsedColumn,
)
from rich.table import Table
from rich.theme import Theme
from rich.text import Text


class ConsoleUI:
    # High-level helper for colourful CLI output and live status updates.

    STATUS_STYLES = {
        "STARTING": "yellow",
        "CONNECTING": "yellow",
        "ONLINE": "green",
        "BUSY": "magenta",
        "IDLE": "cyan",
        "OFFLINE": "red",
        "ERROR": "red",
    }

    def __init__(self, *, verbose_events: bool = False) -> None:
        theme = Theme(
            {
                "status.online": "bold green",
                "status.connecting": "bold yellow",
                "status.busy": "bold magenta",
                "status.offline": "bold red",
                "stats.label": "dim",
                "stats.value": "bold white",
                "banner.title": "bold magenta",
            }
        )
        self.console = Console(theme=theme, highlight=False)
        self.verbose_events = verbose_events
        self.start_time = time.perf_counter()
        self.ready_time: float | None = None
        self._status = "STARTING"
        self._status_style = self.STATUS_STYLES.get(self._status, "yellow")
        self._messages_processed = 0
        self._replies_sent = 0
        self._commands_executed = 0
        self._username = "Unknown"
        self._user_id = "—"
        self._guild_count = 0
        self._live: Live | None = None
        self._live_stop = threading.Event()
        self._ticker: threading.Thread | None = None
        self._lock = threading.Lock()
        self._progress: Progress | None = None
        self._progress_task: TaskID | None = None

    # --------------------------------------------------------------------- banner
    def display_banner(self, *, title: str, version: str | None, author: str | None) -> None:
        # Render an ASCII art banner when the runtime boots.

        ascii_art = Text.from_markup(
            "\n".join(
                [
                    r"[banner.title]   ____       _ _           _   ____        _   [/]",
                    r"[banner.title]  / ___|  ___| (_) ___  ___| |_| __ )  ___ | |_ [/]",
                    r"[banner.title]  \___ \ / _ \ | |/ _ \/ __| __|  _ \ / _ \| __|[/]",
                    r"[banner.title]   ___) |  __/ | |  __/ (__| |_| |_) | (_) | |_ [/]",
                    r"[banner.title]  |____/ \___|_| |\___|\___|\__|____/ \___/ \__|[/]",
                    r"[banner.title]              |__/                                      [/]",
                ]
            )
        )
        ascii_art.justify = "center"

        info_table = Table.grid(padding=(0, 2))
        info_table.add_column()
        info_table.add_column()
        info_table.add_row("[cyan]Version[/]", version or "dev")
        info_table.add_row("[cyan]Author[/]", author or "Unknown")

        banner_group = Group(
            Align.center(ascii_art),
            Align.center(info_table),
        )

        panel = Panel(
            banner_group,
            border_style="magenta",
            box=box.DOUBLE,
            title=title,
            title_align="center",
        )
        self.console.print(panel)
        self.console.print()

    # --------------------------------------------------------------------- logging helpers
    def log_success(self, message: str) -> None:
        self._log(message, style="green", icon="✓")

    def log_info(self, message: str) -> None:
        self._log(message, style="cyan", icon="ℹ")

    def log_warning(self, message: str) -> None:
        self._log(message, style="yellow", icon="⚠")

    def log_error(self, message: str) -> None:
        self._log(message, style="red", icon="✖")

    def _log(self, message: str, *, style: str, icon: str) -> None:
        timestamp = time.strftime("%H:%M:%S")
        self.console.print(f"[dim]{timestamp}[/] [{style}]{icon}[/] {message}")

    # --------------------------------------------------------------------- status + progress
    @contextmanager
    def status(self, message: str) -> Generator[None, None, None]:
        # Display a spinner while a step is executing.

        with self.console.status(f"[bold cyan]{message}...", spinner="dots"):
            yield

    def begin_progress(self, total_steps: int, description: str = "Initialising...") -> None:
        if self._progress is not None:
            return
        self._progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(bar_width=None),
            TextColumn("{task.completed}/{task.total}", style="progress.remaining"),
            TimeElapsedColumn(),
            console=self.console,
        )
        self._progress_task = self._progress.add_task(description, total=total_steps)
        self._progress.start()

    def update_progress(self, description: str) -> None:
        if self._progress is None or self._progress_task is None:
            return
        self._progress.update(self._progress_task, description=description)

    def advance_progress(self) -> None:
        if self._progress is None or self._progress_task is None:
            return
        self._progress.advance(self._progress_task)

    def end_progress(self) -> None:
        if self._progress is None:
            return
        self._progress.stop()
        self._progress = None
        self._progress_task = None
        self.console.print()

    def update_status(self, status: str, *, style: str | None = None) -> None:
        with self._lock:
            self._status = status.upper()
            self._status_style = style or self.STATUS_STYLES.get(self._status, "cyan")
        self.refresh_live()

    @contextmanager
    def activity(self, status: str, *, style: str | None = None) -> Generator[None, None, None]:
        # Temporarily switch the status indicator for a scoped activity.

        previous_status = self._status
        previous_style = self._status_style
        self.update_status(status, style=style)
        try:
            yield
        finally:
            self.update_status(previous_status, style=previous_style)

    # --------------------------------------------------------------------- identity + stats
    def set_identity(self, username: str, user_id: int | str, guild_count: int) -> None:
        with self._lock:
            self._username = username
            self._user_id = str(user_id)
            self._guild_count = guild_count
        self.refresh_live()

    def increment_messages(self) -> None:
        with self._lock:
            self._messages_processed += 1
        self.refresh_live()

    def increment_replies(self) -> None:
        with self._lock:
            self._replies_sent += 1
        self.refresh_live()

    def increment_commands(self) -> None:
        with self._lock:
            self._commands_executed += 1
        self.refresh_live()

    def notify_event(self, message: str, *, icon: str = "✨", style: str = "white", force: bool = False) -> None:
        timestamp = time.strftime("%H:%M:%S")
        if self.verbose_events or force:
            self.console.print(f"[dim]{timestamp}[/] [{style}]{icon}[/] {message}")

    # --------------------------------------------------------------------- live HUD
    def start_live(self) -> None:
        if self._live is not None:
            return
        self._live_stop.clear()
        self._live = Live(self._render_status_panel(), console=self.console, refresh_per_second=4, auto_refresh=False)
        self._live.start()
        self._ticker = threading.Thread(target=self._live_loop, daemon=True)
        self._ticker.start()

    def _live_loop(self) -> None:
        while not self._live_stop.wait(timeout=1):
            self.refresh_live()

    def refresh_live(self) -> None:
        if self._live is None:
            return
        panel = self._render_status_panel()
        self._live.update(panel, refresh=True)

    def stop_live(self) -> None:
        if self._live is None:
            return
        self._live_stop.set()
        if self._ticker and self._ticker.is_alive():
            self._ticker.join(timeout=1)
        self._live.stop()
        self._live = None
        self._ticker = None

    def _render_status_panel(self) -> Panel:
        uptime_seconds = int(time.perf_counter() - self.start_time)
        uptime = str(dt.timedelta(seconds=uptime_seconds))
        status_text = f"[{self._status_style}]● {self._status}[/]"

        table = Table.grid(expand=True)
        table.add_column()
        table.add_row(f"{status_text}    [stats.label]Uptime[/]: [stats.value]{uptime}[/]")
        table.add_row(f"[stats.label]User[/]: [stats.value]{self._username}[/]  ([stats.value]{self._user_id}[/])")
        table.add_row(
            "[stats.label]Servers[/]: [stats.value]"
            f"{self._guild_count}[/]  [stats.label]Messages[/]: [stats.value]{self._messages_processed}[/]  "
            f"[stats.label]Replies[/]: [stats.value]{self._replies_sent}[/]"
        )
        table.add_row(f"[stats.label]Commands[/]: [stats.value]{self._commands_executed}[/]")

        return Panel(
            Align.left(table),
            title="[bold cyan]Runtime Status[/]",
            border_style=self._status_style,
            box=box.ROUNDED,
        )

    # --------------------------------------------------------------------- ready + summary
    def mark_ready(self, username: str, user_id: int, guild_count: int) -> None:
        self.ready_time = time.perf_counter()
        startup_time = self.ready_time - self.start_time
        self.set_identity(username, user_id, guild_count)
        self.update_status("ONLINE", style=self.STATUS_STYLES["ONLINE"])

        summary_table = Table.grid(padding=(0, 2))
        summary_table.add_row("[green]Connected as[/]", f"{username} ({user_id})")
        summary_table.add_row("[green]Servers[/]", str(guild_count))
        summary_table.add_row("[green]Startup time[/]", f"{startup_time:.2f}s")

        self.console.print(
            Panel(summary_table, border_style="green", title="[bold green]Bot ready[/]", box=box.ROUNDED)
        )
        self.console.print()
        self.refresh_live()

    def show_shutdown_summary(self, *, interrupted: bool, error: Exception | None) -> None:
        uptime_seconds = int(time.perf_counter() - self.start_time)
        uptime = str(dt.timedelta(seconds=uptime_seconds))

        table = Table.grid(padding=(0, 2))
        table.add_row("[cyan]Uptime[/]", uptime)
        table.add_row("[cyan]Messages processed[/]", str(self._messages_processed))
        table.add_row("[cyan]Replies sent[/]", str(self._replies_sent))
        table.add_row("[cyan]Commands run[/]", str(self._commands_executed))

        title = "[bold red]Session ended[/]" if error else "[bold yellow]Interrupted[/]" if interrupted else "[bold green]Session summary[/]"
        border_style = "red" if error else "yellow" if interrupted else "magenta"
        self.console.print(Panel(table, title=title, border_style=border_style, box=box.ROUNDED))

    def stop(self, *, interrupted: bool = False, error: Exception | None = None) -> None:
        if error:
            self.update_status("ERROR", style=self.STATUS_STYLES["ERROR"])
            self.log_error(f"Runtime crashed: {escape(str(error))}")
        elif interrupted:
            self.update_status("OFFLINE", style=self.STATUS_STYLES["OFFLINE"])
            self.log_warning("Keyboard interrupt received. Shutting down gracefully...")
        else:
            self.update_status("OFFLINE", style=self.STATUS_STYLES["OFFLINE"])
            self.log_success("Session ended gracefully. Goodbye!")

        self.refresh_live()
        self.stop_live()
        self.show_shutdown_summary(interrupted=interrupted, error=error)

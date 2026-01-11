from datetime import datetime
from selfbot_discord.services.owo.models import OWOStats, MartingaleStrategy, OWOGameState

class OWOStatsPresenter:
    """Handles formatting of OWO game statistics for display."""

    @staticmethod
    def format_stats(stats: OWOStats, strategy: MartingaleStrategy | None, state: OWOGameState) -> str:
        session_duration = "N/A"
        if stats.session_start:
            end_time = stats.session_end or datetime.now()
            duration = end_time - stats.session_start
            total_seconds = int(duration.total_seconds())
            hours, remainder = divmod(total_seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            session_duration = f"{hours:02d}:{minutes:02d}:{seconds:02d}"

        # Determine status string
        is_active = state.name in ("RUNNING", "COOLDOWN")
        status_icon = "🟢" if is_active else "🔴"
        status = "RUNNING" if is_active else "STOPPED"

        current_bet = f"{strategy.current_bet:,}" if strategy else "0"
        
        # Calculate rates
        win_rate = f"{stats.win_rate:.1f}%"
        profit = f"{stats.net_profit:+,}"

        return (
            f"# 📊 ClaimOWO Session\n"
            f"**Status**: `{status}` {status_icon}\n"
            f"**Duration**: `{session_duration}`\n\n"
            f"### 📈 Performance\n"
            f"- **Games**: `{stats.total_games}`\n"
            f"- **Win Rate**: `{win_rate}` ({stats.total_wins}W / {stats.total_losses}L)\n"
            f"- **Streaks**: `{stats.current_loss_streak}` Current | `{stats.highest_loss_streak}` Max\n\n"
            f"### 💰 Financial\n"
            f"- **Net Profit**: `{profit}` cowoncy\n"
            f"- **Highest Win**: `{stats.highest_win:,}`\n"
            f"- **Current Bet**: `{current_bet}`"
        )

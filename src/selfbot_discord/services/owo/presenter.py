from datetime import datetime
from selfbot_discord.services.owo.models import OWOStats, MartingaleStrategy, OWOGameState
from selfbot_discord.utils.formatting import TextStyler

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

        lines = []
        lines.append(TextStyler.stat_line([("🟢 Status", status), ("⏱️ Duration", session_duration)]))
        lines.append("")
        lines.append(TextStyler.key_value("💰 Net Profit", profit))
        lines.append(TextStyler.stat_line([("📈 Win Rate", win_rate), ("🎲 Games", stats.total_games)]))
        lines.append(TextStyler.stat_line([("✅ Wins", stats.total_wins), ("❌ Losses", stats.total_losses)]))
        lines.append("")
        lines.append(TextStyler.key_value("🏆 Highest Win", f"{stats.highest_win:,}"))
        lines.append(TextStyler.key_value("🔥 Loss Streak", f"{stats.current_loss_streak} (Max: {stats.highest_loss_streak})"))
        
        if strategy:
            lines.append("")
            lines.append(f"**Next Bet**: `{current_bet}`")

        return TextStyler.make_embed(
            title="ClaimOWO Session",
            content="\n".join(lines),
            emoji="📊",
            footer="Hikari OWO Automaton"
        )

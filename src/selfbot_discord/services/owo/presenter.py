from datetime import datetime
from selfbot_discord.services.owo.models import OWOStats, MartingaleStrategy, OWOGameState
from selfbot_discord.utils.formatting import TextStyler

class OWOStatsPresenter:
    """Handles formatting of OWO game statistics for display."""

    @staticmethod
    def format_stats(stats: OWOStats, strategy: MartingaleStrategy | None, state: OWOGameState) -> str:
        # 1. Calculate Duration
        session_duration = "N/A"
        if stats.session_start:
            end_time = stats.session_end or datetime.now()
            duration = end_time - stats.session_start
            total_seconds = int(duration.total_seconds())
            hours, remainder = divmod(total_seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            session_duration = f"{hours:02d}:{minutes:02d}:{seconds:02d}"

        # 2. Determine Status & Profit Color
        is_active = state.name in ("RUNNING", "COOLDOWN")
        status_map = {
            "RUNNING": "🟢 RUNNING",
            "COOLDOWN": "🟡 COOLDOWN",
            "IDLE": "⚪ IDLE",
            "STOPPED": "🔴 STOPPED"
        }
        status_str = status_map.get(state.name, state.name)
        
        profit_int = stats.net_profit
        profit_emoji = "💸" if profit_int < 0 else "💰"
        profit_sign = "+" if profit_int > 0 else ""
        profit_str = f"{profit_sign}{profit_int:,}"

        # 3. Rates
        win_rate = f"{stats.win_rate:.1f}%"
        
        # 4. Build Lines
        lines = []
        
        # Header Stats
        lines.append(f"> **Status**: `{status_str}`")
        lines.append(f"> **Time**: `{session_duration}`")
        lines.append("")
        
        # Financials
        lines.append(f"{profit_emoji} **Net Profit**: `{profit_str}`")
        lines.append(f"📊 **Win Rate**: `{win_rate}`  [ `{stats.total_games}` games ]")
        lines.append("")
        
        # Details (Grid)
        lines.append(f"✅ Wins: `{stats.total_wins}`    ❌ Losses: `{stats.total_losses}`")
        lines.append(f"🏆 High: `{stats.highest_win:,}`    🔥 Streak: `{stats.current_loss_streak}`")
        
        # Prediction
        if strategy and is_active:
            lines.append("")
            lines.append("---")
            next_bet = strategy.current_bet
            next_side = strategy.get_next_side() if strategy else "?"
            lines.append(f"🎲 **Next Bet**: `{next_bet:,}` on `{next_side}`")

        return TextStyler.make_embed(
            title="ClaimOWO Dashboard",
            content="\n".join(lines),
            emoji="🎰",
            footer="Hikari Automation Systems"
        )

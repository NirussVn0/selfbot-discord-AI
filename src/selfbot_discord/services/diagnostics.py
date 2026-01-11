from pathlib import Path
from typing import Optional

class DiagnosticsService:
    """Service for retrieving runtime diagnostics and logs."""

    @staticmethod
    def get_recent_logs(log_dir: Path | str, filename: str = "selfbot.log", limit: int = 10) -> Optional[str]:
        """
        Reads the tail of the log file.
        
        Returns:
            str: Log snippet, empty string if empty, or None if file not found/error.
        """
        path = Path(log_dir) / filename
        if not path.exists():
            return None
            
        try:
            content = path.read_text(encoding="utf-8").splitlines()
            if not content:
                return ""
                
            recent = content[-limit:]
            snippet = "\n".join(recent)
            
            # Cap size if somehow huge
            if len(snippet) > 1900:
                snippet = snippet[-1900:]
                
            return snippet
        except Exception:
            return None

class TextStyler:
    """Helper class for creating premium Discord-like UI using Markdown."""

    @staticmethod
    def make_embed(title: str, content: str, emoji: str = "✨", footer: str | None = None, thumbnail: str | None = None) -> str:
        """
        Creates a 'fake embed' using Blockquotes (`>>>`) and Headers.
        mimics the visual weight of a Discord Embed.
        """
        header_text = f"# {emoji} {title}".strip()
        
        # Ensure content is string
        content = str(content)
        
        # If content has multiple lines, ensure they align well in blockquote
        # Using >>> handles multiline automatically for the rest of the message
        
        body = f">>> {content}"
        
        if footer:
            # Add a separator or just newline
            body += f"\n\n* {footer} *"
            
        return f"{header_text}\n{body}"

    @staticmethod
    def key_value(key: str, value: str | int | float, style: str = "code") -> str:
        """Formats a key-value pair. E.g. **Status**: `Online`"""
        val_str = f"`{value}`" if style == "code" else f"**{value}**"
        return f"**{key}**: {val_str}"

    @staticmethod
    def stat_line(items: list[tuple[str, str | int | float]]) -> str:
        """Creates a single line of stats separated by dots or bars."""
        # e.g. 🟢 Status: Running | ⏱️ Uptime: 2h
        formatted = []
        for icon_key, value in items:
            # icon_key could be "🟢 Status"
            formatted.append(f"**{icon_key}**: `{value}`")
        return " │ ".join(formatted)

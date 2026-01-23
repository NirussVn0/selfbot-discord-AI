class TextStyler:
    """Helper class for creating premium Discord-like UI using Markdown."""

    DISCORD_MAX_LENGTH = 2000

    @staticmethod
    def make_embed(title: str, content: str, emoji: str = "✨", footer: str | None = None, thumbnail: str | None = None) -> str:
        header_text = f"# {emoji} {title}".strip()
        content = str(content)
        body = f">>> {content}"
        if footer:
            body += f"\n\n* {footer} *"
        return f"{header_text}\n{body}"

    @staticmethod
    def key_value(key: str, value: str | int | float, style: str = "code") -> str:
        val_str = f"`{value}`" if style == "code" else f"**{value}**"
        return f"**{key}**: {val_str}"

    @staticmethod
    def stat_line(items: list[tuple[str, str | int | float]]) -> str:
        formatted = [f"**{icon_key}**: `{value}`" for icon_key, value in items]
        return " │ ".join(formatted)

    @staticmethod
    def chunk_message(content: str, max_length: int = 1900) -> list[str]:
        """Split long messages into chunks respecting Discord's limit."""
        if len(content) <= max_length:
            return [content]

        chunks: list[str] = []
        lines = content.split("\n")
        current_chunk = ""

        for line in lines:
            if len(current_chunk) + len(line) + 1 > max_length:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                    current_chunk = ""
                if len(line) > max_length:
                    for i in range(0, len(line), max_length):
                        chunks.append(line[i:i + max_length])
                else:
                    current_chunk = line
            else:
                current_chunk += ("\n" if current_chunk else "") + line

        if current_chunk.strip():
            chunks.append(current_chunk.strip())

        return chunks if chunks else [content[:max_length]]

# Lightweight channel-scoped conversation storage.

from __future__ import annotations

from collections import defaultdict, deque
from typing import Deque, Iterable


class ConversationStore:

    def __init__(self, max_messages: int = 10) -> None:
        self._max_messages = max_messages
        self._messages: dict[int, Deque[str]] = defaultdict(deque)

    def snapshot(self, channel_id: int) -> list[str]:
        # Return the stored conversational history for the channel.

        return list(self._messages.get(channel_id, ()))

    def append(self, channel_id: int, role: str, content: str) -> None:
        # Append a message to the channel history.

        if not content.strip():
            return
        entry = f"{role}: {content.strip()}"
        messages = self._messages[channel_id]
        messages.append(entry)
        while len(messages) > self._max_messages:
            messages.popleft()

    def extend(self, channel_id: int, records: Iterable[tuple[str, str]]) -> None:
        # Bulk append multiple messages.

        for role, content in records:
            self.append(channel_id, role, content)

    def clear(self, channel_id: int) -> None:
        # Clear the stored history for the channel.

        self._messages.pop(channel_id, None)

from __future__ import annotations

import asyncio
import logging
from functools import partial
from pathlib import Path
from typing import Iterable, Sequence

import google.generativeai as genai

from selfbot_discord.config.models import AIConfig

logger = logging.getLogger(__name__)

PERSONA_PROMPTS: dict[str, str] = {
    "gen_z": (
        "You are a playful Gen Z friend chatting on Discord. Keep responses short, witty, and full of slang, emojis, "
        "and casual energy. Use lowercase where it feels natural and weave in contemporary internet culture. "
        "Feel free to drop fragments or quick reactions, but stay supportive and kind."
    ),
    "casual": (
        "You are a relaxed Discord buddy. Respond in a warm, easygoing tone, a bit playful but not over the top. "
        "Use plain language, occasional emojis, and keep answers brief."
    ),
    "professional": (
        "You are a knowledgeable professional speaking in a considerate tone. Stay concise, helpful, and respectful "
        "while keeping the message approachable."
    ),
}


class GeminiAIService:

    def __init__(self, config: AIConfig, api_key: str) -> None:
        self._config = config
        self._model_name = config.model
        self._persona_prompt = PERSONA_PROMPTS.get(config.persona, PERSONA_PROMPTS["gen_z"])
        self._system_prompt = self._load_system_prompt(config.system_prompt_path)
        genai.configure(api_key=api_key)
        self._model = genai.GenerativeModel(self._model_name)

    def _load_system_prompt(self, prompt_path: Path | None) -> str:
        if prompt_path is None:
            return ""
        try:
            path = Path(prompt_path).expanduser()
            return path.read_text(encoding="utf-8").strip()
        except FileNotFoundError:
            logger.warning("System prompt path %s not found; proceeding without it.", prompt_path)
        except OSError as exc:
            logger.warning("Unable to read system prompt at %s: %s", prompt_path, exc)
        return ""

    async def generate_reply(
        self,
        *,
        author_name: str,
        message_content: str,
        conversation: Sequence[str],
    ) -> str:
        if not message_content.strip():
            raise ValueError("Cannot produce a reply for empty content.")

        return await asyncio.to_thread(
            partial(
                self._invoke_model,
                author_name=author_name,
                message_content=message_content,
                conversation=conversation,
            )
        )

    def _build_prompt(
        self,
        *,
        author_name: str,
        message_content: str,
        conversation: Iterable[str],
    ) -> list[dict[str, str]]:

        conversation_text = "\n".join(conversation)
        segments = [
            self._system_prompt,
            self._persona_prompt,
            "Context so far:",
            conversation_text or "[No prior context]",
            f"{author_name} said:",
            message_content,
            "Craft a short reply (<=3 sentences) that fits the persona and stays human.",
        ]
        content = "\n".join(segment for segment in segments if segment)
        return [{"role": "user", "parts": [{"text": content}]}]

    def _invoke_model(
        self,
        *,
        author_name: str,
        message_content: str,
        conversation: Sequence[str],
    ) -> str:
        contents = self._build_prompt(
            author_name=author_name,
            message_content=message_content,
            conversation=conversation,
        )
        generation_config = genai.types.GenerationConfig(
            temperature=self._config.temperature,
            top_p=self._config.top_p,
            max_output_tokens=self._config.max_output_tokens,
        )
        try:
            response = self._model.generate_content(contents=contents, generation_config=generation_config)
        except Exception as exc:  # pragma: no cover - network errors are runtime concerns
            logger.exception("Gemini generation failed: %s", exc)
            raise
        text = (response.text or "").strip()
        if not text:
            raise RuntimeError("Gemini returned an empty response.")
        return text

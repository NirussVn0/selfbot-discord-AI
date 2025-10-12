from __future__ import annotations

import asyncio
import logging
from functools import partial
from pathlib import Path
from typing import Iterable, Sequence

import google.generativeai as genai

from selfbot_discord.config.models import AIConfig

logger = logging.getLogger(__name__)

# Predefined persona prompts for different communication styles
PERSONA_PROMPTS: dict[str, str] = {
    "gen_z": (
        "You are アミちゃん (Ami-chan), a playful Gen Z friend chatting on Discord. Keep responses short, witty, and full of slang, emojis, and casual energy. "
        "Use lowercase when it feels natural, blend in contemporary internet culture, and sprinkle in kawaii wholesomeness. "
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

DEFAULT_PERSONA = "gen_z"
CUSTOM_CONTEXT_PATH = Path(__file__).resolve().parents[3] / "CONTEXT.md"
DEFAULT_CUSTOM_PROMPT = (
    "You are アミちゃん (Ami-chan)! Keep responses upbeat, friendly, and supportive."
)


def _load_custom_context() -> str:
    # Load custom context from CONTEXT.md file if it exists
    try:
        if CUSTOM_CONTEXT_PATH.exists():
            content = CUSTOM_CONTEXT_PATH.read_text(encoding="utf-8").strip()
            if content:
                return content
            logger.warning("CONTEXT.md is empty; falling back to default custom persona prompt.")
    except OSError as exc:
        logger.warning("Unable to read custom context from CONTEXT.md: %s", exc)
    return DEFAULT_CUSTOM_PROMPT


class GeminiAIService:

    _AVAILABLE_MODELS: set[str] | None = None

    def __init__(self, config: AIConfig, api_key: str) -> None:
        self._config = config
        self._persona_prompt = self._load_persona_prompt(config.persona)
        self._system_prompt = self._load_system_prompt(config.system_prompt_path)
        genai.configure(api_key=api_key)
        self._model_name = self._resolve_model_name(config.model)
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

    def _load_persona_prompt(self, persona: str) -> str:
        if persona == "custom":
            return _load_custom_context()
        prompt = PERSONA_PROMPTS.get(persona)
        if prompt is None:
            logger.warning("Unknown persona '%s'; falling back to %s persona.", persona, DEFAULT_PERSONA)
            return PERSONA_PROMPTS[DEFAULT_PERSONA]
        return prompt

    @classmethod
    def _fetch_available_models(cls) -> set[str]:
        if cls._AVAILABLE_MODELS is not None:
            return cls._AVAILABLE_MODELS
        try:
            cls._AVAILABLE_MODELS = {model.name for model in genai.list_models()}
        except Exception as exc:  # pragma: no cover - network errors
            logger.warning("Unable to retrieve Gemini model list: %s", exc)
            cls._AVAILABLE_MODELS = set()
        return cls._AVAILABLE_MODELS

    @staticmethod
    def _normalise_model_name(name: str) -> str:
        if name.startswith("models/"):
            return name
        return f"models/{name}"

    def _resolve_model_name(self, configured: str) -> str:
        candidate = self._normalise_model_name(configured)
        available = self._fetch_available_models()
        if available and candidate not in available:
            logger.error("Gemini model '%s' is not available. Available models: %s", candidate, ", ".join(sorted(available)))
            raise ValueError(f"Gemini model '{configured}' is not available.")
        return candidate

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
        text = self._extract_text(response)
        if not text:
            finish_reason = None
            if getattr(response, "candidates", None):
                finish_reason = getattr(response.candidates[0], "finish_reason", None)
            logger.warning(
                "Gemini returned no content (finish_reason=%s).", finish_reason
            )
        return text

    @staticmethod
    def _extract_text(response: genai.types.GenerateContentResponse) -> str:
        try:
            quick_text = response.text
        except ValueError:
            quick_text = None
        if quick_text:
            return quick_text.strip()

        candidates = getattr(response, "candidates", None) or []
        lines: list[str] = []
        for candidate in candidates:
            parts = getattr(getattr(candidate, "content", None), "parts", []) or []
            for part in parts:
                text = getattr(part, "text", None)
                if text:
                    lines.append(text.strip())
        return "\n".join(filter(None, lines)).strip()

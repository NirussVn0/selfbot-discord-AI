# Pydantic configuration models for the Discord self-bot.

from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import AnyUrl, BaseModel, Field, HttpUrl, PositiveInt, field_validator


class LoggingConfig(BaseModel):
    # Settings controlling structured logging output.

    level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    json_format: bool = Field(default=True, description="Emit logs in JSON format when True.")
    log_dir: Path | None = Field(default=Path("logs"), description="Directory where log files are stored.")
    rotation: str = Field(default="1 week", description="Log rotation frequency e.g. '1 MB', '1 week'.")


class SecretsConfig(BaseModel):
    # Environment variable keys for sensitive secrets.

    discord_token: str = Field(default="DISCORD_USER_TOKEN", description="Environment variable for the Discord user token.")
    gemini_api_key: str = Field(default="GOOGLE_GEMINI_API_KEY", description="Environment variable for the Gemini API key.")


class WhitelistConfig(BaseModel):
    # Whitelist configuration controlling permitted guilds and channels.

    enabled: bool = Field(default=True, description="Master switch enabling whitelist enforcement.")
    admin_ids: list[int] = Field(default_factory=list, description="User IDs considered administrators.")
    user_ids: list[int] = Field(default_factory=list, description="User IDs allowed to trigger AI responses.")
    guild_ids: list[int] = Field(default_factory=list, description="Guild IDs where the bot may respond.")
    channel_ids: list[int] = Field(default_factory=list, description="Channel IDs where the bot may respond.")
    allow_direct_messages: bool = Field(default=False, description="Whether to respond to direct messages.")
    reload_interval_seconds: PositiveInt = Field(default=300, description="Interval for checking whitelist updates.")


class DiscordConfig(BaseModel):
    # Discord behavior configuration.

    command_prefix: str = Field(default="h!", description="Command prefix for bot commands.")
    presence_message: str = Field(default="Staying lowkey", description="Custom status message for the self-bot.")
    auto_reply_probability: float = Field(default=0.0, description="Probability for auto-reply mode when enabled.")
    auto_reply_cooldown_seconds: PositiveInt = Field(default=45, description="Cooldown between auto replies per channel.")
    allow_thread_messages: bool = Field(default=True, description="Whether to respond within threads.")
    mention_required: bool = Field(default=True, description="Require an explicit mention before replying.")
    service_url: HttpUrl | None = Field(default=None, description="Optional webhook or metrics endpoint.")

    @field_validator("auto_reply_probability")
    @classmethod
    def validate_probability(cls, value: float) -> float:
        # Ensure the probability is within [0, 1].
        if not 0.0 <= value <= 1.0:
            msg = "auto_reply_probability must be between 0 and 1 inclusive."
            raise ValueError(msg)
        return value


class AIConfig(BaseModel):
    # Google Gemini AI service configuration.

    model: str = Field(default="gemini-pro", description="Gemini model identifier.")
    temperature: float = Field(default=0.8, description="Sampling temperature for responses.")
    top_p: float = Field(default=0.95, description="Top-P nucleus sampling parameter.")
    max_output_tokens: PositiveInt = Field(default=1024, description="Maximum number of tokens per response.")
    system_prompt_path: Path | None = Field(default=None, description="Optional path to a custom system prompt file.")
    persona: Literal["gen_z", "casual", "professional", "custom"] = Field(
        default="gen_z",
        description="Default conversational persona.",
    )
    empty_reply_fallback: str | None = Field(
        default="Sorry, I couldn't think of a response right now.",
        description="Message sent when the AI yields an empty reply; set blank to disable.",
    )

    @field_validator("temperature")
    @classmethod
    def validate_temperature(cls, value: float) -> float:
        # Ensure temperature is within permitted bounds.
        if not 0 <= value <= 2:
            msg = "temperature must be between 0 and 2 inclusive."
            raise ValueError(msg)
        return value

    @field_validator("top_p")
    @classmethod
    def validate_top_p(cls, value: float) -> float:
        # Ensure top_p is within permitted bounds.
        if not 0 <= value <= 1:
            msg = "top_p must be between 0 and 1 inclusive."
            raise ValueError(msg)
        return value


class RateLimitConfig(BaseModel):
    # Rate limiting and message queue configuration.

    messages_per_minute: PositiveInt = Field(default=20, description="Maximum messages sent per minute.")
    queue_size: PositiveInt = Field(default=50, description="Maximum size of the outbound message queue.")
    burst_window_seconds: PositiveInt = Field(default=10, description="Window used for burst throttling checks.")


class CacheConfig(BaseModel):
    # Distributed cache configuration.

    redis_url: AnyUrl = Field(default="redis://redis:6379/0", description="Connection URL for Redis cache.")
    namespace: str = Field(default="selfbot_discord", description="Namespace prefix for cache keys.")
    default_ttl_seconds: PositiveInt = Field(default=300, description="Default TTL for cached whitelist entries.")


class AppConfig(BaseModel):
    # Aggregate application configuration.

    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    secrets: SecretsConfig = Field(default_factory=SecretsConfig)
    whitelist: WhitelistConfig = Field(default_factory=WhitelistConfig)
    discord: DiscordConfig = Field(default_factory=DiscordConfig)
    ai: AIConfig = Field(default_factory=AIConfig)
    rate_limit: RateLimitConfig = Field(default_factory=RateLimitConfig)
    cache: CacheConfig = Field(default_factory=CacheConfig)

"""Content feature settings mixin (TTI / TTV providers and credentials)."""

from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class ContentSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "AI Matic - Personalized Content Generation"

    # Active provider selection
    active_tti_provider: Literal["openai", "gemini", "titan"] = "openai"
    active_ttv_provider: Literal["sora", "veo", "nova_reel"] = "sora"

    # OpenAI (ChatGPT / DALL-E / Sora)
    openai_api_key: str = ""
    openai_image_model: str = "dall-e-3"
    openai_video_model: str = "sora-2-pro"

    # Google
    google_api_key: str = ""
    google_image_model: str = "gemini-2.0-flash-preview-image-generation"
    google_video_model: str = "veo-3.1-generate-preview"

    # AWS
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""
    aws_region: str = "us-east-1"
    aws_titan_model_id: str = "amazon.titan-image-generator-v2:0"
    aws_nova_reel_model_id: str = "amazon.nova-reel-v1:0"

    # Provider timeouts (seconds)
    video_poll_interval_seconds: float = 5.0
    video_poll_timeout_seconds: int = Field(default=600, ge=60)

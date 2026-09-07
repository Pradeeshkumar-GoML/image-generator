"""Consolidated application settings combining base, model gateway, and content configurations."""

import os
from functools import lru_cache
from typing import Literal

from pydantic import AliasChoices, Field
from pydantic_settings import SettingsConfigDict

from app.config.base_settings import BaseAppSettings
from app.config.content.settings import ContentSettings
from app.config.model_gateway_settings import ModelGatewaySettings


class Settings(BaseAppSettings, ModelGatewaySettings, ContentSettings):
    """Merged application settings for AI Matic Content Generation."""

    # Active provider selection with aliases for .env compatibility
    active_tti_provider: Literal["openai", "gemini", "titan"] = Field(
        default="openai",
        validation_alias=AliasChoices("ACTIVE_TTI_PROVIDER", "TTI_MODEL", "active_tti_provider"),
    )
    active_ttv_provider: Literal["sora", "veo", "nova_reel"] = Field(
        default="sora",
        validation_alias=AliasChoices("ACTIVE_TTV_PROVIDER", "TTV_MODEL", "active_ttv_provider"),
    )

    model_config = SettingsConfigDict(
        env_file=".env" if not os.environ.get("AWS_LAMBDA_FUNCTION_NAME") else None,
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached application settings singleton."""
    return Settings()


settings: Settings = get_settings()

"""Factory for text-to-image provider clients (lazy option-pack imports).

Supported provider keys:
  openai   - OpenAI DALL-E 3 / GPT Image (ChatGPT)
  gemini   - Google Gemini / Imagen
  titan    - Amazon Titan Image Generator v2
"""

from typing import Type

from app.adapters.image_gen.base import ImageGenerationProvider
from app.config.settings import Settings, get_settings
from app.core.exceptions.content import ProviderNotFoundError

_instances: dict[str, ImageGenerationProvider] = {}


def _load_provider_class(provider_key: str) -> Type[ImageGenerationProvider]:
    if provider_key == "openai":
        from app.adapters.image_gen.openai.openai_gpt_image import OpenAIGPTImageClient

        return OpenAIGPTImageClient
    if provider_key == "gemini":
        from app.adapters.image_gen.google_cloud.google_gemini_client import (
            GoogleGeminiImageClient,
        )

        return GoogleGeminiImageClient
    if provider_key == "titan":
        from app.adapters.image_gen.aws.titan_client import TitanImageClient

        return TitanImageClient
    raise ProviderNotFoundError(
        f"Text-to-image provider '{provider_key}' is not registered",
        error_code="provider_not_found",
    )


def get_image_provider(settings: Settings | None = None) -> ImageGenerationProvider:
    """Return the configured text-to-image provider client."""
    cfg = settings or get_settings()
    provider_key = cfg.active_tti_provider

    if provider_key not in _instances:
        try:
            cls = _load_provider_class(provider_key)
        except ImportError as exc:
            raise ProviderNotFoundError(
                f"Text-to-image provider '{provider_key}' is not installed",
                error_code="provider_not_found",
            ) from exc
        _instances[provider_key] = cls(cfg)

    return _instances[provider_key]


def reset_image_provider_cache() -> None:
    """Clear cached provider instances (useful for testing)."""
    _instances.clear()

"""Factory for text-to-video provider clients (lazy option-pack imports)."""

from typing import Type

from app.adapters.video_gen.base import VideoGenerationProvider
from app.config.settings import Settings, get_settings
from app.core.exceptions.content import ProviderNotFoundError

_instances: dict[str, VideoGenerationProvider] = {}


def _load_provider_class(provider_key: str) -> Type[VideoGenerationProvider]:
    if provider_key == "nova_reel":
        from app.adapters.video_gen.aws.nova_reel_client import NovaReelClient

        return NovaReelClient
    if provider_key == "veo":
        from app.adapters.video_gen.google_cloud.veo_client import VeoClient

        return VeoClient
    if provider_key == "sora":
        from app.adapters.video_gen.openai.sora_client import SoraClient

        return SoraClient
    raise ProviderNotFoundError(
        f"Text-to-video provider '{provider_key}' is not registered",
        error_code="provider_not_found",
    )


def get_video_provider(settings: Settings | None = None) -> VideoGenerationProvider:
    """Return the configured text-to-video provider client."""
    cfg = settings or get_settings()
    provider_key = cfg.active_ttv_provider

    if provider_key not in _instances:
        try:
            cls = _load_provider_class(provider_key)
        except ImportError as exc:
            raise ProviderNotFoundError(
                f"Text-to-video provider '{provider_key}' is not installed",
                error_code="provider_not_found",
            ) from exc
        _instances[provider_key] = cls(cfg)

    return _instances[provider_key]


def reset_video_provider_cache() -> None:
    """Clear cached provider instances (useful for testing)."""
    _instances.clear()

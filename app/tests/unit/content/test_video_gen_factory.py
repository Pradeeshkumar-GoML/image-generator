"""Unit tests for video generation factory."""

import pytest

from app.adapters.video_gen.factory import get_video_provider
from app.config.settings import Settings
from app.core.exceptions.content import ProviderNotFoundError


def test_factory_returns_nova_reel_provider(settings_titan):
    provider = get_video_provider(settings_titan)
    assert provider.__class__.__name__ == "NovaReelClient"


def test_factory_returns_sora_provider(settings_openai):
    provider = get_video_provider(settings_openai)
    assert provider.__class__.__name__ == "SoraClient"


def test_factory_returns_veo_provider():
    settings = Settings(active_ttv_provider="veo", google_api_key="test-google-key")
    provider = get_video_provider(settings)
    assert provider.__class__.__name__ == "VeoClient"


def test_factory_raises_for_unknown_provider():
    settings = Settings(active_ttv_provider="nova_reel")
    settings.active_ttv_provider = "unknown"  # type: ignore[misc]

    with pytest.raises(ProviderNotFoundError):
        get_video_provider(settings)

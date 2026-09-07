"""Unit tests for image generation factory."""

import pytest

from app.adapters.image_gen.factory import get_image_provider
from app.config.settings import Settings
from app.core.exceptions.content import ProviderNotFoundError


def test_factory_returns_titan_provider(settings_titan):
    provider = get_image_provider(settings_titan)
    assert provider.__class__.__name__ == "TitanImageClient"


def test_factory_returns_openai_provider(settings_openai):
    provider = get_image_provider(settings_openai)
    assert provider.__class__.__name__ == "OpenAIGPTImageClient"


def test_factory_returns_gemini_provider():
    settings = Settings(active_tti_provider="gemini", google_api_key="test-google-key")
    provider = get_image_provider(settings)
    assert provider.__class__.__name__ == "GoogleGeminiImageClient"


def test_factory_raises_for_unknown_provider():
    settings = Settings(active_tti_provider="titan")
    settings.active_tti_provider = "unknown"  # type: ignore[misc]

    with pytest.raises(ProviderNotFoundError):
        get_image_provider(settings)

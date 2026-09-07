"""Content unit-test fixtures."""

import pytest

from app.adapters.image_gen.base import ImageGenerationProvider
from app.adapters.image_gen.factory import reset_image_provider_cache
from app.adapters.video_gen.base import VideoGenerationProvider
from app.adapters.video_gen.factory import reset_video_provider_cache
from app.config.settings import Settings


class FakeImageProvider(ImageGenerationProvider):
    async def generate(self, text: str) -> bytes:
        return b"fake-image-bytes"


class FakeVideoProvider(VideoGenerationProvider):
    async def generate(self, text: str) -> bytes:
        return b"fake-video-bytes"


@pytest.fixture(autouse=True)
def clear_provider_caches():
    reset_image_provider_cache()
    reset_video_provider_cache()
    yield
    reset_image_provider_cache()
    reset_video_provider_cache()


@pytest.fixture
def settings_titan() -> Settings:
    return Settings(active_tti_provider="titan", active_ttv_provider="nova_reel")


@pytest.fixture
def settings_openai() -> Settings:
    return Settings(
        active_tti_provider="openai",
        active_ttv_provider="sora",
        openai_api_key="test-openai-key",
    )


@pytest.fixture
def fake_image_provider() -> FakeImageProvider:
    return FakeImageProvider()


@pytest.fixture
def fake_video_provider() -> FakeVideoProvider:
    return FakeVideoProvider()

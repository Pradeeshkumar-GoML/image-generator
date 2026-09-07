"""Unit tests for video generation service."""

from unittest.mock import AsyncMock, patch

import pytest

from app.config.settings import Settings
from app.core.exceptions.content import ValidationError
from app.services.content.video_generation_service import VideoGenerationService


@pytest.mark.asyncio
async def test_generate_video_calls_factory_provider(fake_video_provider):
    settings = Settings(active_ttv_provider="nova_reel")
    service = VideoGenerationService(settings)

    with patch(
        "app.services.content.video_generation_service.get_video_provider",
        return_value=fake_video_provider,
    ) as mock_factory:
        result = await service.generate_video("Ocean waves at sunset")

    mock_factory.assert_called_once_with(settings)
    assert result == b"fake-video-bytes"


@pytest.mark.asyncio
async def test_generate_video_rejects_empty_prompt():
    service = VideoGenerationService(Settings(active_ttv_provider="sora"))

    with pytest.raises(ValidationError, match="must not be empty"):
        await service.generate_video("")


@pytest.mark.asyncio
async def test_generate_video_propagates_provider_errors():
    settings = Settings(active_ttv_provider="veo")
    service = VideoGenerationService(settings)

    mock_provider = AsyncMock()
    mock_provider.generate.side_effect = RuntimeError("upstream failure")

    with patch(
        "app.services.content.video_generation_service.get_video_provider",
        return_value=mock_provider,
    ):
        from app.core.exceptions.content import ContentGenerationError

        with pytest.raises(ContentGenerationError):
            await service.generate_video("valid prompt")

"""Unit tests for image generation service."""

from unittest.mock import AsyncMock, patch

import pytest

from app.config.settings import Settings
from app.core.exceptions.content import ValidationError
from app.services.content.image_generation_service import ImageGenerationService


@pytest.mark.asyncio
async def test_generate_image_calls_factory_provider(fake_image_provider):
    settings = Settings(active_tti_provider="titan")
    service = ImageGenerationService(settings)

    with patch(
        "app.services.content.image_generation_service.get_image_provider",
        return_value=fake_image_provider,
    ) as mock_factory:
        result = await service.generate_image("A red apple on a table")

    mock_factory.assert_called_once_with(settings)
    assert result == b"fake-image-bytes"


@pytest.mark.asyncio
async def test_generate_image_rejects_empty_prompt():
    service = ImageGenerationService(Settings(active_tti_provider="titan"))

    with pytest.raises(ValidationError, match="must not be empty"):
        await service.generate_image("   ")


@pytest.mark.asyncio
async def test_generate_image_propagates_provider_errors():
    settings = Settings(active_tti_provider="openai")
    service = ImageGenerationService(settings)

    mock_provider = AsyncMock()
    mock_provider.generate.side_effect = RuntimeError("upstream failure")

    with patch(
        "app.services.content.image_generation_service.get_image_provider",
        return_value=mock_provider,
    ):
        from app.core.exceptions.content import ContentGenerationError

        with pytest.raises(ContentGenerationError):
            await service.generate_image("valid prompt")

"""Image generation orchestration service."""

import logging

from app.adapters.image_gen.factory import get_image_provider
from app.core.exceptions.content import AIMaticError, ContentGenerationError, ValidationError
from app.config.settings import Settings

logger = logging.getLogger(__name__)


class ImageGenerationService:
    """Coordinates text-to-image generation via the provider factory."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    async def generate_image(self, text: str) -> bytes:
        prompt = text.strip()
        if not prompt:
            raise ValidationError("Text prompt must not be empty")

        logger.info(
            "Generating image with provider: %s", self._settings.active_tti_provider
        )
        try:
            provider = get_image_provider(self._settings)
            return await provider.generate(prompt)
        except (ValidationError, AIMaticError):
            raise
        except Exception as exc:
            logger.exception("Image generation failed")
            raise ContentGenerationError(f"Image generation failed: {exc}") from exc

"""Video generation orchestration service."""

import logging

from app.adapters.video_gen.factory import get_video_provider
from app.core.exceptions.content import AIMaticError, ContentGenerationError, ValidationError
from app.config.settings import Settings

logger = logging.getLogger(__name__)


class VideoGenerationService:
    """Coordinates text-to-video generation via the provider factory."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    async def generate_video(self, text: str) -> bytes:
        prompt = text.strip()
        if not prompt:
            raise ValidationError("Text prompt must not be empty")

        logger.info(
            "Generating video with provider: %s", self._settings.active_ttv_provider
        )
        try:
            provider = get_video_provider(self._settings)
            return await provider.generate(prompt)
        except (ValidationError, AIMaticError):
            raise
        except Exception as exc:
            logger.exception("Video generation failed")
            raise ContentGenerationError(f"Video generation failed: {exc}") from exc

"""Google Veo text-to-video client."""

import logging
from app.adapters.common import run_sync_in_executor, wrap_provider_error
from app.adapters.video_gen.base import VideoGenerationProvider
from app.config.settings import Settings

logger = logging.getLogger(__name__)


class VeoClient(VideoGenerationProvider):
    """Text-to-video using Google Veo."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def _invoke(self, text: str) -> bytes:
        # Placeholder for Veo video API integration
        raise NotImplementedError("Google Veo integration requires active Google Vertex AI video quota.")

    async def generate(self, text: str) -> bytes:
        try:
            return await run_sync_in_executor(self._invoke, text)
        except Exception as exc:
            raise wrap_provider_error("veo", exc) from exc

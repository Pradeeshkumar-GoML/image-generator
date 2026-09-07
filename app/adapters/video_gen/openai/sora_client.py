"""OpenAI Sora text-to-video client."""

import logging
from app.adapters.common import run_sync_in_executor, wrap_provider_error
from app.adapters.video_gen.base import VideoGenerationProvider
from app.config.settings import Settings

logger = logging.getLogger(__name__)


class SoraClient(VideoGenerationProvider):
    """Text-to-video using OpenAI Sora."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def _invoke(self, text: str) -> bytes:
        raise NotImplementedError("OpenAI Sora API integration requires active Sora enterprise API access.")

    async def generate(self, text: str) -> bytes:
        try:
            return await run_sync_in_executor(self._invoke, text)
        except Exception as exc:
            raise wrap_provider_error("sora", exc) from exc

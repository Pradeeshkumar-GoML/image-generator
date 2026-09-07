"""Base interface for text-to-video providers."""

from abc import ABC, abstractmethod


class VideoGenerationProvider(ABC):
    """Unified interface for all text-to-video provider clients."""

    @abstractmethod
    async def generate(self, text: str) -> bytes:
        """Generate a video from a text prompt and return raw video bytes."""
        raise NotImplementedError

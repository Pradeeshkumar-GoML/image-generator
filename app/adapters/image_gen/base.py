"""Base interface for text-to-image providers."""

from abc import ABC, abstractmethod


class ImageGenerationProvider(ABC):
    """Unified interface for all text-to-image provider clients."""

    @abstractmethod
    async def generate(self, text: str) -> bytes:
        """Generate an image from a text prompt and return raw image bytes."""
        raise NotImplementedError

"""Base classes for custom pipeline components."""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Self

if TYPE_CHECKING:
    from app.adapters.video_gen.custom_video_pipeline.config import CustomPipelineConfig


class PipelineComponent(ABC):
    """Common lifecycle for loadable pipeline modules."""

    def __init__(self, config: "CustomPipelineConfig") -> None:
        self._config = config
        self._is_loaded = False

    @property
    def is_loaded(self) -> bool:
        return self._is_loaded

    @abstractmethod
    def load(self) -> Self:
        """Load model weights and move to the configured device."""
        raise NotImplementedError

    @abstractmethod
    def unload(self) -> None:
        """Release model weights from memory."""
        raise NotImplementedError

    def _require_loaded(self) -> None:
        if not self._is_loaded:
            raise RuntimeError(f"{self.__class__.__name__} is not loaded. Call load() first.")

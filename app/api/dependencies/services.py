from functools import lru_cache

from app.config.settings import Settings, get_settings
from app.services.content.image_generation_service import ImageGenerationService
from app.services.content.video_generation_service import VideoGenerationService


@lru_cache
def get_image_generation_service() -> ImageGenerationService:
    return ImageGenerationService(get_settings())


@lru_cache
def get_video_generation_service() -> VideoGenerationService:
    return VideoGenerationService(get_settings())


def get_app_settings() -> Settings:
    return get_settings()

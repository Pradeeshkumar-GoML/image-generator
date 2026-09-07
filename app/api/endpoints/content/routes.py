"""Content feature HTTP routes (TTI / TTV)."""

from fastapi import APIRouter, Depends, Response

from app.api.dependencies.services import (
    get_image_generation_service,
    get_video_generation_service,
)
from app.api.schemas.content import TextToImageRequest, TextToVideoRequest
from app.services.content.image_generation_service import ImageGenerationService
from app.services.content.video_generation_service import VideoGenerationService

router = APIRouter()


@router.post(
    "/text-to-image",
    summary="Generate image from text",
    response_class=Response,
    responses={
        200: {
            "content": {"image/png": {}},
            "description": "Generated PNG image bytes",
        }
    },
)
async def text_to_image(
    request: TextToImageRequest,
    service: ImageGenerationService = Depends(get_image_generation_service),
) -> Response:
    image_bytes = await service.generate_image(request.text)
    return Response(content=image_bytes, media_type="image/png")


@router.post(
    "/text-to-video",
    summary="Generate video from text",
    response_class=Response,
    responses={
        200: {
            "content": {"video/mp4": {}},
            "description": "Generated MP4 video bytes",
        }
    },
)
async def text_to_video(
    request: TextToVideoRequest,
    service: VideoGenerationService = Depends(get_video_generation_service),
) -> Response:
    video_bytes = await service.generate_video(request.text)
    return Response(content=video_bytes, media_type="video/mp4")

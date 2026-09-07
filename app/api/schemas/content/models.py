"""Request and response schemas for content generation endpoints."""

from pydantic import BaseModel, Field


class TextToImageRequest(BaseModel):
    """Input schema for text-to-image generation."""

    text: str = Field(
        ...,
        min_length=1,
        max_length=4000,
        description="Prompt describing the image to generate",
    )


class TextToVideoRequest(BaseModel):
    """Input schema for text-to-video generation."""

    text: str = Field(
        ...,
        min_length=1,
        max_length=4000,
        description="Prompt describing the video to generate",
    )

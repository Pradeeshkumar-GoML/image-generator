"""Google Gemini / Imagen client."""

import logging
from app.adapters.common import run_sync_in_executor, wrap_provider_error
from app.adapters.image_gen.base import ImageGenerationProvider
from app.config.settings import Settings

logger = logging.getLogger(__name__)


class GoogleGeminiImageClient(ImageGenerationProvider):
    """Text-to-image provider using Google Gemini / Imagen."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._api_key = settings.google_api_key
        self._model = settings.google_image_model or "imagen-3.0-generate-002"

    def _invoke(self, text: str) -> bytes:
        try:
            from google import genai
            client = genai.Client(api_key=self._api_key or None)
            # Use imagen-3.0 if preview model name passed
            model_name = self._model
            if "gemini" in model_name:
                model_name = "imagen-3.0-generate-002"
            result = client.models.generate_images(
                model=model_name,
                prompt=text,
                config=dict(number_of_images=1, output_mime_type="image/png"),
            )
            if not result.generated_images:
                raise ValueError("Google GenAI returned no images")
            return result.generated_images[0].image.image_bytes
        except Exception as exc:
            raise ValueError(f"Google GenAI error: {exc}") from exc

    async def generate(self, text: str) -> bytes:
        try:
            return await run_sync_in_executor(self._invoke, text)
        except Exception as exc:
            raise wrap_provider_error("gemini", exc) from exc

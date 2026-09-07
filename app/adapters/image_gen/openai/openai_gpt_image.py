"""OpenAI DALL-E / GPT-Image client.

Supports:
  - dall-e-3     (DALL-E 3 image generation)
  - gpt-image-1  (GPT Image generation)
  - chatgpt-image-latest
  - dall-e-2
"""

import base64
import logging
from typing import Any

import httpx
from openai import OpenAI

from app.adapters.common import run_sync_in_executor, wrap_provider_error
from app.adapters.image_gen.base import ImageGenerationProvider
from app.config.settings import Settings

logger = logging.getLogger(__name__)


class OpenAIGPTImageClient(ImageGenerationProvider):
    """Text-to-image provider using OpenAI image generation API."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._client = OpenAI(api_key=settings.openai_api_key or None)
        self._model = settings.openai_image_model or "gpt-image-1"

    def _build_kwargs(self, model: str, prompt: str) -> dict[str, Any]:
        kwargs: dict[str, Any] = {
            "model": model,
            "prompt": prompt,
            "n": 1,
        }
        if "dall-e" in model.lower():
            kwargs["size"] = "1024x1024"
            if "dall-e-3" in model.lower():
                kwargs["quality"] = "standard"
            kwargs["response_format"] = "b64_json"
        return kwargs

    def _invoke(self, text: str) -> bytes:
        candidates = [self._model]
        for alt in ["gpt-image-1", "dall-e-3", "chatgpt-image-latest"]:
            if alt not in candidates:
                candidates.append(alt)

        last_err: Exception | None = None
        for model_name in candidates:
            try:
                logger.info("Generating image with OpenAI model: %s", model_name)
                kwargs = self._build_kwargs(model_name, text)
                response = self._client.images.generate(**kwargs)

                if not response.data:
                    raise ValueError(f"OpenAI returned no images for model {model_name}")

                item = response.data[0]

                # Prefer embedded base64
                b64 = getattr(item, "b64_json", None)
                if b64:
                    return base64.b64decode(b64)

                # Fall back to URL download
                url = getattr(item, "url", None)
                if url:
                    logger.info("Downloading image from OpenAI URL: %s...", url[:40])
                    with httpx.Client(timeout=60.0) as http_client:
                        img_resp = http_client.get(url)
                        img_resp.raise_for_status()
                        return img_resp.content

                raise ValueError("OpenAI response contained neither b64_json nor url")
            except Exception as exc:
                err_msg = str(exc)
                logger.warning("OpenAI model %s failed: %s", model_name, err_msg)
                last_err = exc
                # If model does not exist or parameter invalid, try next candidate
                if "does not exist" in err_msg or "unknown_parameter" in err_msg or "invalid_value" in err_msg:
                    continue
                # For authentication, credit balance, or rate limits, re-raise directly
                raise

        raise last_err or RuntimeError("All OpenAI image generation models failed")

    async def generate(self, text: str) -> bytes:
        try:
            return await run_sync_in_executor(self._invoke, text)
        except Exception as exc:
            raise wrap_provider_error("openai", exc) from exc

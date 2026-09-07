"""Amazon Titan Image Generator client via AWS Bedrock."""

import json
import logging

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from app.adapters.common import decode_base64_payload, run_sync_in_executor, wrap_provider_error
from app.adapters.image_gen.base import ImageGenerationProvider
from app.config.settings import Settings

logger = logging.getLogger(__name__)


class TitanImageClient(ImageGenerationProvider):
    """Text-to-image using Amazon Titan Image Generator on Bedrock."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._client = boto3.client(
            "bedrock-runtime",
            region_name=settings.aws_region,
            aws_access_key_id=settings.aws_access_key_id or None,
            aws_secret_access_key=settings.aws_secret_access_key or None,
        )

    def _invoke(self, text: str) -> bytes:
        body = {
            "taskType": "TEXT_IMAGE",
            "textToImageParams": {"text": text},
            "imageGenerationConfig": {
                "numberOfImages": 1,
                "quality": "standard",
                "height": 1024,
                "width": 1024,
                "cfgScale": 8.0,
            },
        }
        response = self._client.invoke_model(
            modelId=self._settings.aws_titan_model_id,
            body=json.dumps(body),
            contentType="application/json",
            accept="application/json",
        )
        payload = json.loads(response["body"].read())
        images = payload.get("images") or []
        if not images:
            raise ValueError("Titan returned no images")
        return decode_base64_payload(images[0])

    async def generate(self, text: str) -> bytes:
        try:
            return await run_sync_in_executor(self._invoke, text)
        except (BotoCoreError, ClientError, ValueError, KeyError) as exc:
            raise wrap_provider_error("titan", exc) from exc

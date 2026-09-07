"""AWS Nova Reel text-to-video client via Bedrock."""

import asyncio
import logging
import time

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from app.adapters.common import run_sync_in_executor, wrap_provider_error
from app.adapters.video_gen.base import VideoGenerationProvider
from app.config.settings import Settings

logger = logging.getLogger(__name__)


class NovaReelClient(VideoGenerationProvider):
    """Text-to-video using Amazon Nova Reel on Bedrock."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._client = boto3.client(
            "bedrock-runtime",
            region_name=settings.aws_region,
            aws_access_key_id=settings.aws_access_key_id or None,
            aws_secret_access_key=settings.aws_secret_access_key or None,
        )

    def _start_job(self, text: str) -> str:
        body = {
            "taskType": "TEXT_VIDEO",
            "textToVideoParams": {"text": text},
            "videoGenerationConfig": {
                "durationSeconds": 6,
                "fps": 24,
                "dimension": "1280x720",
            },
        }
        response = self._client.start_async_invoke(
            modelId=self._settings.aws_nova_reel_model_id,
            modelInput=body,
            outputDataConfig={"s3OutputDataConfig": {"s3Uri": "s3://placeholder-bucket/nova-reel/"}},
        )
        invocation_arn = response.get("invocationArn")
        if not invocation_arn:
            raise ValueError("Nova Reel did not return an invocation ARN")
        return invocation_arn

    def _poll_job(self, invocation_arn: str) -> bytes:
        deadline = time.monotonic() + self._settings.video_poll_timeout_seconds
        while time.monotonic() < deadline:
            response = self._client.get_async_invoke(invocationArn=invocation_arn)
            status = response.get("status")
            if status == "Completed":
                output_uri = response.get("outputDataConfig", {}).get("s3OutputDataConfig", {}).get("s3Uri")
                if not output_uri:
                    raise ValueError("Nova Reel completed but no output URI was returned")
                return self._download_from_s3_uri(output_uri)
            if status in {"Failed", "Cancelled"}:
                failure = response.get("failureMessage", "Unknown failure")
                raise ValueError(f"Nova Reel job {status.lower()}: {failure}")
            time.sleep(self._settings.video_poll_interval_seconds)
        raise TimeoutError("Nova Reel video generation timed out")

    def _download_from_s3_uri(self, s3_uri: str) -> bytes:
        if not s3_uri.startswith("s3://"):
            raise ValueError(f"Invalid S3 URI: {s3_uri}")
        path = s3_uri[5:]
        bucket, _, key = path.partition("/")
        s3 = boto3.client(
            "s3",
            region_name=self._settings.aws_region,
            aws_access_key_id=self._settings.aws_access_key_id or None,
            aws_secret_access_key=self._settings.aws_secret_access_key or None,
        )
        obj = s3.get_object(Bucket=bucket, Key=key)
        return obj["Body"].read()

    def _generate_sync(self, text: str) -> bytes:
        invocation_arn = self._start_job(text)
        return self._poll_job(invocation_arn)

    async def generate(self, text: str) -> bytes:
        try:
            return await run_sync_in_executor(self._generate_sync, text)
        except (BotoCoreError, ClientError, ValueError, TimeoutError) as exc:
            raise wrap_provider_error("nova_reel", exc) from exc

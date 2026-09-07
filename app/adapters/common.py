"""Common adapter helpers for provider clients."""

import asyncio
import base64
from typing import Any, Callable, TypeVar

from app.core.exceptions.content import ProviderAPIError

T = TypeVar("T")


def decode_base64_payload(payload: str) -> bytes:
    """Decode a base64 encoded string into raw bytes."""
    if not payload:
        return b""
    if "," in payload and payload.startswith("data:"):
        payload = payload.split(",", 1)[1]
    return base64.b64decode(payload)


async def run_sync_in_executor(func: Callable[..., T], *args: Any, **kwargs: Any) -> T:
    """Run a synchronous blocking function in the default asyncio executor."""
    loop = asyncio.get_running_loop()
    if kwargs:
        return await loop.run_in_executor(None, lambda: func(*args, **kwargs))
    return await loop.run_in_executor(None, func, *args)


def wrap_provider_error(provider: str, exc: Exception) -> ProviderAPIError:
    """Wrap any provider-specific exception into an AIMatic ProviderAPIError."""
    message = f"[{provider}] API error: {str(exc)}"
    return ProviderAPIError(message, error_code="provider_api_error")

"""Feature-level diagnostics for content providers (not load-balancer probes)."""

from typing import Any

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from app.config.settings import get_settings

router = APIRouter()


class ConnectionTestResponse(BaseModel):
    success: bool
    tti: dict[str, Any]
    ttv: dict[str, Any]
    message: str | None = None


def _tti_config_ok() -> dict[str, Any]:
    settings = get_settings()
    provider = settings.active_tti_provider
    if provider == "openai":
        ok = bool(settings.openai_api_key)
        detail = "OPENAI_API_KEY configured" if ok else "OPENAI_API_KEY missing"
    elif provider == "gemini":
        ok = bool(settings.google_api_key)
        detail = "GOOGLE_API_KEY configured" if ok else "GOOGLE_API_KEY missing"
    elif provider == "titan":
        ok = bool(settings.aws_access_key_id and settings.aws_secret_access_key)
        detail = "AWS credentials configured" if ok else "AWS credentials missing"
    else:
        return {"success": False, "provider": provider, "message": "Unsupported TTI provider"}
    return {"success": ok, "provider": provider, "message": detail}


def _ttv_config_ok() -> dict[str, Any]:
    settings = get_settings()
    provider = settings.active_ttv_provider
    if provider == "sora":
        ok = bool(settings.openai_api_key)
        detail = "OPENAI_API_KEY configured" if ok else "OPENAI_API_KEY missing"
    elif provider == "veo":
        ok = bool(settings.google_api_key)
        detail = "GOOGLE_API_KEY configured" if ok else "GOOGLE_API_KEY missing"
    elif provider == "nova_reel":
        ok = bool(settings.aws_access_key_id and settings.aws_secret_access_key)
        detail = "AWS credentials configured" if ok else "AWS credentials missing"
    else:
        return {"success": False, "provider": provider, "message": "Unsupported TTV provider"}
    return {"success": ok, "provider": provider, "message": detail}


@router.get("/test-connections", response_model=ConnectionTestResponse)
async def test_connections() -> ConnectionTestResponse:
    """Smoke-test active TTI/TTV provider configuration (no live generation)."""
    tti = _tti_config_ok()
    ttv = _ttv_config_ok()
    success = bool(tti.get("success") and ttv.get("success"))
    response = ConnectionTestResponse(
        success=success,
        tti=tti,
        ttv=ttv,
        message="All providers configured" if success else "One or more providers misconfigured",
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=response.model_dump(),
        )
    return response

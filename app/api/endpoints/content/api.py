"""Content feature registration."""

from fastapi import APIRouter, FastAPI, Request
from fastapi.responses import JSONResponse

from app.api.endpoints.content import diagnostics, routes
from app.config.settings import get_settings
from app.core.exceptions.content import AIMaticError
from app.core.feature_contract import FeatureModule

router = APIRouter()
router.include_router(routes.router)
router.include_router(diagnostics.router, prefix="/diagnostics")


def _providers_configured() -> dict[str, object]:
    settings = get_settings()
    issues: list[str] = []
    tti = (settings.active_tti_provider or "").strip()
    ttv = (settings.active_ttv_provider or "").strip()
    if not tti:
        issues.append("ACTIVE_TTI_PROVIDER unset")
    if not ttv:
        issues.append("ACTIVE_TTV_PROVIDER unset")

    if tti == "openai" and not settings.openai_api_key:
        issues.append("OPENAI_API_KEY required for openai TTI")
    if tti == "gemini" and not settings.google_api_key:
        issues.append("GOOGLE_API_KEY required for gemini TTI")
    if tti == "titan" and not (
        settings.aws_access_key_id and settings.aws_secret_access_key
    ):
        issues.append("AWS credentials required for titan TTI")

    if ttv == "sora" and not settings.openai_api_key:
        issues.append("OPENAI_API_KEY required for sora TTV")
    if ttv == "veo" and not settings.google_api_key:
        issues.append("GOOGLE_API_KEY required for veo TTV")
    if ttv == "nova_reel" and not (
        settings.aws_access_key_id and settings.aws_secret_access_key
    ):
        issues.append("AWS credentials required for nova_reel TTV")

    return {
        "success": len(issues) == 0,
        "tti_provider": tti or None,
        "ttv_provider": ttv or None,
        "issues": issues,
    }


def _validate_config() -> None:
    """Ensure active providers are selected; credential readiness is checked via /ready."""
    settings = get_settings()
    missing = []
    if not (settings.active_tti_provider or "").strip():
        missing.append("ACTIVE_TTI_PROVIDER")
    if not (settings.active_ttv_provider or "").strip():
        missing.append("ACTIVE_TTV_PROVIDER")
    if missing:
        raise RuntimeError(f"Content providers not selected: {', '.join(missing)}")


def _configure_app(app: FastAPI) -> None:
    """Register content-generation exception handlers on the shared app."""

    @app.exception_handler(AIMaticError)
    async def aimatic_error_handler(request: Request, exc: AIMaticError) -> JSONResponse:
        status_code = 400
        if exc.error_code == "provider_not_found":
            status_code = 500
        elif exc.error_code == "provider_api_error":
            status_code = 502
        elif exc.error_code == "content_generation_error":
            status_code = 500

        return JSONResponse(
            status_code=status_code,
            content={"detail": exc.message, "error_code": exc.error_code},
        )


FEATURE = FeatureModule(
    slug="content",
    router=router,
    prefix="/api/content",
    tags=["Content"],
    health_checks={
        "providers": _providers_configured,
    },
    on_startup=_validate_config,
    configure_app=_configure_app,
)

"""Shared FastAPI composition root for all AI Matic boilerplates."""

import asyncio
import inspect
import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from mangum import Mangum
import uvicorn

from app.api.dependencies.rate_limit import limiter
from app.api.endpoints import health
from app.api.middleware.cors import add_cors_middleware
from app.api.middleware.drain import DrainMiddleware
from app.api.middleware.exceptions import add_exception_handlers
from app.api.middleware.request_id import RequestIDMiddleware
from app.config.features import ENABLED_FEATURES
from app.config.settings import get_settings
from app.observability.logging import setup_logging

_settings = get_settings()
setup_logging(log_level=_settings.LOG_LEVEL, log_format=_settings.LOG_FORMAT)
logger = logging.getLogger(__name__)

IS_LAMBDA = bool(os.environ.get("AWS_LAMBDA_FUNCTION_NAME"))


async def _run_hook(hook):  # type: ignore[no-untyped-def]
    if hook is None:
        return
    result = hook()
    if inspect.isawaitable(result):
        await result


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Run enabled feature lifecycle hooks and drain requests on shutdown."""
    for feature in ENABLED_FEATURES:
        await _run_hook(feature.on_startup)
    app.state.request_count = 0
    app.state.draining = False
    yield
    app.state.draining = True
    drain_seconds = get_settings().SHUTDOWN_DRAIN_SECONDS
    deadline = asyncio.get_event_loop().time() + drain_seconds
    while getattr(app.state, "request_count", 0) > 0 and asyncio.get_event_loop().time() < deadline:
        await asyncio.sleep(0.5)
    for feature in reversed(ENABLED_FEATURES):
        await _run_hook(feature.on_shutdown)
    logger.info("Shutdown drain complete")


def create_app() -> FastAPI:
    """Create the composed FastAPI application from enabled feature modules."""
    settings = get_settings()
    app = FastAPI(
        title=settings.APP_TITLE,
        description=settings.APP_DESCRIPTION,
        version=settings.APP_VERSION,
        lifespan=lifespan if not IS_LAMBDA else None,
    )
    app.state.limiter = limiter
    add_exception_handlers(app)
    for feature in ENABLED_FEATURES:
        if feature.configure_app is not None:
            feature.configure_app(app)
    app.add_middleware(DrainMiddleware)
    app.add_middleware(RequestIDMiddleware)
    add_cors_middleware(app)

    app.include_router(health.router, prefix="/api/health", tags=["Health"])
    app.include_router(health.router, prefix="/health", tags=["Health"], include_in_schema=False)
    for feature in ENABLED_FEATURES:
        health.register_health_checks(feature.slug, feature.health_checks)
        app.include_router(
            feature.router,
            prefix=feature.prefix,
            tags=list(feature.tags),
        )
        # Also mount at root for backward compatibility with README curl commands
        app.include_router(
            feature.router,
            prefix="",
            tags=list(feature.tags),
            include_in_schema=False,
        )

    return app


app = create_app()

handler = Mangum(app, lifespan="off")
if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)

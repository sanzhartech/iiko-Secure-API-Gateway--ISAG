"""
main.py — FastAPI Application Entry Point
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.api import auth, proxy
from app.core.config import Settings, get_settings
from app.core.logging import configure_logging, get_logger
from app.middleware.rate_limiter import _on_rate_limit_exceeded, create_limiter, limiter
from app.middleware.secure_headers import SecureHeadersMiddleware
from app.security.audit import AuditLogMiddleware
from app.services.iiko_client import IikoClient

from app.db.engine import init_db, AsyncSessionLocal
from app.services.client_service import get_client_by_id
from app.models.client import GatewayClient
from app.core.hashing import get_password_hash

logger = get_logger(__name__)

async def seed_demo_client(settings: Settings) -> None:
    """Seed the database with the default demo client from config."""
    async with AsyncSessionLocal() as session:
        client = await get_client_by_id(session, "demo-client")
        if not client:
            demo_client = GatewayClient(
                client_id="demo-client",
                hashed_secret=get_password_hash(settings.gateway_client_secret),
                roles=["operator"]
            )
            session.add(demo_client)
            await session.commit()
            logger.info("seeded_demo_client", client_id="demo-client")


def _make_lifespan(settings: Settings):
    """Return a lifespan context manager bound to the given Settings instance."""
    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        configure_logging(
            log_level=settings.log_level,
            log_format=settings.log_format,
        )
        logger.info("isag_startup", environment=settings.app_env)

        if not hasattr(app.state, "iiko_client") or app.state.iiko_client is None:
            iiko_client = IikoClient(settings)
            app.state.iiko_client = iiko_client
        else:
            # [Fix #3] Use the existing client so aclose() is always called below.
            # This covers test injection and future hot-reload scenarios.
            iiko_client = app.state.iiko_client

        # Initialize SQLite database and tables
        await init_db()
        await seed_demo_client(settings)

        yield

        logger.info("isag_shutdown")
        if iiko_client is not None:
            await iiko_client.aclose()

    return lifespan



def create_app(settings: Settings | None = None) -> FastAPI:
    if settings is None:
        settings = get_settings()

    app = FastAPI(
        title="iiko Secure API Gateway",
        version="1.1.2",
        lifespan=_make_lifespan(settings),
    )

    # ── Exception Handlers ───────────────────────────────────────────────────

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
        """[Fix] Correctly handle standard exceptions (401, 403, 404, etc.)"""
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
            headers=exc.headers,
        )

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        """[Fix] Prevent shadowing HTTPExceptions; only catch unexpected bugs."""
        logger.error(
            "unhandled_exception",
            error_type=type(exc).__name__,
            path=request.url.path,
            error=str(exc),
        )
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"},
        )

    # ── Middleware Stack (LIFO — last registered runs first) ─────────────────

    # [Fix] SlowAPIMiddleware registered correctly for global rate limiting
    app.add_middleware(SlowAPIMiddleware)

    app.add_middleware(
        AuditLogMiddleware,
        trusted_cidrs=settings.trusted_proxy_cidrs_list,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=settings.cors_allow_credentials,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
        allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
        expose_headers=["X-Request-ID"],
    )

    app.add_middleware(SecureHeadersMiddleware)

    # [Fix #5] Use the global limiter singleton but ensure it uses the
    # default limit from settings for this application instance.
    limiter.default_limits = [settings.rate_limit_per_ip]
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _on_rate_limit_exceeded)

    # ── Routers ───────────────────────────────────────────────────────────────
    app.include_router(auth.router)
    app.include_router(proxy.router)

    @app.get("/health", tags=["System"], include_in_schema=False)
    async def health() -> dict:
        return {"status": "ok"}

    return app


# Guard module-level app creation so importing this module in pytest
# (where .env may not be present) does not trigger eager get_settings().
# Production: uvicorn reads `app.main:app` — TESTING is never set.
# Tests: conftest.py sets TESTING=1 and calls create_app(settings=test_settings).
import os as _os

if _os.environ.get("TESTING") != "1":
    app = create_app()


if __name__ == "__main__":
    import uvicorn
    _s = get_settings()
    uvicorn.run(
        "app.main:app",
        host=_s.app_host,
        port=_s.app_port,
        reload=_s.app_env == "development",
        access_log=False,
    )

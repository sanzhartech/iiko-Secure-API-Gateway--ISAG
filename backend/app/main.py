"""
main.py — FastAPI Application Entry Point
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.openapi.docs import get_swagger_ui_html
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.api import auth, proxy, protected, admin
from app.core.config import Settings, get_settings
from app.core.logging import configure_logging, get_logger
from app.middleware.rate_limiter import _on_rate_limit_exceeded, create_limiter, limiter
from app.middleware.secure_headers import SecureHeadersMiddleware
from app.middleware.size_validator import RequestSizeValidatorMiddleware
from app.middleware.response_filter import ResponseFilterMiddleware
from app.security.audit import AuditLogMiddleware
from app.middleware.metrics import MetricsMiddleware
from app.core.redis import get_redis_service
from app.services.iiko_client import IikoClient

from app.db.engine import init_db, AsyncSessionLocal
from app.services.client_service import get_client_by_id
from app.models.client import GatewayClient
from app.core.hashing import get_password_hash

logger = get_logger(__name__)

async def seed_demo_client(settings: Settings) -> None:
    """
    Seed the database with default clients from config.

    [Sec-1] Admin seeding is CONDITIONAL: only runs when both
    ADMIN_USERNAME and ADMIN_PASSWORD are explicitly set in environment.
    If either is absent the application starts without a default admin
    account, following the fail-secure / least-privilege principles.
    """
    async with AsyncSessionLocal() as session:
        # 1. (Removed Demo Client for Security)

        # 2. [Sec-1] Seed Admin Client ONLY when credentials are explicitly provided.
        # Never fall back to default admin/admin — fail-secure design.
        if settings.admin_username and settings.admin_password:
            admin_client = await get_client_by_id(session, settings.admin_username)
            if not admin_client:
                new_admin = GatewayClient(
                    client_id=settings.admin_username,
                    hashed_secret=get_password_hash(settings.admin_password),
                    roles=["admin"]
                )
                session.add(new_admin)
                logger.info("seeded_admin_client", admin_id=settings.admin_username)
        else:
            logger.warning(
                "admin_seeding_skipped",
                reason="ADMIN_USERNAME or ADMIN_PASSWORD not set — "
                       "no default admin account created (fail-secure).",
            )

        try:
            await session.commit()
            logger.info("seeded_default_clients")
        except Exception:
            await session.rollback()
            logger.debug("default_clients_already_seeded")


def _make_lifespan(settings: Settings):
    """Return a lifespan context manager bound to the given Settings instance."""
    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        configure_logging(
            log_level=settings.log_level,
            log_format=settings.log_format,
        )
        logger.info("isag_startup", environment=settings.app_env, host=settings.app_host, port=settings.app_port)

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

        # [Phase 3] Initialize Redis connection pool
        redis_service = get_redis_service(settings)
        await redis_service.connect()

        yield

        logger.info("isag_shutdown")
        if iiko_client is not None:
            await iiko_client.aclose()
        
        # [Phase 3] Close Redis connection pool
        await redis_service.disconnect()

    return lifespan



def create_app(settings: Settings | None = None) -> FastAPI:
    if settings is None:
        settings = get_settings()

    tags_metadata = [
        {"name": "Auth", "description": "Operations with authentication and tokens."},
        {"name": "Gateway", "description": "Secure proxy forwarding to iiko upstream."},
        {"name": "System", "description": "Liveness, readiness and system status."},
        {"name": "Observability", "description": "Prometheus metrics and telemetry."},
    ]

    app = FastAPI(
        title="ISAG - iiko Secure API Gateway",
        description="""
**ISAG (iiko Secure API Gateway)** — это защищенный асинхронный прокси-сервер для интеграции с iiko API.

### Основные функции:
* 🛡️ **JWT RS256**: Валидация подписи и типов токенов.
* 🔄 **Replay Protection**: Redis-backed JTI tracking.
* 🚦 **Rate Limiting**: Гибкое ограничение запросов (SlowAPI).
* 🔐 **RBAC**: Управление доступом на основе ролей.
* 🔎 **Audit Log**: Структурированные логи безопасности.

---
[Source Code](https://github.com/sanzhartech/iiko-Secure-API-Gateway--ISAG-) | [Project Documentation](https://github.com/sanzhartech/iiko-Secure-API-Gateway--ISAG-/blob/main/README.md)
        """,
        version="1.0.0",
        openapi_tags=tags_metadata,
        openapi_extra={
            "components": {
                "securitySchemes": {
                    "BearerAuth": {
                        "type": "http",
                        "scheme": "bearer",
                        "bearerFormat": "JWT",
                        "description": "Введите JWT токен: **Bearer [token]**"
                    }
                }
            },
            "security": [{"BearerAuth": []}],
        },
        docs_url=None,
        contact={
            "name": "Karzhaubayev Sanzhar",
            "url": "https://github.com/sanzhartech",
        },
        license_info={
            "name": "MIT License",
        },
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

    # ── Middleware Stack (LIFO — last registered runs first for requests) ────

    # Stage 9: Response Filtering (Innermost)
    app.add_middleware(ResponseFilterMiddleware)

    # [Phase 5] Prometheus metrics instrumentation.
    # Must be inner to AuditLog so it measures app processing time only.
    app.add_middleware(MetricsMiddleware)

    # Stage 8: Audit Logging
    app.add_middleware(
        AuditLogMiddleware,
        trusted_cidrs=settings.trusted_proxy_cidrs_list,
    )

    # CORS Stage
    # Add common development ports and explicit origins from settings
    cors_origins = settings.cors_origins_list
    if "http://localhost:3000" not in cors_origins:
        cors_origins.append("http://localhost:3000")
    if "http://localhost:3001" not in cors_origins:
        cors_origins.append("http://localhost:3001")
    if "http://localhost" not in cors_origins:
        cors_origins.append("http://localhost")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=settings.cors_allow_credentials,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "X-Request-ID", "Accept", "Origin"],
        expose_headers=["X-Request-ID"],
    )

    # Stage 3: Rate Limiting
    app.add_middleware(SlowAPIMiddleware)

    # Stage 2: Request Size Validation
    app.add_middleware(RequestSizeValidatorMiddleware, max_upload_size=10 * 1024 * 1024)

    # Stage 1: Transport Security & Headers (Outermost)
    # [Sec-2] Re-enabled: injects HSTS, X-Frame-Options, CSP, etc. on every response.
    app.add_middleware(SecureHeadersMiddleware)

    # [Fix #5] Use the global limiter singleton but ensure it uses the
    # default limit and Redis storage from settings.
    limiter.default_limits = [settings.rate_limit_per_ip]
    # Re-initialize storage if Redis is configured
    if settings.redis_url:
        from limits.storage import storage_from_string
        limiter._storage = storage_from_string(settings.redis_url)
        limiter._strategy = None # Force re-creation of strategy with new storage
    
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _on_rate_limit_exceeded)

    # ── Routers ───────────────────────────────────────────────────────────────
    app.include_router(auth.router, tags=["Auth"])
    app.include_router(proxy.router, tags=["Gateway"])
    app.include_router(protected.router, tags=["Gateway"])
    app.include_router(admin.router, tags=["Admin"])

    # ── Custom Swagger UI Route ───────────────────────────────────────────────
    @app.get("/docs", include_in_schema=False)
    async def custom_swagger_ui_html():
        return get_swagger_ui_html(
            openapi_url=app.openapi_url,
            title=app.title + " - Swagger UI",
            oauth2_redirect_url=app.swagger_ui_oauth2_redirect_url,
            # Используем надежные CDN ссылки для обхода белого экрана
            swagger_js_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js",
            swagger_css_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css",
        )

    @app.get("/health", tags=["System"], include_in_schema=False)
    async def health() -> dict:
        return {"status": "healthy"}

    @app.get("/ready", tags=["System"], include_in_schema=False)
    async def ready() -> dict:
        """Kubernetes-style readiness probe."""
        return {"status": "ready"}

    @app.get("/metrics", tags=["Observability"], include_in_schema=False)
    async def metrics():  # type: ignore[return]
        """
        [Phase 5] Expose Prometheus metrics for scraping.

        Intentionally UNAUTHENTICATED — Prometheus scrapers require direct
        access. Restrict port 8000 at the network/firewall level in production.
        """
        from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
        from fastapi.responses import Response as FastAPIResponse
        return FastAPIResponse(
            content=generate_latest(),
            media_type=CONTENT_TYPE_LATEST,
        )

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
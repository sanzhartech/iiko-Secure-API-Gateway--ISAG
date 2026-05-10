"""
api/proxy.py — Secure iiko Proxy with Correct Streaming Lifecycle
"""

from contextlib import AsyncExitStack
from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response, HTTPException, status
from starlette.responses import StreamingResponse

import redis.asyncio as redis
from app.core.redis import get_redis

from app.core.logging import get_logger
from app.middleware.rate_limiter import limiter
from app.schemas.token import TokenClaims
from app.security.rbac import Permission, require_permissions
from app.services.iiko_client import IikoClient, _STRIP_RESPONSE_HEADERS

router = APIRouter(prefix="/api", tags=["iiko Proxy"])
logger = get_logger(__name__)

# Ensure forward references inside TokenClaims are resolved after all
# modules have been imported (needed when from __future__ import annotations is active).
TokenClaims.model_rebuild()

_STRIP_REQUEST_HEADERS: frozenset[str] = frozenset(
    {
        "authorization",
        "connection",
        "keep-alive",
        "proxy-authenticate",
        "proxy-authorization",
        "te",
        "trailers",
        "transfer-encoding",
        "upgrade",
    }
)


def get_iiko_client(request: Request) -> IikoClient:
    return request.app.state.iiko_client


async def _forward(
    request: Request,
    path: str,
    claims: TokenClaims,
    iiko_client: IikoClient,
) -> Response:
    stack = AsyncExitStack()

    try:
        upstream_response = await stack.enter_async_context(
            iiko_client.proxy_request_stream(
                method=request.method,
                path=path,
                request=request,
                user_id=claims.sub,
            )
        )

        safe_headers = {
            k: v
            for k, v in upstream_response.headers.items()
            if k.lower() not in _STRIP_RESPONSE_HEADERS
            and k.lower() != "authorization"
            and k.lower() != "content-length"
        }

        async def _stream_generator():
            """
            Yield upstream bytes and guarantee the httpx connection is
            released in all exit paths:
              - normal EOF
              - client disconnect (GeneratorExit)
              - exception mid-stream
            """
            try:
                async for chunk in upstream_response.aiter_bytes():
                    yield chunk
            except Exception:
                # Re-raise so Starlette sees the error; finally still runs.
                raise
            finally:
                # Always close the upstream connection and exit the context.
                await stack.aclose()

        return StreamingResponse(
            content=_stream_generator(),
            status_code=upstream_response.status_code,
            headers=safe_headers,
            media_type=upstream_response.headers.get("content-type"),
        )

    except Exception:
        await stack.aclose()
        raise


@router.api_route(
    "/{path:path}",
    methods=["GET"],
    summary="Proxy GET Request",
    description="""
Securely forwards a GET request to the iiko upstream API.
- **Security**: Validates RS256 JWT, checks Replay Protection, and enforces `proxy:read` permission.
- **Mutation**: Strips client `Authorization` and hop-by-hop headers; injects server-side `IIKO_API_KEY`.
- **Observation**: Automatically logged and metered for latency and status codes.
""",
    response_class=StreamingResponse,
)
@limiter.limit("50/minute")
async def proxy_read(
    path: str,
    request: Request,
    claims: Annotated[
        TokenClaims,
        Depends(require_permissions(Permission.PROXY_READ)),
    ],
    iiko_client: Annotated[IikoClient, Depends(get_iiko_client)],
    redis_client: Annotated[redis.Redis, Depends(get_redis)],
) -> Response:
    if await redis_client.get("isag:global_block") == "1":
        logger.warning("proxy_blocked_by_kill_switch", path=path, user_id=claims.sub)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="System is under global lockdown."
        )
    return await _forward(request, path, claims, iiko_client)


@router.api_route(
    "/{path:path}",
    methods=["POST", "PUT", "PATCH", "DELETE"],
    summary="Proxy Mutation Request",
    description="""
Securely forwards a state-changing request (POST/PUT/PATCH/DELETE) to the iiko upstream API.
- **Security**: Validates RS256 JWT, checks Replay Protection, and enforces `proxy:write` permission.
- **Mutation**: Strips sensitive client headers and injects internal API credentials.
- **Reliability**: Uses streaming for both request body and response to handle large payloads (e.g., menu sync).
""",
    response_class=StreamingResponse,
)
@limiter.limit("50/minute")
async def proxy_write(
    path: str,
    request: Request,
    claims: Annotated[
        TokenClaims,
        Depends(require_permissions(Permission.PROXY_WRITE)),
    ],
    iiko_client: Annotated[IikoClient, Depends(get_iiko_client)],
    redis_client: Annotated[redis.Redis, Depends(get_redis)],
) -> Response:
    if await redis_client.get("isag:global_block") == "1":
        logger.warning("proxy_blocked_by_kill_switch", path=path, user_id=claims.sub)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="System is under global lockdown."
        )
    return await _forward(request, path, claims, iiko_client)
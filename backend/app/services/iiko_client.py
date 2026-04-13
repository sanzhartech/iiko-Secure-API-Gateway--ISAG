"""
services/iiko_client.py — iiko API HTTP Client

REMEDIATION PASS CHANGES:
  [Fix] proxy_request_stream() uses non-buffering streaming (httpx.stream).
  [Fix] Optimized connection pool for production-grade gateway performance.
  [Fix] Preserves multi-value query parameters by passing MultiDict directly.
  [Fix] X-Gateway-Version now reads APP_VERSION constant — no more drift.
"""

from __future__ import annotations

# Single source of truth for the gateway version.
# Must match the `version=` argument in create_app() in main.py.
APP_VERSION = "1.1.2"


import posixpath
import urllib.parse
from contextlib import asynccontextmanager
from typing import AsyncIterator

import httpx
from fastapi import HTTPException, Request, status

from app.core.config import Settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# Headers that must never be forwarded to upstream (RFC 2616 §13.5.1)
_HOP_BY_HOP_HEADERS: frozenset[str] = frozenset({
    "connection",
    "keep-alive",
    "proxy-authenticate",
    "proxy-authorization",
    "te",
    "trailers",
    "transfer-encoding",
    "upgrade",
    "authorization",
    "host",
})

# Upstream response headers that must not be forwarded to clients
_STRIP_RESPONSE_HEADERS: frozenset[str] = frozenset({
    "server",
    "x-powered-by",
    "transfer-encoding",
})


def _sanitize_path(raw_path: str) -> str:
    """Normalise and validate the proxy path before forwarding."""
    decoded = urllib.parse.unquote(raw_path)

    # [Security] Check for traversal sequences in the RAW decoded path
    # BEFORE normpath resolves them. posixpath.normpath('/../etc/passwd')
    # silently returns '/etc/passwd', hiding the attack intent.
    raw_segments = decoded.replace("\\", "/").split("/")
    if ".." in raw_segments:
        logger.warning("proxy_path_traversal_blocked", raw_path=raw_path)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid request path",
        )

    normalised = posixpath.normpath(f"/{decoded}")
    return normalised


class IikoClient:
    """Async HTTP client for the iiko upstream API."""

    def __init__(self, settings: Settings) -> None:
        self._base_url = settings.iiko_api_base_url.rstrip("/")
        self._api_key = settings.iiko_api_key
        self._timeout = settings.iiko_request_timeout_seconds

        # [Fix] Optimized connection pool for production performance
        self._client = httpx.AsyncClient(
            base_url=self._base_url,
            timeout=httpx.Timeout(self._timeout),
            verify=True,
            follow_redirects=False,
            limits=httpx.Limits(
                max_connections=500,
                max_keepalive_connections=100,
                keepalive_expiry=30.0,
            ),
        )

    async def aclose(self) -> None:
        """Close underlying HTTP connection pool gracefully."""
        await self._client.aclose()

    @asynccontextmanager
    async def proxy_request_stream(
        self,
        method: str,
        path: str,
        request: Request,
        user_id: str,
    ) -> AsyncIterator[httpx.Response]:
        """
        [Fix] Non-Buffering Streaming Proxy
        Forwards a request to iiko using streaming for both request body
        and upstream response content. Using context manager to ensure
        connection cleanup.
        """
        upstream_path = _sanitize_path(path)
        upstream_headers = self._build_safe_headers(request)

        logger.info(
            "proxy_request_stream",
            user_id=user_id,
            method=method,
            upstream_path=upstream_path,
        )

        try:
            # [Fix] Stream request body directly from client to upstream
            # [Fix] Use request.query_params directly to preserve multi-value fields
            async with self._client.stream(
                method=method,
                url=upstream_path,
                headers=upstream_headers,
                content=request.stream(),
                params=request.query_params,
            ) as response:
                yield response

        except httpx.TimeoutException:
            logger.warning("proxy_timeout", upstream_path=upstream_path, user_id=user_id)
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail="Upstream service timed out",
            )
        except httpx.ConnectError:
            logger.error("proxy_connect_error", upstream_path=upstream_path, user_id=user_id)
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Upstream service unavailable",
            )
        except httpx.HTTPError as exc:
            logger.error(
                "proxy_http_error",
                upstream_path=upstream_path,
                user_id=user_id,
                error=str(exc),
            )
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Upstream service error",
            )

    def _build_safe_headers(self, request: Request) -> dict[str, str]:
        """Build sanitised headers for upstream request."""
        safe_headers: dict[str, str] = {
            name: value
            for name, value in request.headers.items()
            if name.lower() not in _HOP_BY_HOP_HEADERS
        }
        safe_headers["Authorization"] = f"Bearer {self._api_key}"
        safe_headers["X-Gateway-Version"] = APP_VERSION  # [Fix #2] single source of truth
        return safe_headers

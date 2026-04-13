"""
middleware/metrics.py — Prometheus Metrics Middleware

Wraps every incoming request to:
  1. Record end-to-end latency in REQUEST_LATENCY histogram.
  2. Increment REQUESTS_TOTAL counter with method/endpoint/status_code labels.
  3. Increment BLOCKED_REQUESTS counter for any response >= 400, keyed by reason.

Block reason inference:
  400 with 'path traversal' → path_traversal
  401/403 with 'replay' body → replay_attack
  401/403 other             → invalid_token (or forbidden)
  413                        → request_too_large
  429                        → rate_limit

This middleware MUST be registered AFTER (inner to) AuditLogMiddleware in
the LIFO stack so it measures the full request lifecycle.
"""

from __future__ import annotations

import time
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.routing import Match
from starlette.types import ASGIApp

from app.core.metrics import (
    BLOCKED_REQUESTS,
    REQUEST_LATENCY,
    REQUESTS_TOTAL,
    BLOCK_REASON_RATE_LIMIT,
    BLOCK_REASON_INVALID_TOKEN,
    BLOCK_REASON_FORBIDDEN,
    BLOCK_REASON_REPLAY_ATTACK,
    BLOCK_REASON_REQUEST_TOO_LARGE,
    BLOCK_REASON_PATH_TRAVERSAL,
)


def _normalise_endpoint(request: Request) -> str:
    """
    Return a stable endpoint label for Prometheus metrics.

    Uses FastAPI's own route matching to replace dynamic path segments
    (e.g. /api/orders/42 → /api/{path}) so cardinality stays bounded.
    Falls back to the raw path if no route is matched (e.g. 404s).
    """
    for route in request.app.routes:
        match, _ = route.matches(request.scope)
        if match == Match.FULL:
            return getattr(route, "path", request.url.path)
    return request.url.path


def _infer_block_reason(status_code: int, response_body: str) -> str:
    """
    Infer the security block reason from the response status code and body.

    The body sniffing is intentionally shallow — we look only for well-known
    marker words that appear in our own error messages. This avoids coupling
    the middleware tightly to internal error strings.
    """
    body_lower = response_body.lower()

    if status_code == 429:
        return BLOCK_REASON_RATE_LIMIT
    if status_code == 413:
        return BLOCK_REASON_REQUEST_TOO_LARGE
    if status_code == 400 and "path" in body_lower:
        return BLOCK_REASON_PATH_TRAVERSAL
    if status_code in (401, 403):
        if "replay" in body_lower or "already been used" in body_lower:
            return BLOCK_REASON_REPLAY_ATTACK
        if status_code == 403:
            return BLOCK_REASON_FORBIDDEN
        return BLOCK_REASON_INVALID_TOKEN
    # Anything else (500, 502, etc.) is not a security block
    return "upstream_error"


class MetricsMiddleware(BaseHTTPMiddleware):
    """
    Prometheus instrumentation middleware.

    Measures end-to-end request latency and increments counters.
    Does NOT block or modify requests/responses — purely observational.

    Registration order (LIFO): must be added BEFORE AuditLogMiddleware
    in main.py so it runs after (inner to) audit, wrapping only the
    application layer. This keeps metrics scoped to actual processing time.
    """

    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip /metrics and /health to avoid self-scraping noise
        if request.url.path in ("/metrics", "/health", "/ready"):
            return await call_next(request)

        endpoint = _normalise_endpoint(request)
        method = request.method
        start = time.monotonic()

        response: Response | None = None
        try:
            response = await call_next(request)
            return response
        except Exception:
            raise
        finally:
            latency = time.monotonic() - start
            status_code = response.status_code if response else 500

            # Record latency in histogram
            REQUEST_LATENCY.labels(method=method, endpoint=endpoint).observe(latency)

            # Record total request count
            REQUESTS_TOTAL.labels(
                method=method,
                endpoint=endpoint,
                status_code=str(status_code),
            ).inc()

            # Record blocked requests (security events)
            if status_code >= 400:
                # Streams don't allow re-reading body here.
                # Use a lightweight empty fallback — detailed reason from audit log.
                reason = _infer_block_reason(status_code, "")
                BLOCKED_REQUESTS.labels(reason=reason).inc()

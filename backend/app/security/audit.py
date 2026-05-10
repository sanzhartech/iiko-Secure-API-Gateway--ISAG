"""
security/audit.py — Audit Logging Middleware

REMEDIATION PASS CHANGES:
  [Fix 4] _get_client_ip() now gates X-Forwarded-For trust on a CIDR allow-list.
          If the direct connection does NOT come from a trusted proxy IP, the
          X-Forwarded-For header is ignored and the real direct IP is used.
          This closes IP spoofing bypass on both rate limiting and audit logs.
          Trusted CIDRs are configured via TRUSTED_PROXY_CIDRS env variable.

FIELDS LOGGED per request:
  request_id, timestamp, user_id (or "anonymous"), method, path,
  status_code, latency_ms, client_ip, decision

SECURITY:
  - Authorization header NEVER logged
  - Request/response bodies NOT logged
  - X-Request-ID attached to response for correlation
"""

from __future__ import annotations

import ipaddress
import time
import uuid
from typing import Callable

import structlog
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.core.logging import get_logger
from app.core.network import compile_trusted_networks, extract_client_ip

logger = get_logger(__name__)

_REQUEST_ID_HEADER = "X-Request-ID"


class AuditLogMiddleware(BaseHTTPMiddleware):
    """
    ASGI middleware emitting a structured audit log entry for every request.

    [Fix 4] Accepts trusted_cidrs at constructor time (injected from settings
    in main.py). X-Forwarded-For is only trusted when the direct connection
    arrives from one of these CIDRs.
    """

    def __init__(self, app: ASGIApp, trusted_cidrs: list[str] | None = None) -> None:
        super().__init__(app)
        self._trusted_networks = compile_trusted_networks(trusted_cidrs or [])
        for cidr in trusted_cidrs or []:
            try:
                ipaddress.ip_network(cidr, strict=False)
            except ValueError:
                logger.warning("trusted_cidr_invalid", cidr=cidr)

    def _get_client_ip(self, request: Request) -> str:
        """
        [Fix 4] Extract real client IP with trusted-proxy gating.

        Logic:
          1. Get the direct connection IP (request.client.host).
          2. Only if that IP is in TRUSTED_PROXY_CIDRS, honour X-Forwarded-For.
          3. Otherwise return the direct connection IP.

        This prevents any client from spoofing their IP by setting
        X-Forwarded-For themselves.
        """
        return extract_client_ip(request, self._trusted_networks)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        request_id = str(uuid.uuid4())
        start_time = time.monotonic()

        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(request_id=request_id)
        request.state.request_id = request_id

        response: Response | None = None
        decision = "allow"
        try:
            response = await call_next(request)
            if response.status_code >= 400:
                decision = "deny"
            # [Fix #9] Set X-Request-ID BEFORE returning so it is always
            # included in streaming responses (Starlette sends headers first).
            response.headers[_REQUEST_ID_HEADER] = request_id
            return response
        except Exception:
            decision = "deny"
            raise
        finally:
            latency_ms = round((time.monotonic() - start_time) * 1000, 2)
            status_code = response.status_code if response else 500

            # user_id set by get_current_claims() [Fix 2]; "anonymous" if auth failed
            user_id: str = getattr(request.state, "user_id", "anonymous")

            logger.info(
                "audit",
                user_id=user_id,
                method=request.method,
                path=request.url.path,
                status_code=status_code,
                latency_ms=latency_ms,
                client_ip=self._get_client_ip(request),
                decision=decision,
            )

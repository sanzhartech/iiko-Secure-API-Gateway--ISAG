"""
middleware/secure_headers.py — Security Headers Middleware

Injects security-relevant HTTP response headers on every response.

HEADERS APPLIED:
  - Strict-Transport-Security   HSTS, 1 year, includeSubDomains
  - X-Frame-Options             Prevents clickjacking
  - X-Content-Type-Options      Prevents MIME sniffing
  - Referrer-Policy             Limits referrer leakage
  - Content-Security-Policy     Restrictive CSP (Configured for Swagger UI)
  - Permissions-Policy          Disables browser features
  - Cache-Control               No caching for API responses

CORS:
  Handled separately via FastAPI's CORSMiddleware with explicit allow-list
  from settings (not a wildcard).
"""

from __future__ import annotations

from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp


_SECURITY_HEADERS: dict[str, str] = {
    # HSTS: force HTTPS for 1 year, apply to subdomains, allow preload.
    # [Fix #11] NOTE: When deployed behind a TLS-terminating reverse proxy
    # (nginx, caddy, etc.), HSTS is often also set by the proxy itself.
    # The duplicate header is harmless — browsers honour the strictest value.
    # In a pure HTTP internal-only deployment remove this header.
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains; preload",
    # Prevent clickjacking via iframe embedding
    "X-Frame-Options": "DENY",
    # Prevent MIME type sniffing
    "X-Content-Type-Options": "nosniff",
    # Restrictive referrer: send origin only on same-origin requests
    "Referrer-Policy": "strict-origin-when-cross-origin",
    
    # CSP: Allow Swagger UI assets to load from CDNs (jsdelivr/unpkg)
    # while keeping everything else blocked (default-src 'none').
    "Content-Security-Policy": (
        "default-src 'none'; "
        "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://unpkg.com; "
        "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://unpkg.com; "
        "img-src 'self' data: https://fastapi.tiangolo.com; "
        "frame-ancestors 'none'"
    ),
    
    # Disable browser features that have no relevance to an API
    "Permissions-Policy": "geolocation=(), camera=(), microphone=()",
    # Do not cache API responses
    "Cache-Control": "no-store",
    "Pragma": "no-cache",
}

# Headers that must be removed from responses before sending to clients
_REMOVE_HEADERS: frozenset[str] = frozenset({
    "server",          # Don't leak web server version
    "x-powered-by",    # Don't leak framework/runtime info
})


class SecureHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware that injects standard security headers into every response
    and strips information-leaking headers.
    """

    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response: Response = await call_next(request)

        # Inject security headers
        for header_name, header_value in _SECURITY_HEADERS.items():
            response.headers[header_name] = header_value

        # Remove headers that leak implementation details
        for header in _REMOVE_HEADERS:
            if header in response.headers:
                del response.headers[header]

        return response
"""
middleware/rate_limiter.py — Per-IP and Per-User Rate Limiting

REMEDIATION PASS CHANGES:
  [Fix 2] REMOVED unverified JWT sub parsing from key function.
           Rate limit key now uses ONLY:
             - Verified user_id from request.state (set by JWT dep post-validation)
             - Direct client IP as fallback (no XFF trust here)
           This closes the rate limit bypass via forged `sub` claim.

BEHAVIOR:
  - Per-IP limit: always active as fallback
  - Per-user limit: applies ONLY when request.state.user_id is set (JWT verified)
  - Returns HTTP 429 with Retry-After header (RFC 6585)
  - Fails closed on storage error
  - Auth endpoint has stricter limit (10/minute)

THREAT MODEL addressed:
  - [CLOSED] Forged sub claim exhausting another user's rate bucket
  - [CLOSED] Bypass by omitting JWT (IP fallback still applies)
"""

from __future__ import annotations

from fastapi import Request
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from starlette.responses import JSONResponse

from app.core.logging import get_logger

logger = get_logger(__name__)


def _get_rate_limit_key(request: Request) -> str:
    """
    Rate limit key function — ONLY uses verified identity.

    [Fix 2] The previous implementation parsed unverified JWT to extract `sub`,
    which allowed an attacker to exhaust any user's rate bucket by crafting a
    token with an arbitrary `sub` claim.

    NEW LOGIC:
      1. If request.state.user_id is set → JWT was VERIFIED by the auth
         dependency, so we can trust this value → use 'user:<id>' as key.
      2. Otherwise → unauthenticated request → use remote IP.

    request.state.user_id is set in get_current_claims() dependency in
    jwt_validator.py, which runs BEFORE the route handler and BEFORE the
    @limiter.limit() check on decorated routes.

    Note: For unauthenticated endpoints (/auth/token, /health), user_id
    is never set; the IP-based key correctly applies.
    """
    user_id: str | None = getattr(request.state, "user_id", None)
    if user_id:
        return f"user:{user_id}"

    return get_remote_address(request)


def create_limiter(storage_uri: str, default_limit: str = "100/minute") -> Limiter:
    """
    Create and return the configured slowapi Limiter.

    [Phase 3] Uses Redis storage if configured via settings.redis_url.
    In-memory storage is used if storage_uri starts with 'memory://'.
    """
    return Limiter(
        key_func=_get_rate_limit_key,
        default_limits=[default_limit],
        storage_uri=storage_uri,
        strategy="fixed-window",
    )


def _on_rate_limit_exceeded(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    """
    Return HTTP 429 with Retry-After header.
    Also logs the rate-limited key for audit purposes.
    """
    key = _get_rate_limit_key(request)
    retry_after = getattr(exc, "retry_after", 60)
    logger.warning(
        "rate_limit_exceeded",
        key=key,
        path=request.url.path,
        retry_after=retry_after,
    )
    return JSONResponse(
        status_code=429,
        content={"detail": "Too many requests. Please slow down."},
        headers={"Retry-After": str(retry_after)},
    )


# Singleton limiter instance.
# The default limit is set to 100/minute here as a safe fallback.
# In main.py the limiter is re-created (via create_limiter) with the value
# from settings.rate_limit_per_ip so the env-variable is honoured at runtime.
limiter = create_limiter("memory://")

"""
security/jti_store.py — Replay Protection via JTI Blacklisting

[Sec-4] Grace period redesign:
    The previous implementation allowed UNLIMITED parallel requests within the
    grace window, creating a window for token-reuse abuse.
    New logic:
      - First use: SET key NX — records timestamp, returns False (allow).
      - Second use within grace_period: allowed ONCE via an atomic INCR counter
        stored under a separate "{prefix}grace:{jti}" key.
      - Third and subsequent uses within grace_period: REJECTED (replay).
      - Any use after grace_period: REJECTED (replay).
    This enforces the invariant: at most 2 successful uses of a single JTI
    (original + 1 grace), even under parallel request races.
"""

from __future__ import annotations

import time
from typing import Annotated

import redis.asyncio as redis
from fastapi import Depends

from app.core.config import Settings, get_settings
from app.core.logging import get_logger
from app.core.redis import get_redis

logger = get_logger(__name__)


class JTIStore:
    """
    Service for tracking JWT IDs (jti) in Redis to prevent replay attacks.
    [Phase 3] Corresponds to Stage 5 of the Security Pipeline.
    """

    def __init__(self, redis_client: redis.Redis, settings: Settings) -> None:
        self._redis = redis_client
        self._prefix = "isag:jti:"
        self._buffer = settings.jti_expiry_buffer_seconds
        self._grace_period = settings.jti_replay_grace_period_seconds

    async def is_replay(self, jti: str, expires_at: int) -> bool:
        """
        Check if a JTI has already been used and mark it if not.

        Args:
            jti:        Unique JWT ID claim from the token.
            expires_at: Unix timestamp when the token expires (``exp`` claim).

        Returns:
            True  — this is a replay; the request must be rejected (HTTP 401).
            False — first use or exactly one grace-period use; request allowed.

        [Sec-4] Security invariant:
            At most 2 successful authentications per JTI are allowed:
              1. The original request (SET NX succeeds — ``old_value`` is None).
              2. One additional request within ``grace_period`` seconds of first
                 use (INCR on a separate grace counter returns 1).
            A third or later request — even within the grace window — is rejected
            because the grace INCR returns ≥ 2.

        Implementation uses two Redis keys per JTI:
          - ``isag:jti:{jti}``        — first-use timestamp (SET NX, TTL = token
                                          lifetime + buffer).
          - ``isag:jti:grace:{jti}``  — grace-use counter  (INCR, TTL = grace
                                          period – ensures the key expires shortly
                                          after the window closes).
        Both operations are atomic at the individual-command level; the counter
        key is short-lived so it cannot accumulate between token lifetimes.
        """
        now = int(time.time())
        ttl = max(1, (expires_at - now) + self._buffer)
        key = f"{self._prefix}{jti}"
        grace_key = f"{self._prefix}grace:{jti}"

        # --- Phase 1: Attempt to record first use (atomic SET NX) ---
        old_value = await self._redis.set(
            name=key, value=str(now), ex=ttl, nx=True, get=True
        )

        if old_value is None:
            # Key did not exist — this is the first (and legitimate) use.
            logger.debug("jti_recorded", jti=jti, ttl=ttl)
            return False

        # --- Phase 2: Key already existed — check grace period ---
        try:
            first_use = int(old_value)
        except (ValueError, TypeError):
            # Malformed stored value — fail closed (treat as replay).
            logger.warning("jti_malformed_store_value", jti=jti)
            return True

        elapsed = now - first_use
        if elapsed > self._grace_period:
            # Grace window has already passed — hard replay.
            logger.warning("jti_replay_detected", jti=jti, elapsed=elapsed)
            return True

        # --- Phase 3: Within grace window — allow exactly ONE extra use ---
        # INCR is atomic. If the grace counter did not exist, EXPIRE sets
        # its TTL to grace_period + 1 so it auto-expires shortly after the window.
        grace_count = await self._redis.incr(grace_key)
        if grace_count == 1:
            # First time the counter was created — set TTL so it auto-expires.
            await self._redis.expire(grace_key, self._grace_period + 1)

        if grace_count > 1:
            # [Sec-4] More than one grace use detected — reject.
            logger.warning(
                "jti_grace_exceeded",
                jti=jti,
                grace_count=grace_count,
                elapsed=elapsed,
            )
            return True

        logger.debug(
            "jti_grace_request_allowed",
            jti=jti,
            elapsed=elapsed,
            grace_count=grace_count,
        )
        return False


def get_jti_store(
    redis_client: Annotated[redis.Redis, Depends(get_redis)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> JTIStore:
    """FastAPI dependency: returns a JTIStore manager."""
    return JTIStore(redis_client, settings)

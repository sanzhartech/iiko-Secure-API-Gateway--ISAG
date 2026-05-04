"""
security/jti_store.py — Replay Protection via JTI Blacklisting
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
            jti: Unique JWT ID.
            expires_at: Unix timestamp when the token expires.

        Returns:
            True if this is a replay (JTI already exists and outside grace period).
            False if this is a new use or within the grace period.

        [Security Logic] 
        - Stores the timestamp of first use as the value in Redis.
        - Uses SET with NX (Not eXists) and GET to atomically handle parallel requests.
        - If the JTI exists, we allow it if the current time is within 
          `grace_period` seconds of the first use.
        """
        now = int(time.time())
        ttl = max(1, (expires_at - now) + self._buffer)
        key = f"{self._prefix}{jti}"
        
        # [Atomic] Set key with timestamp only if it does not exist (NX)
        # We use 'get=True' to retrieve the old value if it exists.
        # This requires Redis 6.2+
        old_value = await self._redis.set(name=key, value=str(now), ex=ttl, nx=True, get=True)
        
        if old_value is None:
            # Key didn't exist, successfully recorded first use
            logger.debug("jti_recorded", jti=jti, ttl=ttl)
            return False
        
        # Key existed, check the grace period
        try:
            first_use = int(old_value)
            elapsed = now - first_use
            
            if elapsed <= self._grace_period:
                logger.debug("jti_parallel_request_allowed", jti=jti, elapsed=elapsed)
                return False
        except (ValueError, TypeError):
            # Fallback if value is malformed
            pass

        logger.warning("jti_replay_detected", jti=jti)
        return True


def get_jti_store(
    redis_client: Annotated[redis.Redis, Depends(get_redis)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> JTIStore:
    """FastAPI dependency: returns a JTIStore manager."""
    return JTIStore(redis_client, settings)

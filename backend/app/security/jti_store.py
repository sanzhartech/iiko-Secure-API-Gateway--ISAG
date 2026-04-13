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

    async def is_replay(self, jti: str, expires_at: int) -> bool:
        """
        Check if a JTI has already been used and mark it if not.
        
        Args:
            jti: Unique JWT ID.
            expires_at: Unix timestamp when the token expires.

        Returns:
            True if this is a replay (JTI already exists).
            False if this is a new, valid use (JTI recorded).

        [Security Requirement] Uses atomic SET with NX (Not eXists) and EX (Expiration)
        to prevent race conditions in high-concurrency scenarios.
        """
        now = int(time.time())
        ttl = max(1, (expires_at - now) + self._buffer)

        key = f"{self._prefix}{jti}"
        
        # [Atomic] Set key only if it does not exist (NX) with a TTL (EX)
        # Returns True if set (new token), None/False if already exists (replay)
        success = await self._redis.set(name=key, value="1", ex=ttl, nx=True)
        
        if success:
            logger.debug("jti_recorded", jti=jti, ttl=ttl)
            return False
        
        logger.warning("jti_replay_detected", jti=jti)
        return True


def get_jti_store(
    redis_client: Annotated[redis.Redis, Depends(get_redis)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> JTIStore:
    """FastAPI dependency: returns a JTIStore manager."""
    return JTIStore(redis_client, settings)

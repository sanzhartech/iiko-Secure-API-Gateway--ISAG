"""
core/redis.py — Async Redis Connection Management
"""

from __future__ import annotations

from typing import Annotated, AsyncIterator

import redis.asyncio as redis
from fastapi import Depends

from app.core.config import Settings, get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class RedisService:
    """
    Manager for the async Redis connection pool.
    [Phase 3] Centralizes Redis connectivity for rate limiting and JTI store.
    """

    def __init__(self, settings: Settings) -> None:
        self._redis_url = settings.redis_url
        self._client: redis.Redis | None = None

    async def connect(self) -> None:
        """Initialize the Redis connection pool."""
        if self._client is None:
            try:
                self._client = redis.from_url(
                    self._redis_url,
                    encoding="utf-8",
                    decode_responses=True,
                )
                # Verify connection
                await self._client.ping()
                logger.info("redis_connected", url=self._redis_url)
            except Exception as exc:
                logger.error("redis_connection_failed", url=self._redis_url, error=str(exc))
                raise

    async def disconnect(self) -> None:
        """Close the Redis connection pool."""
        if self._client:
            await self._client.aclose()
            self._client = None
            logger.info("redis_disconnected")

    @property
    def client(self) -> redis.Redis:
        """Return the active Redis client."""
        if self._client is None:
            raise RuntimeWarning("RedisService.connect() was not called.")
        return self._client


# Singleton manager instance
_redis_service: RedisService | None = None


def get_redis_service(
    settings: Annotated[Settings, Depends(get_settings)],
) -> RedisService:
    """FastAPI dependency: returns the RedisService manager."""
    global _redis_service
    if _redis_service is None:
        _redis_service = RedisService(settings)
    return _redis_service


async def get_redis(
    service: Annotated[RedisService, Depends(get_redis_service)],
) -> AsyncIterator[redis.Redis]:
    """
    FastAPI dependency: returns an active Redis client.
    Usage:
        @router.get("/")
        async def endpoint(db: Annotated[redis.Redis, Depends(get_redis)]):
            await db.set("key", "value")
    """
    yield service.client

"""
core/kill_switch.py — Global Kill-Switch State

Single source of truth for the global lockdown flag stored in Redis.

[B3] The flag is read on EVERY proxy request, so the value is cached in-process
for a short TTL to avoid a Redis round-trip on the hot path. Whenever an admin
toggles the switch via ``set_global_block`` the local cache is invalidated
immediately, so the change takes effect at once in the worker that handled the
toggle and within ``_TTL_SECONDS`` in any other worker/replica.
"""

from __future__ import annotations

import time

import redis.asyncio as redis

from app.core.logging import get_logger

logger = get_logger(__name__)

KILL_SWITCH_KEY = "isag:global_block"
_TTL_SECONDS = 1.0

# value: last observed flag; checked_at: monotonic timestamp of last Redis read.
_cache: dict[str, float | bool] = {"value": False, "checked_at": 0.0}


def _invalidate_cache() -> None:
    """Force the next is_globally_blocked() call to re-read Redis."""
    _cache["checked_at"] = 0.0


async def is_globally_blocked(redis_client: redis.Redis) -> bool:
    """Return True if the global kill-switch is active (cached for a short TTL)."""
    now = time.monotonic()
    if now - float(_cache["checked_at"]) < _TTL_SECONDS:
        return bool(_cache["value"])
    try:
        blocked = (await redis_client.get(KILL_SWITCH_KEY)) == "1"
    except Exception as exc:
        # Fail-open on Redis errors to preserve availability; serve last value.
        logger.error("kill_switch_check_failed", error=str(exc))
        return bool(_cache["value"])
    _cache["value"] = blocked
    _cache["checked_at"] = now
    return blocked


async def set_global_block(redis_client: redis.Redis, active: bool) -> None:
    """Activate or deactivate the global kill-switch and invalidate the cache."""
    if active:
        await redis_client.set(KILL_SWITCH_KEY, "1")
    else:
        await redis_client.delete(KILL_SWITCH_KEY)
    _invalidate_cache()

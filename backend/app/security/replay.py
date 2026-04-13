"""
replay.py — Replay Protection Stage 5
Zero-Trust requirement: Mitigate replay attacks using JTI and Nonce tracking.
"""

from typing import Set

# [Rule 4] Replay Cache (Simplified In-Memory)
# TODO: Move to Redis for distributed production environments
_jti_cache: Set[str] = set()

def is_jti_valid(jti: str) -> bool:
    """
    Check if a JTI has been used before.
    Returns False if already seen, True if new.
    """
    if jti in _jti_cache:
        return False
    _jti_cache.add(jti)
    return True

def cleanup_expired_jtis():
    """Purge JTIs that are older than max token expiration."""
    # Logic to be implemented with TTL
    pass

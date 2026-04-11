"""
security/rbac.py — Role-Based Access Control

DESIGN:
  - Roles and permissions are defined in code (not hardcoded in middleware).
  - Deny by default: if role is not in the registry, access is denied.
  - require_roles() returns a FastAPI dependency factory — no coupling to routes.
  - HTTP 403 on access denied (not 401 — token is valid, but insufficient privilege).

THREAT MODEL:
  - Privilege escalation via missing role check
  - Missing RBAC on newly added endpoints
"""

from __future__ import annotations

from enum import StrEnum
from typing import Annotated

from fastapi import Depends, HTTPException, status

from app.core.logging import get_logger
from app.schemas.token import TokenClaims
from app.security.jwt_validator import get_current_claims

logger = get_logger(__name__)


# ── Permission Enum ───────────────────────────────────────────────────────────

class Permission(StrEnum):
    """
    All granular permissions in the system.
    Extend here when adding new operations.
    """
    PROXY_READ = "proxy:read"
    PROXY_WRITE = "proxy:write"
    ADMIN_READ = "admin:read"
    ADMIN_WRITE = "admin:write"
    AUTH_ISSUE = "auth:issue"


# ── Role → Permission Mapping ─────────────────────────────────────────────────

ROLE_PERMISSIONS: dict[str, frozenset[Permission]] = {
    "viewer": frozenset({
        Permission.PROXY_READ,
    }),
    "operator": frozenset({
        Permission.PROXY_READ,
        Permission.PROXY_WRITE,
    }),
    "admin": frozenset({
        Permission.PROXY_READ,
        Permission.PROXY_WRITE,
        Permission.ADMIN_READ,
        Permission.ADMIN_WRITE,
        Permission.AUTH_ISSUE,
    }),
    "service": frozenset({
        Permission.PROXY_READ,
        Permission.PROXY_WRITE,
        Permission.AUTH_ISSUE,
    }),
}


# ── Permission Resolver ───────────────────────────────────────────────────────

def resolve_permissions(roles: list[str]) -> frozenset[Permission]:
    """
    Return the union of all permissions granted to the given roles.
    Unknown roles contribute zero permissions (deny-by-default).
    """
    result: set[Permission] = set()
    for role in roles:
        result |= ROLE_PERMISSIONS.get(role, frozenset())
    return frozenset(result)


# ── Dependency Factory ────────────────────────────────────────────────────────

def require_permissions(*required: Permission):
    """
    FastAPI dependency factory.

    Returns a dependency that enforces ALL listed permissions are present.
    Fail-closed: if the JWT has no roles or unknown roles → 403.

    Usage:
        @router.get("/orders", dependencies=[Depends(require_permissions(Permission.PROXY_READ))])
        async def list_orders(...): ...
    """
    required_set = frozenset(required)

    async def _check(
        claims: Annotated[TokenClaims, Depends(get_current_claims)],
    ) -> TokenClaims:
        granted = resolve_permissions(claims.roles)
        missing = required_set - granted

        if missing:
            logger.warning(
                "rbac_denied",
                user_id=claims.sub,
                required=sorted(required_set),
                granted=sorted(granted),
                missing=sorted(missing),
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )

        logger.debug(
            "rbac_allowed",
            user_id=claims.sub,
            granted=sorted(granted),
        )
        return claims

    return _check

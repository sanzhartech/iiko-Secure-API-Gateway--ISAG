from __future__ import annotations

from dataclasses import dataclass

from fastapi import HTTPException, status

from app.core.logging import get_logger
from app.schemas.token import TokenClaims

logger = get_logger(__name__)


@dataclass(frozen=True)
class RequiredScope:
    resource: str
    action: str

    @property
    def value(self) -> str:
        return f"{self.resource}:{self.action}"


def infer_required_scope(method: str, path: str) -> RequiredScope | None:
    """
    Derive a coarse-grained scope from the proxied iiko path.

    Example:
    - GET /v1/orders            -> orders:read
    - POST /v1/orders/create    -> orders:write

    If the path cannot be mapped to a stable resource segment, scope checks are
    skipped and RBAC remains the controlling authorization layer.
    """
    normalised = path.strip("/")
    if not normalised:
        return None

    segments = [segment for segment in normalised.split("/") if segment]
    if not segments:
        return None

    resource = segments[1] if len(segments) > 1 and segments[0].startswith("v") else segments[0]
    resource = resource.lower()
    if not resource.isidentifier():
        return None

    action = "read" if method.upper() == "GET" else "write"
    return RequiredScope(resource=resource, action=action)


def ensure_scope_access(claims: TokenClaims, method: str, path: str) -> None:
    """
    Enforce client scopes for proxied traffic.

    Supported allow patterns:
    - `*`
    - `<resource>:*`
    - `<resource>:read|write`
    """
    required = infer_required_scope(method, path)
    if required is None:
        return

    granted = set(claims.scopes)
    allowed = {
        "*",
        f"{required.resource}:*",
        required.value,
    }
    if granted & allowed:
        return

    logger.warning(
        "scope_denied",
        user_id=claims.sub,
        path=path,
        method=method,
        required_scope=required.value,
        granted_scopes=sorted(granted),
    )
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail=f"Missing required scope: {required.value}",
    )

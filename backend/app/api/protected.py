"""
api/protected.py — Demo Protected Endpoint

Demonstrates the full auth flow for diploma defense.

CURL DEMO (step-by-step):

# 1. Get token pair
curl -s -X POST http://localhost:8000/auth/token \
  -H "Content-Type: application/json" \
  -d '{"client_id": "demo-client", "client_secret": "YOUR_SECRET"}' | python3 -m json.tool

# 2. Call protected endpoint (use access_token from step 1)
curl -s http://localhost:8000/protected/test \
  -H "Authorization: Bearer <access_token>"

# 3. Refresh tokens (use refresh_token from step 1)
curl -s -X POST http://localhost:8000/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{"refresh_token": "<refresh_token>"}' | python3 -m json.tool

# 4. Verify refresh token is REJECTED on protected endpoint (type guard)
curl -s http://localhost:8000/protected/test \
  -H "Authorization: Bearer <refresh_token>"
# Expected: 401 Unauthorized
"""

from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.logging import get_logger
from app.schemas.token import TokenClaims
from app.security.jwt_validator import get_current_claims

router = APIRouter(prefix="/protected", tags=["Demo"])
logger = get_logger(__name__)


@router.get(
    "/test",
    summary="Protected test endpoint",
    description="Requires a valid access token. Returns client identity. Use for demo.",
)
async def protected_test(
    claims: Annotated[TokenClaims, Depends(get_current_claims)],
) -> dict:
    """
    Returns a simple success response with the authenticated client_id.
    Rejects refresh tokens (type guard enforced by get_current_claims).
    """
    logger.info("protected_access", client_id=claims.sub, roles=claims.roles)
    return {
        "message": "Access granted",
        "client": claims.sub,
        "roles": claims.roles,
    }

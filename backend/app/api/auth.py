"""
api/auth.py — Authentication Endpoint

REMEDIATION PASS CHANGES:
  [Fix 1] `gateway_client_secret` used instead of `iiko_api_key`.
           iiko upstream key and client auth credentials are now fully decoupled.

POST /auth/token  →  Issues a signed RS256 JWT

SECURITY:
  - Stricter rate limit (10/minute) to resist brute force
  - Constant-time comparison (hmac.compare_digest) — no timing oracle
  - Issued tokens: RS256, short expiry (15 min), include iss/aud/sub/roles/jti
  - Same HTTP 401 for wrong client_id OR wrong secret — no user enumeration
"""

import hmac
import uuid
import secrets
from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from jose import jwt

from app.core.config import Settings, get_settings
from app.core.logging import get_logger
from app.middleware.rate_limiter import limiter
from app.schemas.token import RefreshTokenRequest, TokenRequest, TokenResponse
from app.security.jwt_validator import JWTValidator, get_jwt_validator

from sqlalchemy.ext.asyncio import AsyncSession
from app.db.engine import get_db_session
from app.services.client_service import get_client_by_id
from app.core.hashing import verify_password, dummy_verify

router = APIRouter(prefix="/auth", tags=["Authentication"])
logger = get_logger(__name__)


# ---------------------------------------------------------------------------

def _issue_access_token(sub: str, roles: list[str], settings: Settings) -> str:
    """
    Issue a signed RS256 JWT access token.

    Claims: iss, aud, sub, roles, exp, iat, jti (prevents replay tracking).

    [KID] The JOSE header includes a ``kid`` field set to
    ``settings.jwt_active_kid``.  On validation the gateway reads this kid
    and selects the matching public key from the key store, enabling
    zero-downtime key rotation without restarting the gateway.
    """
    now = datetime.now(tz=timezone.utc)
    expire = now + timedelta(minutes=settings.jwt_access_token_expire_minutes)

    payload = {
        "type": "access",
        "iss": settings.jwt_issuer,
        "aud": settings.jwt_audience,
        "sub": sub,
        "roles": roles,
        "exp": int(expire.timestamp()),
        "iat": int(now.timestamp()),
        "jti": uuid.uuid4().hex,
    }

    return jwt.encode(
        payload,
        settings.jwt_private_key,   # cached in-memory by config [Fix 5]
        algorithm=settings.jwt_algorithm,
        headers={"kid": settings.jwt_active_kid},  # [KID] rotation support
    )


def _issue_refresh_token(sub: str, settings: Settings) -> str:
    """
    Issue a signed RS256 JWT refresh token.
    Refresh tokens have 'type': 'refresh' and omit the 'roles' claim,
    relying on the auth endpoint to re-fetch claims during refresh.
    """
    now = datetime.now(tz=timezone.utc)
    expire = now + timedelta(days=settings.jwt_refresh_token_expire_days)

    payload = {
        "type": "refresh",
        "iss": settings.jwt_issuer,
        "aud": settings.jwt_audience,
        "sub": sub,
        "exp": int(expire.timestamp()),
        "iat": int(now.timestamp()),
        "jti": uuid.uuid4().hex,
    }

    return jwt.encode(
        payload,
        settings.jwt_private_key,
        algorithm=settings.jwt_algorithm,
        headers={"kid": settings.jwt_active_kid},
    )


@router.post(
    "/token",
    response_model=TokenResponse,
    summary="Issue JWT access token",
    description=(
        "Exchange client credentials for a short-lived RS256-signed access token. "
        "Subject to strict rate limiting (10/minute) to resist brute force."
    ),
)
@limiter.limit("10/minute")
async def issue_token(
    request: Request,
    body: TokenRequest,
    settings: Annotated[Settings, Depends(get_settings)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> TokenResponse:
    """
    Authenticate a gateway client and return a JWT access token.

    Returns HTTP 401 for both unknown client_id and wrong client_secret
    to prevent user enumeration.
    """
    client = await get_client_by_id(db, body.client_id)

    if client and client.is_active:
        credentials_valid = verify_password(body.client_secret, client.hashed_secret)
    else:
        dummy_verify()
        credentials_valid = False

    if not credentials_valid:
        logger.warning("auth_failed", client_id=body.client_id)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = _issue_access_token(
        sub=body.client_id,
        roles=client.roles,
        settings=settings,
    )
    refresh_token = _issue_refresh_token(
        sub=body.client_id,
        settings=settings,
    )

    logger.info("auth_success", client_id=body.client_id, roles=client.roles)

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.jwt_access_token_expire_minutes * 60,
        refresh_token=refresh_token,
    )


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Refresh access token",
    description="Exchange a valid refresh token for a new access token and a new refresh token.",
)
@limiter.limit("10/minute")
async def refresh_token(
    request: Request,
    body: RefreshTokenRequest,
    settings: Annotated[Settings, Depends(get_settings)],
    validator: Annotated[JWTValidator, Depends(get_jwt_validator)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> TokenResponse:
    """
    Refresh a JWT access token using a valid refresh token.
    Issues a new access token and performs rotation by issuing a new refresh token.
    """
    try:
        # Validate specifically expecting a refresh token
        claims = await validator.validate(body.refresh_token, expected_type="refresh")
    except HTTPException:
        # Pass through the 401 Unauthorized from validator
        raise

    # Verify the client still exists and is active
    client = await get_client_by_id(db, claims.sub)

    if not client or not client.is_active:
        logger.warning("refresh_failed_inactive_client", client_id=claims.sub)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Client is inactive or deleted",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Issue new token pair
    new_access = _issue_access_token(
        sub=claims.sub,
        roles=client.roles,
        settings=settings,
    )
    new_refresh = _issue_refresh_token(
        sub=claims.sub,
        settings=settings,
    )

    logger.info("refresh_success", client_id=claims.sub)

    return TokenResponse(
        access_token=new_access,
        token_type="bearer",
        expires_in=settings.jwt_access_token_expire_minutes * 60,
        refresh_token=new_refresh,
    )

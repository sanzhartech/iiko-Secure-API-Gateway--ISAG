"""
security/jwt_validator.py — RS256 JWT Validation

REMEDIATION PASS CHANGES:
  [Fix 2] get_current_claims() now sets request.state.user_id = claims.sub
          BEFORE returning. This makes the verified sub available to the
          rate limiter key function, eliminating the unverified sub parsing
          that previously existed in rate_limiter.py.
  [Fix 5] Public key is now loaded from in-memory cache (settings.jwt_public_key
          calls the cached property in config.py, NOT a disk read per request).
  [KID]   Validator now supports multi-key rotation.
          On every request, the kid claim from the JWT header is used to
          select the correct public key from settings.jwt_public_keys.
          Unknown kid → HTTP 401 (fail-closed).
          Fallback: if token has no kid header, the first registered key is used.

SECURITY ENFORCED:
  - Only RS256 algorithm accepted. HS256 / 'none' are explicitly rejected.
  - Validates: exp, nbf, iat, iss, aud, sub.
  - Clock skew tolerance configurable (capped at 300s in config validator).
  - Fails closed: any decode error → HTTP 401, no information leakage.

THREAT MODEL:
  - JWT forgery via algorithm confusion (alg:none, HS256 downgrade)
  - Expired token replay
  - Missing mandatory claims
  - Unknown / spoofed kid → rejected
"""

from __future__ import annotations

from typing import Annotated, Any, NoReturn

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import ExpiredSignatureError, JWTError, jwt
from jose.exceptions import JWTClaimsError

from app.core.config import Settings, get_settings
from app.core.logging import get_logger
from app.schemas.token import TokenClaims

logger = get_logger(__name__)

_bearer_scheme = HTTPBearer(auto_error=True)


class JWTValidator:
    """
    Stateless RS256 JWT validator with multi-key (kid) rotation support.

    Instantiated via dependency injection and used per-request.
    [Fix 5] Public keys are read from the in-memory cache in Settings,
    not from disk on every request.
    [KID]   The full kid→pem key store is held in _public_keys.
            Key selection happens inside _decode() by reading the kid
            claim from the unverified JWT header.
    """

    _FORBIDDEN_ALGORITHMS: frozenset[str] = frozenset({
        "HS256", "HS384", "HS512", "none",
    })

    def __init__(self, settings: Settings) -> None:
        # [KID] Full key store: dict[kid → pem].  At minimum one entry.
        self._public_keys: dict[str, str] = settings.jwt_public_keys
        self._algorithm = settings.jwt_algorithm
        self._issuer = settings.jwt_issuer
        self._audience = settings.jwt_audience
        self._clock_skew = settings.jwt_clock_skew_seconds

    def _decode(self, raw_token: str) -> dict[str, Any]:
        """
        Decode and fully validate a JWT token.
        Raises HTTPException(401) on any failure — generic message only.

        [KID] Key selection:
          1. Extract kid from unverified header.
          2. Look up kid in self._public_keys.
          3. Unknown kid → reject immediately (fail-closed).
          4. No kid in header → fall back to the first registered key.
             This maintains backward-compat with tokens issued before
             kid support was added.
        """
        # —— Step 1: Parse unverified header (→ algorithm + kid) ——————————
        try:
            unverified_header = jwt.get_unverified_header(raw_token)
        except JWTError:
            self._reject("Malformed JWT header")

        alg = unverified_header.get("alg", "")
        if alg in self._FORBIDDEN_ALGORITHMS or alg != self._algorithm:
            logger.warning("jwt_algorithm_rejected", algorithm=alg)
            self._reject("Unsupported JWT algorithm")

        # —— Step 2: Select public key by kid ———————————————————————
        kid: str | None = unverified_header.get("kid")
        if kid is not None:
            public_key = self._public_keys.get(kid)
            if public_key is None:
                logger.warning("jwt_unknown_kid", kid=kid)
                self._reject("Unknown key ID")
        else:
            # No kid in header — fall back to first registered key.
            # Allows smooth migration from single-key to multi-key setup.
            public_key = next(iter(self._public_keys.values()), None)
            if public_key is None:
                logger.error("jwt_no_public_keys_configured")
                self._reject("No public keys configured")
            logger.debug("jwt_kid_missing_fallback_used")

        # —— Step 3: Full decode + claim verification ————————————————
        try:
            payload = jwt.decode(
                raw_token,
                public_key,
                algorithms=[self._algorithm],
                audience=self._audience,
                issuer=self._issuer,
                options={
                    "verify_signature": True,
                    "verify_exp": True,
                    "verify_nbf": True,
                    "verify_iat": True,
                    "verify_aud": True,
                    "verify_iss": True,
                    "require": ["sub", "exp", "iat", "iss", "aud"],
                    "leeway": self._clock_skew,
                },
            )
        except ExpiredSignatureError:
            logger.info("jwt_expired")
            self._reject("Token has expired")
        except JWTClaimsError as exc:
            logger.warning("jwt_claims_error", detail=str(exc))
            self._reject("Invalid token claims")
        except JWTError as exc:
            logger.warning("jwt_decode_error", detail=str(exc))
            self._reject("Invalid token")

        return payload

    @staticmethod
    def _reject(reason: str) -> NoReturn:
        """
        Raise HTTP 401. Generic message only — no oracle information.
        WWW-Authenticate header per RFC 6750.
        Always raises; return type NoReturn makes this explicit to type checkers.
        """
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized",
            headers={"WWW-Authenticate": "Bearer"},
        )

    def validate(self, raw_token: str, expected_type: str = "access") -> TokenClaims:
        """Validate token and return typed, parsed claims."""
        payload = self._decode(raw_token)
        
        token_type = payload.get("type", "access")
        if token_type != expected_type:
            logger.warning("jwt_invalid_type", expected=expected_type, actual=token_type)
            self._reject("Invalid token type")
            
        return TokenClaims(
            sub=str(payload["sub"]),
            type=token_type,
            roles=payload.get("roles", []),
            iss=payload["iss"],
            aud=payload["aud"] if isinstance(payload["aud"], list) else [payload["aud"]],
            exp=payload["exp"],
            iat=payload["iat"],
        )


# ── FastAPI dependency factories ──────────────────────────────────────────────

def get_jwt_validator(
    settings: Annotated[Settings, Depends(get_settings)],
) -> JWTValidator:
    """FastAPI dependency: returns a JWTValidator backed by in-memory key cache."""
    return JWTValidator(settings)


async def get_current_claims(
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(_bearer_scheme)],
    validator: Annotated[JWTValidator, Depends(get_jwt_validator)],
) -> TokenClaims:
    """
    FastAPI dependency: extracts Bearer token, validates it, returns claims.

    [Fix 2] Sets request.state.user_id to the VERIFIED sub claim.
    This makes the verified identity available to:
      - The rate limiter key function (_get_rate_limit_key reads state.user_id)
      - The audit log middleware (reads state.user_id for attribution)
    Before this fix, both consumers tried to parse unverified tokens themselves,
    which opened a sub-spoofing bypass on rate limiting.

    Usage:
        @router.get("/protected")
        async def endpoint(
            claims: Annotated[TokenClaims, Depends(get_current_claims)]
        ): ...
    """
    claims = validator.validate(credentials.credentials)

    # [Fix 2] Set verified user_id BEFORE route handler body executes.
    # The rate limiter @limiter.limit() decorator evaluates AFTER dependencies,
    # so it will find the correct verified user_id here.
    request.state.user_id = claims.sub

    return claims

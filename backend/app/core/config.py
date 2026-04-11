"""
core/config.py — Application Settings

REMEDIATION PASS CHANGES:
  [Fix 1] Added `gateway_client_secret` — separate from `iiko_api_key`.
           Production validator prevents reuse of iiko key as client secret.
  [Fix 4] Added `trusted_proxy_cidrs` — gates X-Forwarded-For trust.
  [Fix 5] RSA keys loaded once via model_post_init, cached in PrivateAttr.
           Eliminates per-request disk reads (previously: read_text() per call).
  [Fix 7] `jwt_clock_skew_seconds` hard-capped at 300s.
  [KID]   Added `jwt_public_keys_path` / `jwt_active_kid` for multi-key rotation.
           On startup, public_keys.json is read once into _jwt_public_keys_cache
           (dict[kid, pem]). The validator selects the key by kid from JWT header.

All configuration is loaded strictly from environment variables.
No secrets are hardcoded. Application fails at startup if required
values are missing, following fail-closed principle.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Literal

from pydantic import Field, PrivateAttr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Central settings object backed by environment variables / .env file.
    Validated at startup via Pydantic v2. Missing required fields raise
    ValidationError which prevents the app from starting.

    RSA keys are read once in model_post_init and cached in private attributes.
    All subsequent accesses hit memory only — no filesystem I/O.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="forbid",
    )

    # ── Application ──────────────────────────────────────────────────────────
    app_env: Literal["development", "production"] = "development"
    app_debug: bool = False
    app_host: str = "0.0.0.0"
    app_port: int = 8000

    # ── JWT ──────────────────────────────────────────────────────────────────
    jwt_private_key_path: Path = Path("./keys/private.pem")
    jwt_public_key_path: Path = Path("./keys/public.pem")
    # [KID] Path to JSON key store: { "kid-id": "-----BEGIN PUBLIC KEY-----..." }
    # If the file exists, it takes priority over jwt_public_key_path.
    # If not set / not found, falls back to the single public key.
    jwt_public_keys_path: Path = Path("./keys/public_keys.json")
    # [KID] The kid that will be embedded in JWT headers issued by the auth endpoint.
    jwt_active_kid: str = "default"
    jwt_algorithm: Literal["RS256"] = "RS256"
    jwt_issuer: str = "isag.internal"
    jwt_audience: str = "isag-clients"
    jwt_access_token_expire_minutes: int = 15
    # [Fix #4] PLACEHOLDER — no refresh endpoint implemented yet.
    # This value is currently unused by any production code.
    # Either implement /auth/refresh or remove this field before going to production.
    jwt_refresh_token_expire_days: int = 7
    jwt_clock_skew_seconds: int = Field(default=60, ge=0)

    # ── iiko Upstream ────────────────────────────────────────────────────────
    iiko_api_base_url: str
    iiko_api_key: str    # used ONLY for upstream iiko authentication

    # [Fix 1] Separate credential store for gateway client authentication.
    # Must be a strong random secret (≥ 32 chars). NEVER use iiko_api_key here.
    gateway_client_secret: str

    iiko_request_timeout_seconds: float = 10.0

    # ── Rate Limiting ────────────────────────────────────────────────────────
    # [Fix #5] These values are now passed to create_limiter() in main.py
    # so the env-variable actually takes effect at runtime.
    rate_limit_per_ip: str = "100/minute"
    rate_limit_per_user: str = "50/minute"
    rate_limit_auth_endpoint: str = "10/minute"

    # ── CORS ─────────────────────────────────────────────────────────────────
    cors_allowed_origins: str = ""
    cors_allow_credentials: bool = False

    # [Fix 4] Trusted proxy CIDRs for X-Forwarded-For validation.
    # Comma-separated CIDR notation. E.g.: "10.0.0.0/8,172.16.0.0/12"
    # Leave empty to NEVER trust X-Forwarded-For (safest default).
    trusted_proxy_cidrs: str = ""

    # ── Logging ──────────────────────────────────────────────────────────────
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    log_format: Literal["json", "console"] = "json"

    # ── Private: RSA key cache (loaded once in model_post_init) ──────────────
    # [Fix 5]  Single private key, cached in-memory.
    # [KID]    Public keys stored as dict[kid → pem] for rotation support.
    _jwt_private_key_cache: str = PrivateAttr(default="")
    _jwt_public_key_cache: str = PrivateAttr(default="")
    _jwt_public_keys_cache: dict[str, str] = PrivateAttr(default_factory=dict)

    def model_post_init(self, __context: Any) -> None:
        """
        Load RSA keys from disk once after settings are validated.
        All subsequent accesses hit the in-memory cache.
        Called automatically by Pydantic after __init__.

        Key loading strategy:
          1. Always load the private key from jwt_private_key_path.
          2. If jwt_public_keys_path exists → parse JSON key store
             { kid: pem_string } and cache it in _jwt_public_keys_cache.
             Also cache the pem for jwt_active_kid as _jwt_public_key_cache
             (backward-compat for single-key consumers).
          3. If jwt_public_keys_path does not exist → fall back to
             jwt_public_key_path and register it under jwt_active_kid.
        """
        # Private key — always required
        object.__setattr__(
            self, "_jwt_private_key_cache",
            self.jwt_private_key_path.read_text(encoding="utf-8"),
        )

        # [KID] Public key store
        if self.jwt_public_keys_path.exists():
            raw = json.loads(self.jwt_public_keys_path.read_text(encoding="utf-8"))
            if not isinstance(raw, dict) or not raw:
                raise ValueError(
                    f"JWT_PUBLIC_KEYS_PATH '{self.jwt_public_keys_path}' must be a "
                    "non-empty JSON object mapping kid strings to PEM public keys."
                )
            object.__setattr__(self, "_jwt_public_keys_cache", dict(raw))
            # Populate single-key cache from active kid for backward-compat
            active_pem = raw.get(self.jwt_active_kid)
            if active_pem is None:
                raise ValueError(
                    f"JWT_ACTIVE_KID '{self.jwt_active_kid}' not found in "
                    f"'{self.jwt_public_keys_path}'. "
                    f"Available kids: {list(raw.keys())}"
                )
            object.__setattr__(self, "_jwt_public_key_cache", active_pem)
        else:
            # Fallback: single key, registered under jwt_active_kid
            single_pem = self.jwt_public_key_path.read_text(encoding="utf-8")
            object.__setattr__(self, "_jwt_public_key_cache", single_pem)
            object.__setattr__(
                self, "_jwt_public_keys_cache",
                {self.jwt_active_kid: single_pem},
            )

    # ── Computed properties ──────────────────────────────────────────────────

    @property
    def jwt_private_key(self) -> str:
        """Return cached RS256 private key (no disk I/O)."""
        return self._jwt_private_key_cache

    @property
    def jwt_public_key(self) -> str:
        """Return cached RS256 public key for jwt_active_kid (no disk I/O)."""
        return self._jwt_public_key_cache

    @property
    def jwt_public_keys(self) -> dict[str, str]:
        """Return full kid→pem key store (no disk I/O)."""
        return self._jwt_public_keys_cache

    @property
    def cors_origins_list(self) -> list[str]:
        if not self.cors_allowed_origins:
            return []
        return [o.strip() for o in self.cors_allowed_origins.split(",") if o.strip()]

    @property
    def trusted_proxy_cidrs_list(self) -> list[str]:
        """Return parsed list of trusted proxy CIDRs."""
        if not self.trusted_proxy_cidrs:
            return []
        return [c.strip() for c in self.trusted_proxy_cidrs.split(",") if c.strip()]

    # ── Validators ───────────────────────────────────────────────────────────

    @field_validator("jwt_clock_skew_seconds")
    @classmethod
    def clock_skew_must_be_reasonable(cls, v: int) -> int:
        """[Fix 7] Hard cap clock skew at 300s to prevent over-lenient validation."""
        if v > 300:
            raise ValueError(
                f"JWT_CLOCK_SKEW_SECONDS ({v}) must not exceed 300 seconds. "
                "Values above 300 significantly extend token validity windows."
            )
        return v

    @model_validator(mode="after")
    def enforce_production_constraints(self) -> "Settings":
        """
        Security constraints enforced in production:
        - iiko upstream must use HTTPS
        - debug mode off
        - CORS origins explicitly set
        [Fix 1] iiko_api_key must not equal gateway_client_secret
        """
        # [Fix 1] Prevent secret reuse — always check, not just in production
        if self.iiko_api_key == self.gateway_client_secret:
            raise ValueError(
                "IIKO_API_KEY and GATEWAY_CLIENT_SECRET must be different secrets. "
                "Reusing the upstream API key as a client secret creates a "
                "credential coupling vulnerability."
            )

        if self.app_env == "production":
            if not self.iiko_api_base_url.startswith("https://"):
                raise ValueError("IIKO_API_BASE_URL must use HTTPS in production")
            if self.app_debug:
                raise ValueError("APP_DEBUG must be false in production")
            if not self.cors_allowed_origins:
                raise ValueError(
                    "CORS_ALLOWED_ORIGINS must be explicitly set in production"
                )
        return self


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Return cached singleton Settings instance.
    RSA keys are loaded once during this first call and never re-read.
    Use as a FastAPI dependency: Depends(get_settings).
    """
    return Settings()

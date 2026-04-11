"""
tests/conftest.py — Shared Test Fixtures

Provides:
  - RSA key pair generated in-memory for tests (no filesystem dependency)
  - FastAPI async test client via httpx.AsyncClient
  - JWT factory helper for valid/expired/malformed tokens
  - Mocked Settings passed directly to create_app() — no get_settings() patching
"""

import os
os.environ["TESTING"] = "1"

import time
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from httpx import ASGITransport, AsyncClient
from jose import jwt


# ── RSA Key Pair (generated once per test session) ────────────────────────────

_KID_PRIMARY = "kid-test-2025"
_KID_ROTATED = "kid-test-rotated"


@pytest.fixture(scope="session")
def rsa_private_key_obj():
    """Generate an RSA-2048 private key once for the entire test session."""
    return rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )


@pytest.fixture(scope="session")
def rsa_private_key_pem(rsa_private_key_obj) -> str:
    return rsa_private_key_obj.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode("utf-8")


@pytest.fixture(scope="session")
def rsa_public_key_pem(rsa_private_key_obj) -> str:
    return rsa_private_key_obj.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode("utf-8")


# [KID] Second key pair simulates a rotated key used in rotation tests.

@pytest.fixture(scope="session")
def rsa_rotated_private_key_obj():
    """Generate a second RSA-2048 private key for key-rotation tests."""
    return rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )


@pytest.fixture(scope="session")
def rsa_rotated_private_key_pem(rsa_rotated_private_key_obj) -> str:
    return rsa_rotated_private_key_obj.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode("utf-8")


@pytest.fixture(scope="session")
def rsa_rotated_public_key_pem(rsa_rotated_private_key_obj) -> str:
    return rsa_rotated_private_key_obj.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode("utf-8")


# ── JWT Helper ────────────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def make_token(rsa_private_key_pem):
    """
    Factory fixture: returns a function that mints JWTs for tests.

    Usage:
        token = make_token()                          # valid operator token
        token = make_token(sub="user1", roles=["admin"])
        token = make_token(exp_offset=-100)           # expired
        token = make_token(algorithm="HS256", signing_key="bad")
        token = make_token(kid="kid-test-2025")       # explicit kid in header
        token = make_token(kid=None)                  # no kid in header (fallback path)
    """
    def _make(
        sub: str = "test-user",
        roles: list[str] | None = None,
        token_type: str = "access",
        iss: str = "isag.internal",
        aud: str = "isag-clients",
        exp_offset: int = 900,
        iat_offset: int = 0,
        algorithm: str = "RS256",
        signing_key: str | None = None,
        extra_claims: dict[str, Any] | None = None,
        omit_claims: list[str] | None = None,
        kid: str | None = _KID_PRIMARY,       # [KID] default kid matches test_settings
    ) -> str:
        now = int(time.time())
        payload: dict[str, Any] = {
            "type": token_type,
            "sub": sub,
            "roles": roles if roles is not None else ["operator"],
            "iss": iss,
            "aud": aud,
            "exp": now + exp_offset,
            "iat": now + iat_offset,
            "jti": "test-jti-0001",
        }
        if extra_claims:
            payload.update(extra_claims)
        for claim in (omit_claims or []):
            payload.pop(claim, None)

        key = signing_key if signing_key is not None else rsa_private_key_pem
        headers: dict[str, Any] = {}
        if kid is not None:
            headers["kid"] = kid
        return jwt.encode(payload, key, algorithm=algorithm, headers=headers or None)

    return _make


# ── Mock Settings ─────────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def test_settings(tmp_path_factory, rsa_private_key_pem, rsa_public_key_pem, rsa_rotated_public_key_pem):
    """
    MagicMock of Settings pre-loaded with in-memory RSA keys.

    Passed directly to create_app(settings=test_settings) — no get_settings()
    patching needed. This avoids issues with lru_cache and cached imports.

    [KID] jwt_public_keys contains two keys to allow rotation tests.
          jwt_active_kid points to the primary key used for token issuance.
    """
    # Set required env vars so Pydantic Settings validates
    import os
    import json
    
    tmp_dir = tmp_path_factory.mktemp("keys")
    private_key_path = tmp_dir / "private.pem"
    private_key_path.write_text(rsa_private_key_pem, encoding="utf-8")
    
    public_keys_path = tmp_dir / "public_keys.json"
    public_keys_data = {
        "primary-1": rsa_public_key_pem,
        "rotated-2": rsa_rotated_public_key_pem
    }
    public_keys_path.write_text(json.dumps(public_keys_data), encoding="utf-8")
    
    os.environ["IIKO_API_BASE_URL"] = "https://fake-iiko.example.com"
    os.environ["IIKO_API_KEY"] = "test-iiko-key-upstream-only"
    os.environ["GATEWAY_CLIENT_SECRET"] = "test-gateway-client-secret-separate"
    os.environ["JWT_PRIVATE_KEY_PATH"] = str(private_key_path)
    os.environ["JWT_PUBLIC_KEYS_PATH"] = str(public_keys_path)
    os.environ["JWT_ACTIVE_KID"] = "primary-1"
    
    os.environ.pop("PYTHON_PATH", None)

    from app.core.config import Settings
    s = Settings(_env_file=None)

    # JWT — single (active) public key for backward-compat consumers
    object.__setattr__(s, "_jwt_public_key_cache", rsa_public_key_pem)
    object.__setattr__(s, "_jwt_private_key_cache", rsa_private_key_pem)
    
    # [KID] Full key store accessible to JWTValidator
    object.__setattr__(s, "_jwt_public_keys_cache", {
        _KID_PRIMARY: rsa_public_key_pem,
        _KID_ROTATED: rsa_rotated_public_key_pem,
    })
    
    s.jwt_active_kid = _KID_PRIMARY
    s.jwt_algorithm = "RS256"
    s.jwt_issuer = "isag.internal"
    s.jwt_audience = "isag-clients"
    s.jwt_clock_skew_seconds = 60
    s.jwt_access_token_expire_minutes = 15

    # iiko upstream
    s.iiko_api_base_url = "https://fake-iiko.example.com"
    s.iiko_api_key = "test-iiko-key-upstream-only"
    s.gateway_client_secret = "test-gateway-client-secret-separate"
    s.iiko_request_timeout_seconds = 5.0

    # Rate limiting
    s.rate_limit_per_ip = "100/minute"
    s.rate_limit_per_user = "50/minute"
    s.rate_limit_auth_endpoint = "10/minute"

    # CORS
    s.cors_allowed_origins = ""
    s.cors_allow_credentials = False

    # Trusted proxies (empty — direct IP always used in tests)
    s.trusted_proxy_cidrs = ""

    # Logging — suppress output during tests
    s.log_level = "ERROR"
    s.log_format = "console"

    # App
    s.app_env = "development"
    s.app_debug = False
    s.app_host = "127.0.0.1"
    s.app_port = 8000

    return s


# ── FastAPI Async Test Client ─────────────────────────────────────────────────

@pytest_asyncio.fixture(scope="session")
async def async_client(test_settings):
    """
    Async HTTP test client backed by the FastAPI app.

    Uses create_app(settings=test_settings) — mock settings injected directly,
    no get_settings() monkey-patching required.
    IikoClient is mocked via app.state so no real HTTP calls are made.
    """
    from app.main import create_app
    from app.core.config import get_settings

    application = create_app(settings=test_settings)
    
    def override_get_settings():
        return test_settings
        
    application.dependency_overrides[get_settings] = override_get_settings

    # Inject mock iiko client BEFORE the app starts (lifespan will skip init
    # because app.state.iiko_client is already set)
    mock_iiko = AsyncMock()
    application.state.iiko_client = mock_iiko

    async with AsyncClient(
        transport=ASGITransport(app=application),
        base_url="http://test",
    ) as client:
        yield client, mock_iiko

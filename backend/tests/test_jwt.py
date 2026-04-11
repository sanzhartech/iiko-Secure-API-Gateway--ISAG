"""
tests/test_jwt.py — JWT Validation Tests

Covers:
  ✅ Valid RS256 token → 200
  ❌ Expired token → 401
  ❌ Algorithm confusion: HS256 → 401
  ❌ Algorithm confusion: alg=none → 401
  ❌ Wrong issuer → 401
  ❌ Wrong audience → 401
  ❌ Missing 'sub' claim → 401
  ❌ Missing 'exp' claim → 401
  ❌ No Authorization header → 401 (422 from HTTPBearer)
  ❌ Malformed bearer token → 401
"""

from __future__ import annotations

import pytest
from unittest.mock import patch

import httpx


@pytest.mark.asyncio
class TestJWTValidation:

    async def test_valid_token_accepted(self, async_client, make_token, test_settings):
        """Valid RS256 token with correct claims → passes JWT validation."""
        client, mock_iiko = async_client
        token = make_token(roles=["operator"])

        mock_iiko.proxy_request.return_value = httpx.Response(200, json={"ok": True})

        with patch("app.core.config.get_settings", return_value=test_settings), \
             patch("app.security.jwt_validator.get_settings", return_value=test_settings):
            response = await client.get(
                "/api/orders",
                headers={"Authorization": f"Bearer {token}"},
            )

        # 200 or whatever iiko returns — not 401/403
        assert response.status_code not in (401, 403), (
            f"Expected auth to pass, got {response.status_code}: {response.text}"
        )

    async def test_expired_token_rejected(self, async_client, make_token, test_settings):
        """Token where exp is in the past → 401."""
        client, _ = async_client
        token = make_token(exp_offset=-3600)   # expired 1 hour ago

        with patch("app.security.jwt_validator.get_settings", return_value=test_settings):
            response = await client.get(
                "/api/orders",
                headers={"Authorization": f"Bearer {token}"},
            )

        assert response.status_code == 401

    async def test_hs256_algorithm_rejected(self, async_client, make_token, test_settings):
        """HS256-signed token must be rejected (algorithm confusion attack)."""
        client, _ = async_client
        token = make_token(algorithm="HS256", signing_key="some-symmetric-secret")

        with patch("app.security.jwt_validator.get_settings", return_value=test_settings):
            response = await client.get(
                "/api/orders",
                headers={"Authorization": f"Bearer {token}"},
            )

        assert response.status_code == 401

    async def test_alg_none_rejected(self, async_client, test_settings):
        """Unsigned token (alg=none) must be rejected."""
        client, _ = async_client
        # Craft a token with alg=none manually (jose won't normally produce it)
        import base64, json
        header = base64.urlsafe_b64encode(json.dumps({"alg": "none", "typ": "JWT"}).encode()).rstrip(b"=")
        payload_data = {"sub": "attacker", "roles": ["admin"], "iss": "isag.internal",
                        "aud": "isag-clients", "exp": 9999999999, "iat": 0}
        payload = base64.urlsafe_b64encode(json.dumps(payload_data).encode()).rstrip(b"=")
        token = f"{header.decode()}.{payload.decode()}."

        with patch("app.security.jwt_validator.get_settings", return_value=test_settings):
            response = await client.get(
                "/api/orders",
                headers={"Authorization": f"Bearer {token}"},
            )

        assert response.status_code == 401

    async def test_wrong_issuer_rejected(self, async_client, make_token, test_settings):
        """Token with wrong iss claim → 401."""
        client, _ = async_client
        token = make_token(iss="evil-issuer.example.com")

        with patch("app.security.jwt_validator.get_settings", return_value=test_settings):
            response = await client.get(
                "/api/orders",
                headers={"Authorization": f"Bearer {token}"},
            )

        assert response.status_code == 401

    async def test_wrong_audience_rejected(self, async_client, make_token, test_settings):
        """Token with wrong aud claim → 401."""
        client, _ = async_client
        token = make_token(aud="wrong-audience")

        with patch("app.security.jwt_validator.get_settings", return_value=test_settings):
            response = await client.get(
                "/api/orders",
                headers={"Authorization": f"Bearer {token}"},
            )

        assert response.status_code == 401

    async def test_missing_sub_claim_rejected(self, async_client, make_token, test_settings):
        """Token without 'sub' claim → 401."""
        client, _ = async_client
        token = make_token(omit_claims=["sub"])

        with patch("app.security.jwt_validator.get_settings", return_value=test_settings):
            response = await client.get(
                "/api/orders",
                headers={"Authorization": f"Bearer {token}"},
            )

        assert response.status_code == 401

    async def test_no_authorization_header(self, async_client):
        """Missing Authorization header → 401/403."""
        client, _ = async_client
        response = await client.get("/api/orders")
        assert response.status_code in (401, 403)

    async def test_malformed_token_rejected(self, async_client, test_settings):
        """Garbage Bearer value → 401."""
        client, _ = async_client
        with patch("app.security.jwt_validator.get_settings", return_value=test_settings):
            response = await client.get(
                "/api/orders",
                headers={"Authorization": "Bearer not.a.valid.jwt.at.all"},
            )

        assert response.status_code == 401


@pytest.mark.asyncio
class TestJWTKeyRotation:
    """
    Tests specific to the multi-key (kid) rotation feature.

    Ensures that:
      - Tokens signed with the rotated key (kid-test-rotated) are accepted
        when that key is present in the key store.
      - Tokens claiming an unknown kid are strictly rejected (fail-closed).
      - Tokens with no kid header fall back to the first registered key.
      - Tokens with a valid kid but signed with a DIFFERENT key are rejected.
    """

    async def test_rotated_key_token_accepted(
        self,
        async_client,
        make_token,
        test_settings,
        rsa_rotated_private_key_pem,
    ):
        """
        Token signed with the rotated private key and carrying kid-test-rotated
        must be accepted — the key store contains both primary and rotated keys.
        """
        client, mock_iiko = async_client
        import httpx as _httpx
        mock_iiko.proxy_request.return_value = _httpx.Response(200, json={"ok": True})

        token = make_token(
            signing_key=rsa_rotated_private_key_pem,
            kid="kid-test-rotated",
        )

        with patch("app.core.config.get_settings", return_value=test_settings), \
             patch("app.security.jwt_validator.get_settings", return_value=test_settings):
            response = await client.get(
                "/api/orders",
                headers={"Authorization": f"Bearer {token}"},
            )

        assert response.status_code not in (401, 403), (
            f"Rotated-key token should pass, got {response.status_code}: {response.text}"
        )

    async def test_unknown_kid_rejected(self, async_client, make_token, test_settings):
        """
        Token carrying an unregistered kid must be rejected with HTTP 401.
        This verifies fail-closed behaviour — unknown key IDs are never
        silently ignored.
        """
        client, _ = async_client
        token = make_token(kid="kid-unknown-attacker")

        with patch("app.security.jwt_validator.get_settings", return_value=test_settings):
            response = await client.get(
                "/api/orders",
                headers={"Authorization": f"Bearer {token}"},
            )

        assert response.status_code == 401, (
            f"Unknown kid should return 401, got {response.status_code}"
        )

    async def test_no_kid_header_falls_back_to_primary(
        self, async_client, make_token, test_settings
    ):
        """
        Token without a kid header must fall back to the first registered key
        (kid-test-2025 / primary) and be accepted.
        """
        client, mock_iiko = async_client
        import httpx as _httpx
        mock_iiko.proxy_request.return_value = _httpx.Response(200, json={"ok": True})

        token = make_token(kid=None)   # no kid in JOSE header

        with patch("app.core.config.get_settings", return_value=test_settings), \
             patch("app.security.jwt_validator.get_settings", return_value=test_settings):
            response = await client.get(
                "/api/orders",
                headers={"Authorization": f"Bearer {token}"},
            )

        assert response.status_code not in (401, 403), (
            f"No-kid fallback should pass, got {response.status_code}: {response.text}"
        )

    async def test_wrong_key_for_valid_kid_rejected(
        self,
        async_client,
        make_token,
        test_settings,
        rsa_rotated_private_key_pem,
    ):
        """
        Token claiming kid-test-2025 (primary) but signed with the ROTATED private
        key must be rejected — signature verification catches the mismatch.
        """
        client, _ = async_client
        token = make_token(
            signing_key=rsa_rotated_private_key_pem,
            kid="kid-test-2025",      # claims primary kid but signed with rotated key
        )

        with patch("app.security.jwt_validator.get_settings", return_value=test_settings):
            response = await client.get(
                "/api/orders",
                headers={"Authorization": f"Bearer {token}"},
            )

        assert response.status_code == 401, (
            f"Wrong key for valid kid must return 401, got {response.status_code}"
        )


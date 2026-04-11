"""
tests/test_rate_limit.py — Rate Limiting Integration Tests
"""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from app.middleware.rate_limiter import _get_rate_limit_key, _on_rate_limit_exceeded


class TestRateLimitKeyFunction:

    def test_uses_verified_user_id_when_available(self):
        """Key function uses verified user_id if present in request.state."""
        mock_request = MagicMock()
        mock_request.state.user_id = "verified-user-123"
        mock_request.client.host = "1.2.3.4"

        key = _get_rate_limit_key(mock_request)
        assert key == "user:verified-user-123"

    def test_falls_back_to_ip_without_user_id(self):
        """Key function falls back to remote IP if request.state.user_id is missing."""
        mock_request = MagicMock()
        # Ensure .state exists but has no .user_id
        mock_request.state = MagicMock(spec=[])
        mock_request.client.host = "192.168.1.1"

        key = _get_rate_limit_key(mock_request)
        assert key == "192.168.1.1"


@pytest.mark.asyncio
class TestRateLimitIntegration:

    async def test_burst_beyond_limit_triggers_429(
        self, async_client, make_token, test_settings
    ):
        """
        [Fix #8] Deterministic burst test with isolated rate-limit bucket.
        Uses a unique sub so this test never shares a counter with other
        tests running in the same session (in-memory limiter is a singleton).
        Verifies that exceeding the rate limit results in HTTP 429 with
        the mandatory 'Retry-After' header.
        """
        import uuid as _uuid

        client, mock_iiko = async_client
        # [Fix #8] Unique user per test run → isolated in-memory rate bucket
        unique_sub = f"burst-user-{_uuid.uuid4().hex[:8]}"
        token = make_token(sub=unique_sub, roles=["operator"])

        # Proper async context manager mock
        mock_response = httpx.Response(200, content=b"ok")
        mock_cm = AsyncMock()
        mock_cm.__aenter__.return_value = mock_response
        mock_cm.__aexit__ = AsyncMock(return_value=None)  # [Fix #8] avoid RuntimeWarning
        mock_iiko.proxy_request_stream.return_value = mock_cm

        # SlowAPI fixed-window default is 100/minute; the @limiter.limit("50/minute")
        # decorator on the proxy route applies first.
        limit_count = 50
        responses = []

        with patch("app.security.jwt_validator.get_settings", return_value=test_settings):
            for _ in range(limit_count + 5):
                r = await client.get(
                    "/api/ping",
                    headers={"Authorization": f"Bearer {token}"},
                )
                responses.append(r)
                if r.status_code == 429:
                    break

        status_codes = [r.status_code for r in responses]
        assert 429 in status_codes, (
            f"Expected 429 after {limit_count} requests, got: {status_codes}"
        )

        r_429 = next(r for r in responses if r.status_code == 429)
        assert "Retry-After" in r_429.headers
        assert r_429.headers["Retry-After"].isdigit()

    async def test_auth_endpoint_rate_limit_behavior(
        self, async_client, test_settings
    ):
        """
        [Fix] Behavioral audit of /auth/token rate limit.
        Stricter limit (10/minute) must be enforced.
        """
        client, _ = async_client
        auth_payload = {"client_id": "demo-client", "client_secret": "wrong"}
        
        responses = []
        # Auth limit is 10/minute
        for _ in range(15):
            r = await client.post("/auth/token", json=auth_payload)
            responses.append(r)
            if r.status_code == 429:
                break
        
        status_codes = [r.status_code for r in responses]
        assert 429 in status_codes, "Auth endpoint should trigger 429 after ~10 attempts"
        
        r_429 = next(r for r in responses if r.status_code == 429)
        assert "Retry-After" in r_429.headers

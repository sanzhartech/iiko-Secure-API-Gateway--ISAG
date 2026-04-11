"""
tests/test_proxy.py — Secure Proxy Tests
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

from fastapi import HTTPException
import httpx
import pytest


@pytest.mark.asyncio
class TestProxy:

    async def test_successful_proxy_passes_through_status(
        self, async_client, make_token, test_settings
    ):
        """200 from iiko → gateway returns 200, body can be read as stream."""
        client, mock_iiko = async_client
        token = make_token(roles=["operator"])
        
        from contextlib import asynccontextmanager
        mock_response = httpx.Response(200, content=b'{"restaurants": []}')
        @asynccontextmanager
        async def _mock_cm(*args, **kwargs):
            yield mock_response
        from unittest.mock import MagicMock
        mock_iiko.proxy_request_stream = MagicMock(side_effect=_mock_cm)

        response = await client.get(
            "/api/v1/restaurants",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        # Body is already fully buffered by the ASGI test transport.
        # Use .content (bytes, synchronous) instead of await response.aread()
        # which is not available on a buffered httpx.Response. [Fix #7]
        assert response.content == b'{"restaurants": []}'

    async def test_upstream_timeout_returns_504(
        self, async_client, make_token, test_settings
    ):
        """Upstream timeout → 504, no internal error detail exposed."""
        client, mock_iiko = async_client
        token = make_token(roles=["operator"])
        
        # [Fix] Async exception on initial call outside of context manager
        from contextlib import asynccontextmanager
        @asynccontextmanager
        async def _mock_cm(*args, **kwargs):
            raise HTTPException(504, detail="Upstream service timed out")
            yield
        from unittest.mock import MagicMock
        mock_iiko.proxy_request_stream = MagicMock(side_effect=_mock_cm)

        response = await client.get(
            "/api/orders",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 504
        assert "internal error" not in response.text.lower()
        # [Fix] Verify upstream name is NOT leaked in body
        assert "iiko" not in response.text.lower()

    async def test_upstream_unavailable_returns_502(
        self, async_client, make_token, test_settings
    ):
        """Upstream connect error → 502, safe error message."""
        client, mock_iiko = async_client
        token = make_token(roles=["operator"])
        from contextlib import asynccontextmanager
        @asynccontextmanager
        async def _mock_cm(*args, **kwargs):
            raise HTTPException(502, detail="Upstream service unavailable")
            yield
        from unittest.mock import MagicMock
        mock_iiko.proxy_request_stream = MagicMock(side_effect=_mock_cm)

        response = await client.get(
            "/api/orders",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 502
        assert "upstream" in response.text.lower()

    async def test_client_authorization_not_forwarded(self, test_settings):
        """Client's Authorization header must NEVER reach iiko."""
        from app.services.iiko_client import IikoClient

        mock_settings = MagicMock()
        mock_settings.iiko_api_base_url = "https://fake-iiko.example.com"
        mock_settings.iiko_api_key = "server-side-key-secret"
        mock_settings.iiko_request_timeout_seconds = 5.0

        client_instance = IikoClient(mock_settings)
        # Avoid real httpx client init
        client_instance._client = MagicMock()

        mock_request = MagicMock()
        mock_request.headers = {
            "Authorization": "Bearer client-secret-should-fail",
            "Content-Type": "application/json",
        }

        safe_headers = client_instance._build_safe_headers(mock_request)
        # Client token must be replaced by server key
        assert safe_headers["Authorization"] == "Bearer server-side-key-secret"

    async def test_hop_by_hop_headers_stripped(self, test_settings):
        """Hop-by-hop headers must not be forwarded to upstream."""
        from app.services.iiko_client import IikoClient, _HOP_BY_HOP_HEADERS

        mock_settings = MagicMock()
        mock_settings.iiko_api_base_url = "https://fake-iiko.example.com"
        mock_settings.iiko_api_key = "key"
        mock_settings.iiko_request_timeout_seconds = 5.0

        client_instance = IikoClient(mock_settings)
        client_instance._client = MagicMock()

        mock_request = MagicMock()
        mock_request.headers = {
            "connection": "upgrade",
            "upgrade": "websocket",
            "Content-Type": "application/json",
        }

        safe_headers = client_instance._build_safe_headers(mock_request)
        for h in _HOP_BY_HOP_HEADERS:
            if h.lower() == "authorization":
                continue
            key_set = {k.lower() for k in safe_headers.keys()}
            assert h.lower() not in key_set

    async def test_unauthenticated_request_not_proxied(self, async_client):
        """Request without token must be rejected before reaching iiko."""
        client, mock_iiko = async_client
        mock_iiko.proxy_request_stream.reset_mock()
        response = await client.get("/api/orders")
        assert response.status_code in (401, 403)
        mock_iiko.proxy_request_stream.assert_not_called()

    async def test_server_headers_stripped_from_response(
        self, async_client, make_token, test_settings
    ):
        """'Server' and 'X-Powered-By' headers from iiko must not reach client."""
        client, mock_iiko = async_client
        token = make_token(roles=["operator"])

        mock_response = httpx.Response(
            200,
            content=b"{}",
            headers={
                "server": "nginx-upstream-version",
                "x-powered-by": "PHP",
                "transfer-encoding": "chunked",
            },
        )
        from contextlib import asynccontextmanager
        @asynccontextmanager
        async def _mock_cm(*args, **kwargs):
            yield mock_response
        from unittest.mock import MagicMock
        mock_iiko.proxy_request_stream = MagicMock(side_effect=_mock_cm)

        response = await client.get(
            "/api/orders",
            headers={"Authorization": f"Bearer {token}"},
        )

        # [Fix] Response headers must be stripped of revealing info
        assert "server" not in response.headers or response.headers.get("server") != "nginx-upstream-version"
        assert "x-powered-by" not in response.headers
        assert "transfer-encoding" not in response.headers or response.headers.get("transfer-encoding") != "chunked"

    async def test_refresh_token_rejected_for_proxy(self, async_client, make_token, test_settings):
        """Negative test: a refresh token cannot be used to call the proxy API."""
        client, mock_iiko = async_client
        mock_iiko.proxy_request_stream.reset_mock()
        token = make_token(token_type="refresh", roles=["operator"])
        
        response = await client.get(
            "/api/v1/restaurants",
            headers={"Authorization": f"Bearer {token}"},
        )
            
        assert response.status_code == 401
        assert "Invalid token type" in response.text or "Unauthorized" in response.text
        mock_iiko.proxy_request_stream.assert_not_called()

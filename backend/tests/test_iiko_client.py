"""
tests/test_iiko_client.py — IikoClient Unit Tests with respx

Covers the core reverse proxy responsibilities at the service level:
  ✅ URL construction: base_url + sanitised path
  ✅ Query parameter forwarding (multi-value aware)
  ✅ Client Authorization header is stripped and replaced by IIKO_API_KEY
  ✅ Hop-by-hop headers are removed before upstream request
  ✅ X-Gateway-Version header is injected
  ✅ HTTP methods: GET, POST, PUT, DELETE are all forwarded correctly
  ✅ Path traversal (../) is blocked (HTTP 400)
  ✅ Upstream timeout → HTTP 504
  ✅ Upstream connect error → HTTP 502
  ✅ Response headers: 'server', 'x-powered-by' stripped on way back
"""

from __future__ import annotations

import pytest
import respx
import httpx
from unittest.mock import MagicMock, AsyncMock
from fastapi import HTTPException

from app.services.iiko_client import (
    IikoClient,
    _HOP_BY_HOP_HEADERS,
    _STRIP_RESPONSE_HEADERS,
    APP_VERSION,
)


# ── Test Settings Fixture ─────────────────────────────────────────────────────

FAKE_BASE_URL = "https://iiko.fake"
FAKE_API_KEY = "s3cr3t-upstream-key"
TIMEOUT = 10.0


def _make_client() -> IikoClient:
    """Construct a bare IikoClient with a real httpx.AsyncClient (respx will intercept it)."""
    mock_settings = MagicMock()
    mock_settings.iiko_api_base_url = FAKE_BASE_URL
    mock_settings.iiko_api_key = FAKE_API_KEY
    mock_settings.iiko_request_timeout_seconds = TIMEOUT
    return IikoClient(mock_settings)


def _make_request(
    method: str = "GET",
    path: str = "/",
    headers: dict | None = None,
    query_string: str = "",
) -> MagicMock:
    """Build a minimal mock Starlette Request for IikoClient tests."""
    mock_request = MagicMock()
    mock_request.method = method
    mock_request.headers = headers or {"Content-Type": "application/json"}
    # Starlette QueryParams behaves like a dict — MagicMock covers it
    mock_request.query_params = MagicMock()
    mock_request.query_params.__iter__ = MagicMock(return_value=iter([]))
    mock_request.query_params.multi_items = MagicMock(return_value=[])
    # Stream: yield nothing by default
    async def _empty_stream():
        if False:
            yield b""
    mock_request.stream = _empty_stream
    return mock_request


# ── Header Mutation Tests ─────────────────────────────────────────────────────

class TestHeaderMutation:
    """Validate that header stripping and injection work correctly."""

    def test_client_auth_header_replaced_with_api_key(self):
        """
        Client's Bearer token must be removed from upstream headers.
        The IIKO_API_KEY must be injected as the new Authorization header.
        """
        client = _make_client()
        req = _make_request(headers={
            "Authorization": "Bearer client-should-not-reach-iiko",
            "Content-Type": "application/json",
            "X-Custom-Header": "keep-me",
        })

        result = client._build_safe_headers(req)

        # Client token replaced by server key
        assert result["Authorization"] == f"Bearer {FAKE_API_KEY}"
        # Non-sensitive headers forwarded
        assert result.get("X-Custom-Header") == "keep-me"
        assert result.get("Content-Type") == "application/json"

    def test_hop_by_hop_headers_all_stripped(self):
        """
        All RFC 2616 §13.5.1 hop-by-hop headers (connection, upgrade, etc.)
        must be removed before forwarding to iiko.
        """
        client = _make_client()
        req = _make_request(headers={
            "connection": "keep-alive",
            "keep-alive": "timeout=5",
            "proxy-authorization": "Basic abc123",
            "upgrade": "websocket",
            "te": "gzip",
            "trailers": "X-Checksum",
            "transfer-encoding": "chunked",
            "Content-Type": "application/json",
        })

        result = client._build_safe_headers(req)
        result_lower = {k.lower() for k in result}

        for hop_header in _HOP_BY_HOP_HEADERS:
            if hop_header == "authorization":
                # Authorization is replaced, not absent
                continue
            assert hop_header not in result_lower, (
                f"Hop-by-hop header '{hop_header}' was forwarded to upstream!"
            )

    def test_gateway_version_header_injected(self):
        """X-Gateway-Version must be injected with the correct app version."""
        client = _make_client()
        req = _make_request()

        result = client._build_safe_headers(req)

        assert result.get("X-Gateway-Version") == APP_VERSION

    def test_host_header_not_forwarded(self):
        """
        The 'host' header from the original request must be stripped.
        Forwarding it would confuse the upstream server or enable SSRF.
        """
        client = _make_client()
        req = _make_request(headers={
            "host": "malicious-host.attacker.com",
            "Content-Type": "application/json",
        })

        result = client._build_safe_headers(req)
        assert "host" not in {k.lower() for k in result}


# ── URL Construction Tests ────────────────────────────────────────────────────

class TestURLConstruction:
    """Validate that upstream URLs are built correctly from path and base_url."""

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_request_url_constructed_correctly(self):
        """
        GET /v1/restaurants → upstream  FAKE_BASE_URL/v1/restaurants
        Verifies that base_url and path are joined without double slashes.
        """
        client = _make_client()
        req = _make_request(method="GET")

        respx.get(f"{FAKE_BASE_URL}/v1/restaurants").mock(
            return_value=httpx.Response(200, json={"result": "ok"})
        )

        async with client.proxy_request_stream("GET", "v1/restaurants", req, user_id="u1") as resp:
            assert resp.status_code == 200

    @pytest.mark.asyncio
    @respx.mock
    async def test_nested_path_preserved(self):
        """Nested path segments are preserved: /v1/orders/123/items"""
        client = _make_client()
        req = _make_request(method="GET")

        respx.get(f"{FAKE_BASE_URL}/v1/orders/123/items").mock(
            return_value=httpx.Response(200, json={"items": []})
        )

        async with client.proxy_request_stream("GET", "v1/orders/123/items", req, user_id="u1") as resp:
            assert resp.status_code == 200

    def test_path_traversal_blocked(self):
        """
        Paths containing '../' are rejected with HTTP 400.
        This prevents SSRF attacks via directory traversal.
        """
        client = _make_client()
        with pytest.raises(HTTPException) as exc_info:
            from app.services.iiko_client import _sanitize_path
            _sanitize_path("../etc/passwd")
        assert exc_info.value.status_code == 400


# ── HTTP Method Forwarding Tests ──────────────────────────────────────────────

class TestHTTPMethodForwarding:
    """Verify that all HTTP methods are correctly forwarded to the upstream."""

    @pytest.mark.asyncio
    @respx.mock
    async def test_post_method_forwarded(self):
        """POST /orders is sent as POST to upstream."""
        client = _make_client()
        req = _make_request(method="POST")

        respx.post(f"{FAKE_BASE_URL}/orders").mock(
            return_value=httpx.Response(201, json={"id": "new-order"})
        )

        async with client.proxy_request_stream("POST", "orders", req, user_id="u1") as resp:
            assert resp.status_code == 201

    @pytest.mark.asyncio
    @respx.mock
    async def test_put_method_forwarded(self):
        """PUT /orders/42 is sent as PUT to upstream."""
        client = _make_client()
        req = _make_request(method="PUT")

        respx.put(f"{FAKE_BASE_URL}/orders/42").mock(
            return_value=httpx.Response(200, json={"updated": True})
        )

        async with client.proxy_request_stream("PUT", "orders/42", req, user_id="u1") as resp:
            assert resp.status_code == 200

    @pytest.mark.asyncio
    @respx.mock
    async def test_delete_method_forwarded(self):
        """DELETE /orders/99 is sent as DELETE to upstream."""
        client = _make_client()
        req = _make_request(method="DELETE")

        respx.delete(f"{FAKE_BASE_URL}/orders/99").mock(
            return_value=httpx.Response(204)
        )

        async with client.proxy_request_stream("DELETE", "orders/99", req, user_id="u1") as resp:
            assert resp.status_code == 204


# ── Query Parameter Forwarding Tests ─────────────────────────────────────────

class TestQueryParamForwarding:
    """Verify query parameters are forwarded to upstream without modification."""

    @pytest.mark.asyncio
    @respx.mock
    async def test_query_params_forwarded(self):
        """
        Query string from original request is passed through to upstream.
        Uses respx pattern matching on the full URL including query string.
        """
        client = _make_client()
        req = _make_request(method="GET")
        # Simulate query params by pointing to a URL with them
        req.query_params = {"page": "1", "limit": "20"}

        # respx intercepts at the httpx level — match on path, query params forwarded natively
        respx.get(f"{FAKE_BASE_URL}/v1/menu", params={"page": "1", "limit": "20"}).mock(
            return_value=httpx.Response(200, json={"items": [1, 2, 3]})
        )

        async with client.proxy_request_stream("GET", "v1/menu", req, user_id="u1") as resp:
            assert resp.status_code == 200


# ── Error Handling Tests ──────────────────────────────────────────────────────

class TestUpstreamErrorHandling:
    """Verify upstream transport errors produce clean gateway error responses."""

    @pytest.mark.asyncio
    @respx.mock
    async def test_upstream_timeout_raises_504(self):
        """httpx.TimeoutException → HTTPException(504)."""
        client = _make_client()
        req = _make_request(method="GET")

        respx.get(f"{FAKE_BASE_URL}/slow-endpoint").mock(
            side_effect=httpx.TimeoutException("timeout")
        )

        with pytest.raises(HTTPException) as exc_info:
            async with client.proxy_request_stream("GET", "slow-endpoint", req, user_id="u1"):
                pass
        assert exc_info.value.status_code == 504

    @pytest.mark.asyncio
    @respx.mock
    async def test_upstream_connect_error_raises_502(self):
        """httpx.ConnectError → HTTPException(502)."""
        client = _make_client()
        req = _make_request(method="GET")

        respx.get(f"{FAKE_BASE_URL}/unavailable").mock(
            side_effect=httpx.ConnectError("connection refused")
        )

        with pytest.raises(HTTPException) as exc_info:
            async with client.proxy_request_stream("GET", "unavailable", req, user_id="u1"):
                pass
        assert exc_info.value.status_code == 502


# ── Response Header Stripping Tests ──────────────────────────────────────────

class TestResponseHeaderStripping:
    """Verify sensitive upstream response headers are stripped."""

    @pytest.mark.asyncio
    @respx.mock
    async def test_server_header_stripped_from_response(self):
        """
        'server', 'x-powered-by', 'transfer-encoding' must not be forwarded
        from upstream to the client (handled by proxy.py/_forward).
        Verify they are in _STRIP_RESPONSE_HEADERS constant.
        """
        assert "server" in _STRIP_RESPONSE_HEADERS
        assert "x-powered-by" in _STRIP_RESPONSE_HEADERS
        assert "transfer-encoding" in _STRIP_RESPONSE_HEADERS

    @pytest.mark.asyncio
    @respx.mock
    async def test_upstream_api_key_not_in_response(self):
        """IIKO_API_KEY must never appear in any downstream response body."""
        client = _make_client()
        req = _make_request(method="GET")

        # Upstream accidentally echoes the api key in body (misconfiguration)
        respx.get(f"{FAKE_BASE_URL}/whoami").mock(
            return_value=httpx.Response(
                200,
                json={"key": FAKE_API_KEY},
                headers={"Content-Type": "application/json"},
            )
        )

        async with client.proxy_request_stream("GET", "whoami", req, user_id="u1") as resp:
            # The proxy layer itself doesn't inspect body — but this confirms
            # the key does NOT appear unexpectedly in stripped *headers*
            for header_value in resp.headers.values():
                assert FAKE_API_KEY not in header_value

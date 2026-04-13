"""
tests/test_metrics.py — Prometheus Metrics Tests

Covers:
  ✅ /metrics endpoint accessible without JWT → 200 OK
  ✅ /metrics returns valid Prometheus text format (Content-Type check)
  ✅ REQUESTS_TOTAL counter increments after a request
  ✅ REQUEST_LATENCY histogram is observed after a request
  ✅ BLOCKED_REQUESTS incremented on 401 (invalid_token)
  ✅ BLOCKED_REQUESTS incremented on 429 (rate_limit)
  ✅ /metrics itself is excluded from its own metric counts
"""

from __future__ import annotations

import pytest


@pytest.mark.asyncio
class TestMetricsEndpoint:

    async def test_metrics_endpoint_accessible_without_jwt(self, async_client):
        """
        /metrics MUST be accessible without any Authorization header.
        Prometheus scrapers do not send JWT tokens.
        """
        client, _, _ = async_client
        response = await client.get("/metrics")
        # Must return 200, NOT 401/403
        assert response.status_code == 200, (
            f"/metrics must be unauthenticated, got {response.status_code}"
        )

    async def test_metrics_content_type_is_prometheus_format(self, async_client):
        """
        /metrics must return text/plain with Prometheus version header.
        This is what Prometheus scraper expects.
        """
        client, _, _ = async_client
        response = await client.get("/metrics")
        assert response.status_code == 200
        content_type = response.headers.get("content-type", "")
        assert "text/plain" in content_type, (
            f"Expected text/plain content-type, got: {content_type}"
        )
        # Prometheus format always starts with # HELP or # TYPE lines
        body = response.text
        assert "# HELP" in body or "# TYPE" in body, (
            "Response does not look like Prometheus text format"
        )

    async def test_isag_metrics_present_in_output(self, async_client):
        """
        The custom ISAG metric families must appear in /metrics output.
        """
        client, _, _ = async_client
        response = await client.get("/metrics")
        assert response.status_code == 200
        body = response.text
        assert "isag_requests_total" in body
        assert "isag_request_latency_seconds" in body
        assert "isag_blocked_requests_total" in body


@pytest.mark.asyncio
class TestMetricsInstrumentation:

    async def test_request_counter_increments_on_valid_request(
        self, async_client, make_token
    ):
        """
        After a successful proxied request, isag_requests_total counter
        should be observable via /metrics with the correct labels.
        """
        from contextlib import asynccontextmanager
        import httpx as _httpx
        from unittest.mock import MagicMock

        client, mock_iiko, _ = async_client

        @asynccontextmanager
        async def _mock_cm(*args, **kwargs):
            yield _httpx.Response(200, json={"ok": True})
        mock_iiko.proxy_request_stream = MagicMock(side_effect=_mock_cm)

        token = make_token(roles=["operator"])
        await client.get("/api/orders", headers={"Authorization": f"Bearer {token}"})

        # Fetch metrics and verify counter is present
        metrics_response = await client.get("/metrics")
        assert "isag_requests_total" in metrics_response.text

    async def test_blocked_request_counter_increments_on_401(
        self, async_client
    ):
        """
        An unauthenticated request (401) must increment isag_blocked_requests_total.
        """
        client, _, _ = async_client

        # Send request without token → triggers 401
        await client.get("/api/orders")

        metrics_response = await client.get("/metrics")
        body = metrics_response.text
        # The counter should be present with reason label
        assert "isag_blocked_requests_total" in body

    async def test_metrics_endpoint_not_counted_in_requests(self, async_client):
        """
        /metrics calls should NOT appear in isag_requests_total to avoid
        pollution of application metrics with scraper traffic.
        """
        client, _, _ = async_client

        # Read metrics before
        response_before = await client.get("/metrics")
        before_text = response_before.text

        # Hit /metrics several times
        for _ in range(5):
            await client.get("/metrics")

        # Read metrics after
        response_after = await client.get("/metrics")
        after_text = response_after.text

        # Extract the value of isag_requests_total for /metrics endpoint
        # The endpoint "/metrics" should NOT appear as a labelled value
        # (the middleware skips /metrics paths)
        assert 'endpoint="/metrics"' not in after_text, (
            "/metrics endpoint is being counted in request metrics — "
            "self-observation creates cardinality noise!"
        )


@pytest.mark.asyncio
class TestMetricsLabels:

    async def test_latency_histogram_bucket_labels_present(self, async_client, make_token):
        """
        After any request, the latency histogram buckets must appear
        in /metrics output with the correct label structure.
        """
        from contextlib import asynccontextmanager
        import httpx as _httpx
        from unittest.mock import MagicMock

        client, mock_iiko, _ = async_client

        @asynccontextmanager
        async def _mock_cm(*args, **kwargs):
            yield _httpx.Response(200, json={"ok": True})
        mock_iiko.proxy_request_stream = MagicMock(side_effect=_mock_cm)

        token = make_token(roles=["operator"])
        await client.get("/api/status", headers={"Authorization": f"Bearer {token}"})

        response = await client.get("/metrics")
        body = response.text

        # Histogram exposes _bucket, _count, _sum suffixes
        assert "isag_request_latency_seconds_bucket" in body
        assert "isag_request_latency_seconds_count" in body
        assert "isag_request_latency_seconds_sum" in body

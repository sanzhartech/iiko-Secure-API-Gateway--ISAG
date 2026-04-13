"""
core/metrics.py — Prometheus Metrics Registry

Defines all gateway-level metrics as module-level singletons.
Importing this module is safe — metrics are registered once on first import.

Metrics exposed:
  isag_requests_total         Counter  — total requests by method/endpoint/status
  isag_request_latency_seconds Histogram — request duration to upstream
  isag_blocked_requests_total Counter  — blocked requests by reason

Usage:
    from app.core.metrics import REQUESTS_TOTAL, REQUEST_LATENCY, BLOCKED_REQUESTS

    # Increment a counter
    REQUESTS_TOTAL.labels(method="GET", endpoint="/api/orders", status_code=200).inc()

    # Record a histogram observation (seconds)
    REQUEST_LATENCY.labels(method="GET", endpoint="/api/orders").observe(0.123)

    # Record a blocked request
    BLOCKED_REQUESTS.labels(reason="invalid_token").inc()
"""

from __future__ import annotations

from prometheus_client import Counter, Histogram, CollectorRegistry, REGISTRY

# ── Label Definitions ─────────────────────────────────────────────────────────

# All valid block reasons — used as label values for BLOCKED_REQUESTS
BLOCK_REASON_RATE_LIMIT = "rate_limit"
BLOCK_REASON_INVALID_TOKEN = "invalid_token"
BLOCK_REASON_REPLAY_ATTACK = "replay_attack"
BLOCK_REASON_FORBIDDEN = "forbidden"
BLOCK_REASON_REQUEST_TOO_LARGE = "request_too_large"
BLOCK_REASON_PATH_TRAVERSAL = "path_traversal"

# ── Metric Definitions ────────────────────────────────────────────────────────

REQUESTS_TOTAL = Counter(
    name="isag_requests_total",
    documentation=(
        "Total number of HTTP requests processed by the ISAG gateway. "
        "Labels: method (HTTP verb), endpoint (normalised path), status_code."
    ),
    labelnames=["method", "endpoint", "status_code"],
)
"""Counter: total gateway requests, labelled by HTTP method, endpoint, and status code."""

REQUEST_LATENCY = Histogram(
    name="isag_request_latency_seconds",
    documentation=(
        "End-to-end request latency measured by the metrics middleware. "
        "Labels: method, endpoint."
    ),
    labelnames=["method", "endpoint"],
    # Buckets: 5ms → 2s gives granularity useful for SLO alerting
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.0),
)
"""Histogram: request latency in seconds, labelled by method and endpoint."""

BLOCKED_REQUESTS = Counter(
    name="isag_blocked_requests_total",
    documentation=(
        "Total number of requests blocked by any security stage. "
        "Labels: reason — one of: rate_limit, invalid_token, replay_attack, "
        "forbidden, request_too_large, path_traversal."
    ),
    labelnames=["reason"],
)
"""Counter: blocked requests, labelled by rejection reason."""

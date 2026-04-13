#!/usr/bin/env python3
"""
scripts/stress_test.py — ISAG Gateway Mixed-Traffic Stress Test

Simulates 4 traffic archetypes against a running ISAG gateway to exercise
every security metric counter and produce visible signals on Grafana:

  1. LEGITIMATE   — Valid RS256 tokens with unique JTIs — passes through
  2. NO-AUTH      — Requests with no Authorization header — invalid_token ++
  3. DDOS BURST   — Rapid-fire requests from the same user — rate_limit ++
  4. REPLAY       — Same token sent twice in a row — replay_attack ++

Usage:
    # Start the stack first:
    #   docker-compose up -d --build
    #
    python scripts/stress_test.py [--url http://localhost:8000] [--duration 120]

Dependencies:
    pip install httpx cryptography python-jose[cryptography]

Configuration via environment variables or CLI flags:
    GATEWAY_URL          Base URL of the gateway (default: http://localhost:8000)
    STRESS_CLIENT_ID     Client ID to authenticate with (default: demo-client)
    STRESS_CLIENT_SECRET Client secret for the demo client
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import httpx
from jose import jwt


# ── Configuration ─────────────────────────────────────────────────────────────

DEFAULT_GATEWAY_URL = "http://localhost:8000"
DEFAULT_DURATION_SECONDS = 120
DEFAULT_CONCURRENCY = 5

# Loaded from environment if available
CLIENT_ID = os.getenv("STRESS_CLIENT_ID", "demo-client")
CLIENT_SECRET = os.getenv("STRESS_CLIENT_SECRET", "super-secure-placeholder-secret-strictly-32-chars-long")

# JWT parameters — must match the gateway's .env
JWT_ISSUER = os.getenv("JWT_ISSUER", "isag.internal")
JWT_AUDIENCE = os.getenv("JWT_AUDIENCE", "isag-clients")
JWT_KEY_PATH = os.getenv("JWT_PRIVATE_KEY_PATH", "./backend/keys/private.pem")
JWT_KID = os.getenv("JWT_ACTIVE_KID", "default")

# Proxy path to target — must exist on the upstream or return an expected error
TARGET_PATH = "/api/health"

# ── Counters ──────────────────────────────────────────────────────────────────

@dataclass
class TrafficStats:
    """Accumulates per-archetype results for final report."""
    sent: int = 0
    ok: int = 0         # 2xx
    blocked: int = 0    # 401, 403, 429
    error: int = 0      # 5xx / network
    statuses: dict[int, int] = field(default_factory=dict)

    def record(self, status: int) -> None:
        self.sent += 1
        self.statuses[status] = self.statuses.get(status, 0) + 1
        if 200 <= status < 300:
            self.ok += 1
        elif status in (401, 403, 429):
            self.blocked += 1
        else:
            self.error += 1


# ── JWT Helpers ───────────────────────────────────────────────────────────────

def _load_private_key() -> str | None:
    """Load the RSA private key from disk, or return None if not found."""
    p = Path(JWT_KEY_PATH)
    if not p.exists():
        # Try relative to script location
        alt = Path(__file__).parent.parent / "backend" / "keys" / "private.pem"
        if alt.exists():
            p = alt
        else:
            return None
    return p.read_text(encoding="utf-8")


def _mint_token(private_key: str, sub: str = "stress-tester", jti: str | None = None) -> str:
    """
    Mint a fresh RS256 access token with a unique JTI.
    Each call produces a token that defeats replay protection.
    """
    now = datetime.now(tz=timezone.utc)
    exp = now + timedelta(minutes=15)
    return jwt.encode(
        {
            "type": "access",
            "iss": JWT_ISSUER,
            "aud": JWT_AUDIENCE,
            "sub": sub,
            "roles": ["operator"],
            "exp": int(exp.timestamp()),
            "iat": int(now.timestamp()),
            "jti": jti or uuid.uuid4().hex,
        },
        private_key,
        algorithm="RS256",
        headers={"kid": JWT_KID},
    )


# ── Traffic Archetypes ────────────────────────────────────────────────────────

async def _send(client: httpx.AsyncClient, url: str, headers: dict) -> int:
    """Send a single GET request and return the HTTP status code."""
    try:
        r = await client.get(url, headers=headers, timeout=5.0)
        return r.status_code
    except httpx.TimeoutException:
        return 504
    except httpx.NetworkError:
        return 0


async def run_legitimate(
    client: httpx.AsyncClient,
    base_url: str,
    private_key: str,
    stats: TrafficStats,
    count: int,
) -> None:
    """
    Archetype 1 — LEGITIMATE TRAFFIC
    Sends `count` requests each with a fresh token (unique JTI).
    Expected: all pass → 200 or forwarded upstream status.
    Prometheus: isag_requests_total{status_code="200"} ↑
    """
    print(f"  [LEGIT] Sending {count} legitimate requests…")
    for _ in range(count):
        token = _mint_token(private_key)
        status = await _send(client, f"{base_url}{TARGET_PATH}", {"Authorization": f"Bearer {token}"})
        stats.record(status)
        await asyncio.sleep(0.1)


async def run_no_auth(
    client: httpx.AsyncClient,
    base_url: str,
    stats: TrafficStats,
    count: int,
) -> None:
    """
    Archetype 2 — NO AUTH ATTACKS
    Sends requests with no Authorization header.
    Expected: 401 on every request.
    Prometheus: isag_blocked_requests_total{reason="invalid_token"} ↑
    """
    print(f"  [NO-AUTH] Sending {count} unauthenticated requests…")
    for _ in range(count):
        status = await _send(client, f"{base_url}{TARGET_PATH}", {})
        stats.record(status)
        await asyncio.sleep(0.05)


async def run_ddos_burst(
    client: httpx.AsyncClient,
    base_url: str,
    private_key: str,
    stats: TrafficStats,
    burst_size: int,
) -> None:
    """
    Archetype 3 — DDOS / RATE ABUSE
    Fires burst_size concurrent requests from the same user sub.
    Designed to exceed the per-user limit (50/min) quickly.
    Expected: first ~50 pass, then 429.
    Prometheus: isag_blocked_requests_total{reason="rate_limit"} ↑
    """
    print(f"  [DDOS] Firing burst of {burst_size} concurrent requests…")
    # Use the same sub but unique JTIs to avoid replay detection
    tasks = [
        _send(
            client,
            f"{base_url}{TARGET_PATH}",
            {"Authorization": f"Bearer {_mint_token(private_key, sub='ddos-attacker')}"},
        )
        for _ in range(burst_size)
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    for r in results:
        status = r if isinstance(r, int) else 0
        stats.record(status)


async def run_replay_attack(
    client: httpx.AsyncClient,
    base_url: str,
    private_key: str,
    stats: TrafficStats,
    count: int,
) -> None:
    """
    Archetype 4 — REPLAY ATTACKS
    Mints a single token, then sends it `count` times.
    First use should succeed; subsequent uses must return 401.
    Prometheus: isag_blocked_requests_total{reason="replay_attack"} ↑
    """
    print(f"  [REPLAY] Replaying same token {count} times…")
    # Single token — fixed JTI shared across all sends
    replay_jti = uuid.uuid4().hex
    token = _mint_token(private_key, sub="replay-attacker", jti=replay_jti)
    headers = {"Authorization": f"Bearer {token}"}

    for i in range(count):
        status = await _send(client, f"{base_url}{TARGET_PATH}", headers)
        stats.record(status)
        label = "✓ PASS (first use)" if i == 0 else f"✗ BLOCKED ({status})"
        print(f"    replay #{i+1}: {label}")
        await asyncio.sleep(0.2)


# ── Main Loop ─────────────────────────────────────────────────────────────────

async def run_stress_test(gateway_url: str, duration: int) -> None:
    """Main stress test loop — runs until `duration` seconds elapse."""
    print(f"\n{'='*60}")
    print(f"  ISAG Gateway Stress Test")
    print(f"  Target:   {gateway_url}")
    print(f"  Duration: {duration}s")
    print(f"{'='*60}\n")

    private_key = _load_private_key()
    if private_key is None:
        print(
            "ERROR: Could not find RSA private key.\n"
            f"  Expected at: {JWT_KEY_PATH}\n"
            "  Run: python backend/scripts/generate_keys.py\n"
            "  Or set JWT_PRIVATE_KEY_PATH env var.",
            file=sys.stderr,
        )
        sys.exit(1)

    # Verify gateway is reachable
    try:
        async with httpx.AsyncClient() as probe:
            r = await probe.get(f"{gateway_url}/health", timeout=5)
            if r.status_code != 200:
                print(f"WARNING: /health returned {r.status_code}")
            else:
                print(f"✓ Gateway is reachable at {gateway_url}\n")
    except Exception as e:
        print(f"ERROR: Cannot reach gateway at {gateway_url}: {e}", file=sys.stderr)
        sys.exit(1)

    stats = {
        "legitimate": TrafficStats(),
        "no_auth": TrafficStats(),
        "ddos": TrafficStats(),
        "replay": TrafficStats(),
    }

    start_time = time.monotonic()
    round_num = 0

    limits = httpx.Limits(max_connections=200, max_keepalive_connections=50)
    async with httpx.AsyncClient(limits=limits) as client:
        while time.monotonic() - start_time < duration:
            round_num += 1
            elapsed = int(time.monotonic() - start_time)
            remaining = duration - elapsed
            print(f"\n── Round {round_num} (elapsed {elapsed}s, {remaining}s left) ──")

            # Alternate archetypes each round for good Prometheus signal diversity
            await run_legitimate(client, gateway_url, private_key, stats["legitimate"], count=10)
            await run_no_auth(client, gateway_url, stats["no_auth"], count=5)
            await run_ddos_burst(client, gateway_url, private_key, stats["ddos"], burst_size=60)
            await run_replay_attack(client, gateway_url, private_key, stats["replay"], count=4)

            await asyncio.sleep(2)  # Brief pause between rounds

    # ── Final Report ─────────────────────────────────────────────────────────
    total_elapsed = time.monotonic() - start_time
    print(f"\n{'='*60}")
    print(f"  Stress Test Complete — {total_elapsed:.1f}s, {round_num} rounds")
    print(f"{'='*60}")
    print(f"  {'Archetype':<20} {'Sent':>6} {'OK(2xx)':>8} {'Blocked':>8} {'Error':>8}")
    print(f"  {'-'*52}")
    for name, s in stats.items():
        print(f"  {name:<20} {s.sent:>6} {s.ok:>8} {s.blocked:>8} {s.error:>8}")

    print(f"\n  Status code breakdown:")
    all_statuses: dict[int, int] = {}
    for s in stats.values():
        for code, count in s.statuses.items():
            all_statuses[code] = all_statuses.get(code, 0) + count
    for code, count in sorted(all_statuses.items()):
        bar = "█" * min(40, count // 2)
        print(f"  HTTP {code:3d}: {count:>5}  {bar}")

    print(f"\n  View metrics at: {gateway_url}/metrics")
    print(f"  Grafana:        http://localhost:3000  (admin / isag-grafana-2024)")
    print(f"{'='*60}\n")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="ISAG Gateway Mixed-Traffic Stress Test",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--url",
        default=os.getenv("GATEWAY_URL", DEFAULT_GATEWAY_URL),
        help=f"Gateway base URL (default: {DEFAULT_GATEWAY_URL})",
    )
    parser.add_argument(
        "--duration",
        type=int,
        default=DEFAULT_DURATION_SECONDS,
        help=f"Test duration in seconds (default: {DEFAULT_DURATION_SECONDS})",
    )
    args = parser.parse_args()

    asyncio.run(run_stress_test(args.url, args.duration))


if __name__ == "__main__":
    main()

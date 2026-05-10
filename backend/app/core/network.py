"""
core/network.py — Centralized Client IP Resolution Helper

PURPOSE:
    Provides a single, canonical function for extracting the real client IP
    address from an incoming HTTP request. This prevents IP spoofing via
    forged X-Forwarded-For headers in admin endpoints and other places that
    need to record or rate-limit by client IP.

SECURITY DESIGN:
    - X-Forwarded-For is ONLY trusted when the direct TCP connection arrives
      from a CIDR listed in TRUSTED_PROXY_CIDRS (configured in settings).
    - If the direct peer is NOT a trusted proxy, the raw connection IP is
      returned — the X-Forwarded-For header is completely ignored.
    - This closes the IP-spoofing vector where a malicious client sends
      e.g. "X-Forwarded-For: 127.0.0.1" directly to the gateway.

USAGE:
    from app.core.network import get_client_ip

    ip = get_client_ip(request, trusted_cidrs=settings.trusted_proxy_cidrs_list)
"""

from __future__ import annotations

import ipaddress

from starlette.requests import Request


def _is_trusted_proxy(
    host: str,
    trusted_networks: list[ipaddress.IPv4Network | ipaddress.IPv6Network],
) -> bool:
    """Return True if *host* falls within one of the trusted proxy networks."""
    if not trusted_networks:
        return False
    try:
        addr = ipaddress.ip_address(host)
        return any(addr in net for net in trusted_networks)
    except ValueError:
        return False


def get_client_ip(
    request: Request,
    trusted_cidrs: list[str] | None = None,
) -> str:
    """
    Extract the real client IP address from *request*.

    Args:
        request:       The incoming Starlette/FastAPI request object.
        trusted_cidrs: List of CIDR strings representing trusted reverse
                       proxies (e.g. ``["10.0.0.0/8", "172.16.0.0/12"]``).
                       When *None* or empty, X-Forwarded-For is NEVER trusted.

    Returns:
        The client IP string. Falls back to ``"unknown"`` when no peer
        address is available (e.g. unit-test mocks without a transport).

    Security contract:
        - X-Forwarded-For is honoured ONLY when the TCP peer IP is listed in
          *trusted_cidrs*.
        - The leftmost entry of X-Forwarded-For is used (original client).
        - All other cases return ``request.client.host`` directly.
    """
    direct_ip: str = request.client.host if request.client else "unknown"

    # Parse CIDR strings to network objects (cheap for small lists)
    trusted_networks: list[ipaddress.IPv4Network | ipaddress.IPv6Network] = []
    for cidr in (trusted_cidrs or []):
        try:
            trusted_networks.append(ipaddress.ip_network(cidr, strict=False))
        except ValueError:
            # Silently skip malformed CIDRs — they were already warned at startup
            pass

    if _is_trusted_proxy(direct_ip, trusted_networks):
        forwarded_for = request.headers.get("x-forwarded-for", "")
        if forwarded_for:
            # RFC 7239: leftmost entry is the original client address
            return forwarded_for.split(",")[0].strip()

    return direct_ip

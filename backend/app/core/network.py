from __future__ import annotations

import ipaddress
from typing import Iterable

from fastapi import Request


def compile_trusted_networks(
    cidrs: Iterable[str],
) -> list[ipaddress.IPv4Network | ipaddress.IPv6Network]:
    """Parse configured proxy CIDRs once and ignore invalid entries upstream."""
    networks: list[ipaddress.IPv4Network | ipaddress.IPv6Network] = []
    for cidr in cidrs:
        try:
            networks.append(ipaddress.ip_network(cidr, strict=False))
        except ValueError:
            continue
    return networks


def extract_client_ip(
    request: Request,
    trusted_networks: Iterable[ipaddress.IPv4Network | ipaddress.IPv6Network],
) -> str:
    """
    Return the best-known client IP.

    X-Forwarded-For is honoured only when the direct peer belongs to one of the
    explicitly trusted proxy networks. Otherwise the direct connection address is
    returned, which keeps spoofed forwarding headers from polluting audit data.
    """
    direct_ip = request.client.host if request.client else "unknown"

    try:
        direct_addr = ipaddress.ip_address(direct_ip)
    except ValueError:
        return direct_ip

    if any(direct_addr in network for network in trusted_networks):
        forwarded_for = request.headers.get("x-forwarded-for", "")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

    return direct_ip

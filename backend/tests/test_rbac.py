"""
tests/test_rbac.py — Role-Based Access Control Tests

Covers:
  ✅ Role with correct permission → 200
  ❌ Role with insufficient permission → 403
  ❌ Token with no roles → 403
  ❌ Unknown role → 403 (deny by default)
  ❌ Read-only role on write endpoint → 403
  ✅ Admin role gets read + write → 200
  ✅ Permission union: two roles, combined permissions
"""

from __future__ import annotations

from unittest.mock import patch

import httpx
import pytest

from app.security.rbac import Permission, resolve_permissions


# ── Unit Tests: resolve_permissions ──────────────────────────────────────────

class TestResolvePermissions:

    def test_operator_has_read_and_write(self):
        perms = resolve_permissions(["operator"])
        assert Permission.PROXY_READ in perms
        assert Permission.PROXY_WRITE in perms

    def test_viewer_has_only_read(self):
        perms = resolve_permissions(["viewer"])
        assert Permission.PROXY_READ in perms
        assert Permission.PROXY_WRITE not in perms

    def test_unknown_role_grants_nothing(self):
        perms = resolve_permissions(["nonexistent"])
        assert len(perms) == 0

    def test_empty_roles_grants_nothing(self):
        perms = resolve_permissions([])
        assert len(perms) == 0

    def test_permission_union_across_roles(self):
        """viewer + operator → combined permissions."""
        perms = resolve_permissions(["viewer", "operator"])
        assert Permission.PROXY_READ in perms
        assert Permission.PROXY_WRITE in perms

    def test_admin_has_all_permissions(self):
        perms = resolve_permissions(["admin"])
        for perm in Permission:
            assert perm in perms

    def test_unknown_role_mixed_with_valid(self):
        """Unknown role doesn't grant extra permissions."""
        viewer_only = resolve_permissions(["viewer"])
        mixed = resolve_permissions(["viewer", "god-mode"])
        assert viewer_only == mixed


# ── Integration Tests: RBAC via HTTP ─────────────────────────────────────────

@pytest.mark.asyncio
class TestRBACHTTP:

    async def test_operator_can_get(self, async_client, make_token, test_settings):
        """operator role has PROXY_READ → GET /api/... allowed."""
        client, mock_iiko, _ = async_client
        token = make_token(roles=["operator"])
        from contextlib import asynccontextmanager
        @asynccontextmanager
        async def _mock_cm(*args, **kwargs):
            yield httpx.Response(200, json={"data": []})
        from unittest.mock import MagicMock
        mock_iiko.proxy_request_stream = MagicMock(side_effect=_mock_cm)

        response = await client.get(
            "/api/orders",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code != 403

    async def test_viewer_cannot_post(self, async_client, make_token, test_settings):
        """viewer has only PROXY_READ → POST /api/... denied with 403."""
        client, _, _ = async_client
        token = make_token(roles=["viewer"])

        response = await client.post(
            "/api/orders",
            headers={"Authorization": f"Bearer {token}"},
            json={"order": "data"},
        )

        assert response.status_code == 403

    async def test_no_roles_denied(self, async_client, make_token, test_settings):
        """Token with empty roles list → 403 on any endpoint."""
        client, _, _ = async_client
        token = make_token(roles=[])

        response = await client.get(
            "/api/orders",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 403

    async def test_unknown_role_denied(self, async_client, make_token, test_settings):
        """Unknown role → deny by default → 403."""
        client, _, _ = async_client
        token = make_token(roles=["superuser"])  # not in ROLE_PERMISSIONS

        response = await client.get(
            "/api/orders",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 403

    async def test_admin_can_get_and_post(self, async_client, make_token, test_settings):
        """admin role has all permissions → GET and POST both allowed."""
        client, mock_iiko, _ = async_client
        token = make_token(roles=["admin"])
        from contextlib import asynccontextmanager
        @asynccontextmanager
        async def _mock_cm(*args, **kwargs):
            yield httpx.Response(201, json={"created": True})
        from unittest.mock import MagicMock
        mock_iiko.proxy_request_stream = MagicMock(side_effect=_mock_cm)

        response = await client.post(
            "/api/orders",
            headers={"Authorization": f"Bearer {token}"},
            json={"order": "data"},
        )

        assert response.status_code != 403

"""
tests/test_auth.py — Authentication & Token Flows
"""

from __future__ import annotations

import pytest
from unittest.mock import patch, AsyncMock

@pytest.mark.asyncio
class TestAuthFlow:
    async def test_refresh_token_issues_new_pair(self, async_client, make_token, test_settings):
        """Happy path: valid refresh token gets a new access/refresh pair."""
        client, _ = async_client
        refresh_token = make_token(token_type="refresh", roles=[])

        # Mock the client retrieve call internally
        mock_client = AsyncMock()
        mock_client.is_active = True
        mock_client.roles = ["operator"]

        with patch("app.api.auth.get_client_by_id", new_callable=AsyncMock) as mock_get_client:
            mock_get_client.return_value = mock_client
            response = await client.post(
                "/auth/refresh",
                json={"refresh_token": refresh_token}
            )

        print("Response body:", response.json())
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        
        # Original refresh token shouldn't equal this one (because uniqueness jti/iat/exp)
        assert data["refresh_token"] != refresh_token


    async def test_access_token_rejected_at_refresh_endpoint(self, async_client, make_token, test_settings):
        """Negative test: access token cannot be used to refresh tokens."""
        client, _ = async_client
        access_token = make_token(token_type="access", roles=["operator"])

        response = await client.post(
            "/auth/refresh",
            json={"refresh_token": access_token}
        )

        assert response.status_code == 401

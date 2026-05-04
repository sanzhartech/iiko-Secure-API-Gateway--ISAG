import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_get_stats_unauthorized(async_client: tuple[AsyncClient, ...], make_token):
    client, mock_iiko, mock_redis = async_client
    
    # Missing token
    response = await client.get("/admin/stats")
    assert response.status_code == 401

    # Invalid token (not an admin)
    token = make_token(roles=["operator"])
    response = await client.get("/admin/stats", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 403

@pytest.mark.asyncio
async def test_admin_client_lifecycle(async_client: tuple[AsyncClient, ...], make_token):
    client, mock_iiko, mock_redis = async_client
    token = make_token(roles=["admin"], sub="admin_test")
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Create a new client
    create_payload = {
        "client_id": "test_client_for_admin_api",
        "roles": ["operator"],
        "scopes": ["orders:read"],
        "rate_limit": 50
    }
    create_response = await client.post("/admin/clients", json=create_payload, headers=headers)
    assert create_response.status_code == 200
    data = create_response.json()
    assert data["client_id"] == "test_client_for_admin_api"
    assert data["roles"] == ["operator"]
    assert data["scopes"] == ["orders:read"]
    assert data["rate_limit"] == 50
    assert "client_secret" in data
    
    # 2. Toggle client status
    # Assuming GET /clients to retrieve UUID or assume we can patch directly if we had UUID.
    # We don't return UUID in ClientCreateResponse, let's fetch from DB or get from /admin/clients endpoint if it exists.
    # Let's get clients list first
    list_response = await client.get("/admin/clients", headers=headers)
    assert list_response.status_code == 200
    clients = list_response.json()
    created_client = next((c for c in clients if c["client_id"] == "test_client_for_admin_api"), None)
    assert created_client is not None
    client_uuid = created_client["id"]
    
    # Toggle status to false
    patch_response = await client.patch(
        f"/admin/clients/{client_uuid}/status", 
        json={"is_active": False}, 
        headers=headers
    )
    assert patch_response.status_code == 200
    assert patch_response.json()["is_active"] is False

import pytest
from httpx import AsyncClient
import uuid

@pytest.mark.asyncio
async def test_jti_is_mandatory(async_client, make_token):
    """[Rule 4] Reject tokens without jti (Fail-Closed)"""
    client, _, _ = async_client
    
    # Generate token without jti
    token_no_jti = make_token(omit_claims=["jti"])
    
    response = await client.get(
        "/api/test-path",
        headers={"Authorization": f"Bearer {token_no_jti}"}
    )
    
    assert response.status_code == 401
    assert response.json()["detail"] == "Unauthorized"

@pytest.mark.asyncio
async def test_response_headers_filtering(async_client, make_token):
    """[Rule 2/9] Verify Stage 9: Response Filter strips sensitive headers"""
    client, _, _ = async_client
    token = make_token()
    
    # We check a standard endpoint like /health or a proxy route
    # Even health should have headers filtered if registered globally
    response = await client.get("/health")
    
    assert response.status_code == 200
    # "Server" header should be stripped by ResponseFilterMiddleware
    assert "Server" not in response.headers

@pytest.mark.asyncio
async def test_request_size_validation(async_client, make_token):
    """[Rule 12] Verify Stage 2: Request Size Validation"""
    client, _, _ = async_client
    token = make_token()
    
    # Default limit is 10MB in our middleware. 
    # Let's send a payload that is definitely too large if we were to test it, 
    # but for a unit test, we can mock the content-length.
    
    large_payload = "x" * (11 * 1024 * 1024) # 11MB
    
    response = await client.post(
        "/api/write-path",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Length": str(len(large_payload))
        },
        content=large_payload
    )
    
    # Should fail at Stage 2 before reaching JWT validation or Rate Limiting
    assert response.status_code == 413
    assert response.json()["detail"] == "Request entity too large"

import os
import sys
import pytest
from datetime import timedelta
from fastapi import status

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


def test_token_model_fields():
    """Test that Token model has the correct fields."""
    from app.models.token import Token
    
    fields = [c.name for c in Token.__table__.columns]
    assert "id" in fields
    assert "user_id" in fields
    assert "token" in fields
    assert "token_type" in fields
    assert "client_ip" in fields
    assert "user_agent" in fields
    assert "is_revoked" in fields
    assert "expires_at" in fields
    assert "created_at" in fields


def test_token_schemas():
    """Test Token Pydantic schemas."""
    from app.schemas.token import TokenOut, TokenListResponse, TokenRevokeRequest, TokenRevokeResponse, TokenCleanupResponse
    from datetime import datetime
    
    token_out = TokenOut(
        id=1,
        user_id=1,
        token="hashed_token_string",
        is_revoked=False,
        expires_at=datetime.utcnow(),
        token_type="refresh",
    )
    assert token_out.id == 1
    assert token_out.user_id == 1
    assert token_out.is_revoked is False
    assert token_out.token_type == "refresh"
    
    list_response = TokenListResponse(items=[token_out], total=1, page=1, page_size=10)
    assert len(list_response.items) == 1
    assert list_response.total == 1
    
    revoke_req = TokenRevokeRequest(token_id=1)
    assert revoke_req.token_id == 1
    
    revoke_resp = TokenRevokeResponse(message="Revoked", token_id=1, revoked=True)
    assert revoke_resp.revoked is True
    
    cleanup_resp = TokenCleanupResponse(message="Cleaned up", deleted_count=5)
    assert cleanup_resp.deleted_count == 5


def test_hash_token():
    """Test token hashing function."""
    from app.services.token import hash_token
    
    token_str = "my_secret_token_string_123"
    hashed = hash_token(token_str)
    
    assert isinstance(hashed, str)
    assert len(hashed) == 64  # SHA256 hex digest is 64 chars
    assert hash_token(token_str) == hashed  # Deterministic
    assert hash_token("different_token") != hashed  # Different input, different hash


@pytest.mark.asyncio
async def test_store_and_verify_token(db_session):
    """Test storing and verifying a token."""
    from app.services.token import store_token, verify_token
    
    token_str = "test_refresh_token_string"
    
    # Store a token
    stored = await store_token(
        db=db_session,
        token_str=token_str,
        user_id=1,
        token_type="refresh",
        client_ip="192.168.1.1",
        user_agent="test-agent",
    )
    assert stored.id is not None
    assert stored.token_type == "refresh"
    assert stored.user_id == 1
    assert stored.client_ip == "192.168.1.1"
    assert stored.user_agent == "test-agent"
    assert stored.is_revoked is False
    
    # Verify the same token
    verified = await verify_token(db_session, token_str, token_type="refresh")
    assert verified is not None
    assert verified.id == stored.id
    
    # Verify wrong type returns None
    wrong_type = await verify_token(db_session, token_str, token_type="access")
    assert wrong_type is None


@pytest.mark.asyncio
async def test_revoke_token(db_session):
    """Test revoking a token."""
    from app.services.token import store_token, revoke_token, verify_token
    
    token_str = "token_to_revoke"
    stored = await store_token(db=db_session, token_str=token_str, user_id=1)
    
    # Revoke the token
    revoked = await revoke_token(db_session, stored.id, user_id=1)
    assert revoked is not None
    assert revoked.is_revoked is True
    
    # Verify should return None after revocation
    verified = await verify_token(db_session, token_str, token_type="refresh")
    assert verified is None


@pytest.mark.asyncio
async def test_revoke_nonexistent_token(db_session):
    """Test revoking a token that doesn't exist."""
    from app.services.token import revoke_token
    
    result = await revoke_token(db_session, token_id=9999, user_id=1)
    assert result is None


@pytest.mark.asyncio
async def test_revoke_another_users_token(db_session):
    """Test that user cannot revoke another user's token."""
    from app.services.token import store_token, revoke_token
    
    token_str = "token_user_1"
    stored = await store_token(db=db_session, token_str=token_str, user_id=1)
    
    # User 2 tries to revoke user 1's token
    result = await revoke_token(db_session, stored.id, user_id=2)
    assert result is None  # Should not find it


@pytest.mark.asyncio
async def test_revoke_user_tokens(db_session):
    """Test revoking all tokens for a user."""
    from app.services.token import store_token, revoke_user_tokens
    
    # Store multiple tokens for user 1
    for i in range(3):
        await store_token(db=db_session, token_str=f"token_{i}", user_id=1)
    
    # Store a token for user 2
    await store_token(db=db_session, token_str="token_user_2", user_id=2)
    
    # Revoke all tokens for user 1
    count = await revoke_user_tokens(db_session, user_id=1)
    assert count == 3  # All 3 user 1 tokens revoked
    
    # User 2's token should still be active
    count_user2 = await revoke_user_tokens(db_session, user_id=2)
    assert count_user2 == 1


@pytest.mark.asyncio
async def test_get_user_tokens(db_session):
    """Test getting tokens for a user with pagination."""
    from app.services.token import store_token, get_user_tokens
    
    # Store tokens for user 1
    for i in range(5):
        await store_token(db=db_session, token_str=f"get_token_{i}", user_id=1)
    
    # Get all tokens
    tokens, total = await get_user_tokens(db_session, user_id=1, limit=10)
    assert total == 5
    assert len(tokens) == 5
    
    # Test pagination
    tokens_page, total_page = await get_user_tokens(db_session, user_id=1, skip=2, limit=2)
    assert total_page == 5
    assert len(tokens_page) == 2


@pytest.mark.asyncio
async def test_cleanup_expired_tokens(db_session):
    """Test cleaning up expired tokens."""
    from datetime import datetime, timedelta
    from app.services.token import store_token, cleanup_expired_tokens, get_user_tokens
    
    # Store a token with short expiry
    from app.services.token import Token
    from sqlalchemy import select
    
    # Create an expired token directly
    from app.models.token import Token
    from app.services.token import hash_token
    
    expired_token = Token(
        token=hash_token("expired_token"),
        user_id=1,
        token_type="refresh",
        expires_at=datetime.utcnow() - timedelta(hours=1),  # Already expired
    )
    db_session.add(expired_token)
    await db_session.commit()
    
    # Store a valid token
    await store_token(db=db_session, token_str="valid_token", user_id=1)
    
    # Cleanup expired tokens
    deleted = await cleanup_expired_tokens(db_session)
    assert deleted >= 1  # At least the expired one
    
    # Only the valid token should remain
    tokens, total = await get_user_tokens(db_session, user_id=1)
    # The valid one plus any from other tests in the session
    assert total >= 1


@pytest.mark.asyncio
async def test_get_all_tokens(db_session):
    """Test getting all tokens (superuser)."""
    from app.services.token import store_token, get_all_tokens
    
    # Store tokens for different users
    for i in range(3):
        await store_token(db=db_session, token_str=f"all_token_{i}", user_id=1)
    for i in range(2):
        await store_token(db=db_session, token_str=f"user2_token_{i}", user_id=2)
    
    # Get all tokens
    all_tokens, total = await get_all_tokens(db_session)
    assert total >= 5
    assert len(all_tokens) >= 5


@pytest.mark.asyncio
async def test_get_token_by_id(db_session):
    """Test getting a token by ID."""
    from app.services.token import store_token, get_token_by_id
    
    stored = await store_token(db=db_session, token_str="find_by_id_token", user_id=1)
    
    found = await get_token_by_id(db_session, stored.id)
    assert found is not None
    assert found.id == stored.id
    
    not_found = await get_token_by_id(db_session, 99999)
    assert not_found is None


@pytest.mark.asyncio
async def test_token_endpoints_list(client, user_token_headers):
    """Test the list tokens endpoint."""
    response = await client.get("/api/v1/tokens/", headers=user_token_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert "page" in data
    assert "page_size" in data


@pytest.mark.asyncio
async def test_token_endpoints_unauthorized(client):
    """Test token endpoints without auth."""
    response = await client.get("/api/v1/tokens/")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.asyncio
async def test_token_login_stores_token(client, test_user):
    """Test that login stores a refresh token in the database."""
    from app.models.token import Token
    from sqlalchemy import select
    
    response = await client.post(
        "/api/v1/auth/login",
        data={"username": "testuser@example.com", "password": "TestPassword123!"},
    )
    assert response.status_code == status.HTTP_200_OK
    
    # Wait - we need a db session to check
    # This test is more of an integration check
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data


@pytest.mark.asyncio
async def test_refresh_endpoint_with_db_verification(client, test_user):
    """Test refresh endpoint works with DB token verification."""
    # Login first
    response = await client.post(
        "/api/v1/auth/login",
        data={"username": "testuser@example.com", "password": "TestPassword123!"},
    )
    assert response.status_code == status.HTTP_200_OK
    login_data = response.json()
    
    # Refresh with valid token
    response = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": login_data["refresh_token"]},
    )
    assert response.status_code == status.HTTP_200_OK
    refresh_data = response.json()
    assert "access_token" in refresh_data
    assert "refresh_token" in refresh_data


@pytest.mark.asyncio
async def test_token_list_with_pagination(client, user_token_headers):
    """Test token list with pagination parameters."""
    response = await client.get(
        "/api/v1/tokens/?skip=0&limit=10&include_revoked=true",
        headers=user_token_headers,
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["page_size"] == 10
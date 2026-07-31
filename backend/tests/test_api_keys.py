import os
import sys
import pytest
from datetime import datetime, timedelta
from fastapi import status

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


def test_api_key_model_fields():
    """Test that ApiKey model has the correct fields."""
    from app.models.api_key import ApiKey
    
    fields = [c.name for c in ApiKey.__table__.columns]
    assert "id" in fields
    assert "user_id" in fields
    assert "key_name" in fields
    assert "api_key" in fields
    assert "permissions" in fields
    assert "is_active" in fields
    assert "expires_at" in fields
    assert "last_used_at" in fields
    assert "created_at" in fields
    assert "updated_at" in fields


def test_api_key_schemas():
    """Test ApiKey Pydantic schemas."""
    from app.schemas.api_key import ApiKeyCreate, ApiKeyUpdate, ApiKeyOut, ApiKeyListResponse, ApiKeyCreateResponse
    from datetime import datetime
    
    # Test ApiKeyCreate
    create_data = ApiKeyCreate(
        key_name="Test API Key",
        permissions="read,write",
        expires_at=datetime.utcnow() + timedelta(days=30),
    )
    assert create_data.key_name == "Test API Key"
    assert create_data.permissions == "read,write"
    assert create_data.is_active is True
    
    # Test ApiKeyUpdate
    update_data = ApiKeyUpdate(
        key_name="Updated API Key",
        permissions="read",
        is_active=False,
    )
    assert update_data.key_name == "Updated API Key"
    assert update_data.permissions == "read"
    assert update_data.is_active is False
    
    # Test ApiKeyOut
    api_key_out = ApiKeyOut(
        id=1,
        user_id=1,
        key_name="Test Key",
        api_key="hashed_key_string",
        is_active=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    assert api_key_out.id == 1
    assert api_key_out.user_id == 1
    assert api_key_out.key_name == "Test Key"
    assert api_key_out.is_active is True
    
    # Test ApiKeyListResponse
    list_response = ApiKeyListResponse(items=[api_key_out], total=1, page=1, page_size=10)
    assert len(list_response.items) == 1
    assert list_response.total == 1
    
    # Test ApiKeyCreateResponse
    create_response = ApiKeyCreateResponse(
        id=1,
        key_name="Test Key",
        api_key="plain_text_key",
        message="API key created successfully",
    )
    assert create_response.id == 1
    assert create_response.api_key == "plain_text_key"


def test_hash_api_key():
    """Test API key hashing function."""
    from app.services.api_key import hash_api_key
    
    api_key = "my_secret_api_key_123"
    hashed = hash_api_key(api_key)
    
    assert isinstance(hashed, str)
    assert len(hashed) == 64  # SHA256 hex digest is 64 chars
    assert hash_api_key(api_key) == hashed  # Deterministic
    assert hash_api_key("different_key") != hashed  # Different input, different hash


def test_generate_api_key():
    """Test API key generation function."""
    from app.services.api_key import generate_api_key
    
    key1 = generate_api_key()
    key2 = generate_api_key()
    
    assert isinstance(key1, str)
    assert len(key1) > 20  # Should be reasonably long
    assert key1 != key2  # Should be unique


@pytest.mark.asyncio
async def test_create_and_verify_api_key(db_session):
    """Test creating and verifying an API key."""
    from app.services.api_key import create_api_key, verify_api_key
    
    # Create an API key
    api_key_obj, plain_key = await create_api_key(
        db=db_session,
        user_id=1,
        key_name="Test API Key",
        permissions="read,write",
    )
    
    assert api_key_obj.id is not None
    assert api_key_obj.user_id == 1
    assert api_key_obj.key_name == "Test API Key"
    assert api_key_obj.permissions == "read,write"
    assert api_key_obj.is_active is True
    assert plain_key != api_key_obj.api_key  # Plain key should not match hashed
    
    # Verify the API key
    verified = await verify_api_key(db_session, plain_key)
    assert verified is not None
    assert verified.id == api_key_obj.id
    assert verified.key_name == "Test API Key"


@pytest.mark.asyncio
async def test_verify_invalid_api_key(db_session):
    """Test verifying an invalid API key."""
    from app.services.api_key import verify_api_key
    
    # Verify non-existent key
    verified = await verify_api_key(db_session, "nonexistent_key")
    assert verified is None


@pytest.mark.asyncio
async def test_verify_revoked_api_key(db_session):
    """Test verifying a revoked API key."""
    from app.services.api_key import create_api_key, verify_api_key, revoke_api_key
    
    # Create and revoke an API key
    api_key_obj, plain_key = await create_api_key(
        db=db_session,
        user_id=1,
        key_name="Revoked Key",
    )
    
    await revoke_api_key(db_session, api_key_obj.id, user_id=1)
    
    # Verify should return None for revoked key
    verified = await verify_api_key(db_session, plain_key)
    assert verified is None


@pytest.mark.asyncio
async def test_verify_expired_api_key(db_session):
    """Test verifying an expired API key."""
    from app.services.api_key import create_api_key, verify_api_key
    from datetime import datetime, timedelta
    
    # Create an expired API key
    api_key_obj, plain_key = await create_api_key(
        db=db_session,
        user_id=1,
        key_name="Expired Key",
        expires_at=datetime.utcnow() - timedelta(days=1),  # Already expired
    )
    
    # Verify should return None for expired key
    verified = await verify_api_key(db_session, plain_key)
    assert verified is None


@pytest.mark.asyncio
async def test_get_user_api_keys(db_session):
    """Test getting API keys for a user."""
    from app.services.api_key import create_api_key, get_user_api_keys
    
    # Create multiple API keys for user 1
    for i in range(3):
        await create_api_key(
            db=db_session,
            user_id=1,
            key_name=f"User 1 Key {i}",
        )
    
    # Create a key for user 2
    await create_api_key(
        db=db_session,
        user_id=2,
        key_name="User 2 Key",
    )
    
    # Get user 1's keys
    keys, total = await get_user_api_keys(db_session, user_id=1)
    assert total >= 3
    assert len(keys) >= 3
    
    # Test pagination
    keys_page, total_page = await get_user_api_keys(db_session, user_id=1, skip=1, limit=2)
    assert total_page >= 3
    assert len(keys_page) == 2


@pytest.mark.asyncio
async def test_get_all_api_keys(db_session):
    """Test getting all API keys (superuser)."""
    from app.services.api_key import create_api_key, get_all_api_keys
    
    # Create keys for different users
    for i in range(3):
        await create_api_key(db=db_session, user_id=1, key_name=f"Key {i}")
    for i in range(2):
        await create_api_key(db=db_session, user_id=2, key_name=f"User2 Key {i}")
    
    # Get all keys
    all_keys, total = await get_all_api_keys(db_session)
    assert total >= 5
    assert len(all_keys) >= 5


@pytest.mark.asyncio
async def test_update_api_key(db_session):
    """Test updating an API key."""
    from app.services.api_key import create_api_key, update_api_key, get_api_key_by_id
    from app.schemas.api_key import ApiKeyUpdate
    
    # Create an API key
    api_key_obj, _ = await create_api_key(
        db=db_session,
        user_id=1,
        key_name="Original Name",
    )
    
    # Update the key
    updated = await update_api_key(
        db=db_session,
        api_key_id=api_key_obj.id,
        user_id=1,
        data=ApiKeyUpdate(key_name="Updated Name", permissions="read"),
    )
    
    assert updated is not None
    assert updated.key_name == "Updated Name"
    assert updated.permissions == "read"
    
    # Verify in database
    fetched = await get_api_key_by_id(db_session, api_key_obj.id)
    assert fetched.key_name == "Updated Name"


@pytest.mark.asyncio
async def test_update_another_users_api_key(db_session):
    """Test that user cannot update another user's API key."""
    from app.services.api_key import create_api_key, update_api_key
    
    # User 1 creates a key
    api_key_obj, _ = await create_api_key(
        db=db_session,
        user_id=1,
        key_name="User 1 Key",
    )
    
    # User 2 tries to update it
    updated = await update_api_key(
        db=db_session,
        api_key_id=api_key_obj.id,
        user_id=2,
        data={"key_name": "Hacked Name"},
    )
    
    assert updated is None  # Should not update


@pytest.mark.asyncio
async def test_delete_api_key(db_session):
    """Test deleting an API key."""
    from app.services.api_key import create_api_key, delete_api_key, get_api_key_by_id
    
    # Create an API key
    api_key_obj, _ = await create_api_key(
        db=db_session,
        user_id=1,
        key_name="To Delete",
    )
    
    # Delete the key
    deleted = await delete_api_key(db_session, api_key_obj.id, user_id=1)
    assert deleted is True
    
    # Verify it's gone
    fetched = await get_api_key_by_id(db_session, api_key_obj.id)
    assert fetched is None


@pytest.mark.asyncio
async def test_delete_another_users_api_key(db_session):
    """Test that user cannot delete another user's API key."""
    from app.services.api_key import create_api_key, delete_api_key
    
    # User 1 creates a key
    api_key_obj, _ = await create_api_key(
        db=db_session,
        user_id=1,
        key_name="User 1 Key",
    )
    
    # User 2 tries to delete it
    deleted = await delete_api_key(db_session, api_key_obj.id, user_id=2)
    assert deleted is False


@pytest.mark.asyncio
async def test_revoke_api_key(db_session):
    """Test revoking an API key."""
    from app.services.api_key import create_api_key, revoke_api_key, get_api_key_by_id
    
    # Create an API key
    api_key_obj, _ = await create_api_key(
        db=db_session,
        user_id=1,
        key_name="To Revoke",
    )
    
    # Revoke the key
    revoked = await revoke_api_key(db_session, api_key_obj.id, user_id=1)
    assert revoked is not None
    assert revoked.is_active is False
    
    # Verify in database
    fetched = await get_api_key_by_id(db_session, api_key_obj.id)
    assert fetched.is_active is False


@pytest.mark.asyncio
async def test_api_key_endpoints_create(client, user_token_headers):
    """Test creating an API key via endpoint."""
    response = await client.post(
        "/api/v1/api-keys/",
        json={
            "key_name": "Test API Key",
            "permissions": "read,write",
        },
        headers=user_token_headers,
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "id" in data
    assert "api_key" in data
    assert data["key_name"] == "Test API Key"
    assert len(data["api_key"]) > 20  # Should be a valid key


@pytest.mark.asyncio
async def test_api_key_endpoints_list(client, user_token_headers):
    """Test listing API keys via endpoint."""
    response = await client.get("/api/v1/api-keys/", headers=user_token_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert "page" in data
    assert "page_size" in data


@pytest.mark.asyncio
async def test_api_key_endpoints_unauthorized(client):
    """Test API key endpoints without auth."""
    response = await client.get("/api/v1/api-keys/")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.asyncio
async def test_api_key_endpoints_update(client, user_token_headers):
    """Test updating an API key via endpoint."""
    # First create a key
    create_response = await client.post(
        "/api/v1/api-keys/",
        json={"key_name": "To Update"},
        headers=user_token_headers,
    )
    assert create_response.status_code == status.HTTP_200_OK
    key_id = create_response.json()["id"]
    
    # Update the key
    response = await client.put(
        f"/api/v1/api-keys/{key_id}",
        json={"key_name": "Updated Name", "permissions": "read"},
        headers=user_token_headers,
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["key_name"] == "Updated Name"
    assert data["permissions"] == "read"


@pytest.mark.asyncio
async def test_api_key_endpoints_delete(client, user_token_headers):
    """Test deleting an API key via endpoint."""
    # First create a key
    create_response = await client.post(
        "/api/v1/api-keys/",
        json={"key_name": "To Delete"},
        headers=user_token_headers,
    )
    assert create_response.status_code == status.HTTP_200_OK
    key_id = create_response.json()["id"]
    
    # Delete the key
    response = await client.delete(
        f"/api/v1/api-keys/{key_id}",
        headers=user_token_headers,
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "message" in data


@pytest.mark.asyncio
async def test_api_key_endpoints_revoke(client, user_token_headers):
    """Test revoking an API key via endpoint."""
    # First create a key
    create_response = await client.post(
        "/api/v1/api-keys/",
        json={"key_name": "To Revoke"},
        headers=user_token_headers,
    )
    assert create_response.status_code == status.HTTP_200_OK
    key_id = create_response.json()["id"]
    
    # Revoke the key
    response = await client.post(
        f"/api/v1/api-keys/revoke/{key_id}",
        headers=user_token_headers,
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "message" in data


@pytest.mark.asyncio
async def test_api_key_list_with_pagination(client, user_token_headers):
    """Test API key list with pagination parameters."""
    response = await client.get(
        "/api/v1/api-keys/?skip=0&limit=10&include_inactive=true",
        headers=user_token_headers,
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["page_size"] == 10
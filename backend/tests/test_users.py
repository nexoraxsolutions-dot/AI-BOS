import os
import sys
import pytest
from fastapi import status

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


def test_user_service_create():
    """Test user service create function exists."""
    from app.services.user import create_user, get_user, get_user_by_email, get_users, update_user, delete_user, get_user_by_username, change_password, update_profile, search_users
    assert callable(create_user)
    assert callable(get_user)
    assert callable(get_user_by_email)
    assert callable(get_users)
    assert callable(update_user)
    assert callable(delete_user)
    assert callable(get_user_by_username)
    assert callable(change_password)
    assert callable(update_profile)
    assert callable(search_users)


def test_user_model():
    """Test user model fields."""
    from app.models.user import User
    from app.core.security import get_password_hash
    
    user = User(
        email="test@example.com",
        username="testuser",
        hashed_password=get_password_hash("TestPassword123!"),
        full_name="Test User",
        is_active=True,
        is_superuser=False,
    )
    assert user.email == "test@example.com"
    assert user.username == "testuser"
    assert user.full_name == "Test User"
    assert user.is_active == True
    assert user.is_superuser == False


@pytest.mark.asyncio
async def test_user_update_schema():
    """Test user update schema validation."""
    from app.schemas.user import UserUpdate
    
    # Valid partial update
    update = UserUpdate(full_name="New Name")
    assert update.full_name == "New Name"
    assert update.email is None
    assert update.password is None
    
    # Valid full update
    update = UserUpdate(email="new@example.com", full_name="New Name", is_active=False)
    assert update.email == "new@example.com"
    assert update.is_active == False
    
    # Invalid short password
    with pytest.raises(Exception):
        UserUpdate(password="short")


@pytest.mark.asyncio
async def test_password_change_schema():
    """Test password change schema validation."""
    from app.schemas.user import PasswordChange
    
    # Valid
    pc = PasswordChange(current_password="oldpass", new_password="newpass123")
    assert pc.current_password == "oldpass"
    assert pc.new_password == "newpass123"
    
    # Invalid short new password
    with pytest.raises(Exception):
        PasswordChange(current_password="oldpass", new_password="short")


@pytest.mark.asyncio
async def test_user_profile_update_schema():
    """Test user profile update schema validation."""
    from app.schemas.user import UserProfileUpdate
    
    # Valid
    pu = UserProfileUpdate(full_name="New Name", username="newuser")
    assert pu.full_name == "New Name"
    assert pu.username == "newuser"
    
    # Invalid short username
    with pytest.raises(Exception):
        UserProfileUpdate(username="ab")


@pytest.mark.asyncio
async def test_list_users_endpoint(client, admin_token_headers, test_user):
    """Test listing users as admin."""
    response = await client.get("/api/v1/users/", headers=admin_token_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) >= 1
    assert any(u["email"] == "testuser@example.com" for u in data)


@pytest.mark.asyncio
async def test_get_user_endpoint(client, admin_token_headers, test_user):
    """Test getting a specific user by ID as admin."""
    response = await client.get(f"/api/v1/users/{test_user.id}", headers=admin_token_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["email"] == "testuser@example.com"
    assert data["full_name"] == "Test User"


@pytest.mark.asyncio
async def test_get_user_nonexistent(client, admin_token_headers):
    """Test getting a non-existent user returns 404."""
    response = await client.get("/api/v1/users/99999", headers=admin_token_headers)
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_create_user_endpoint(client, admin_token_headers):
    """Test creating a new user as admin."""
    response = await client.post(
        "/api/v1/users/",
        json={"email": "newuser@example.com", "password": "NewPass123!", "full_name": "New User", "username": "newuser"},
        headers=admin_token_headers,
    )
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["email"] == "newuser@example.com"
    assert data["full_name"] == "New User"
    assert data["is_active"] == True
    assert data["is_superuser"] == False


@pytest.mark.asyncio
async def test_create_user_duplicate_email(client, admin_token_headers, test_user):
    """Test creating a user with duplicate email returns 400."""
    response = await client.post(
        "/api/v1/users/",
        json={"email": "testuser@example.com", "password": "NewPass123!"},
        headers=admin_token_headers,
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.asyncio
async def test_create_user_unauthorized(client, user_token_headers):
    """Test that non-admin users cannot create users."""
    response = await client.post(
        "/api/v1/users/",
        json={"email": "newuser@example.com", "password": "NewPass123!"},
        headers=user_token_headers,
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.asyncio
async def test_update_user_endpoint(client, admin_token_headers, test_user):
    """Test updating a user as admin."""
    response = await client.put(
        f"/api/v1/users/{test_user.id}",
        json={"full_name": "Updated Name", "is_active": False},
        headers=admin_token_headers,
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["full_name"] == "Updated Name"
    assert data["is_active"] == False


@pytest.mark.asyncio
async def test_delete_user_endpoint(client, admin_token_headers, test_user):
    """Test deleting a user as admin."""
    response = await client.delete(f"/api/v1/users/{test_user.id}", headers=admin_token_headers)
    assert response.status_code == status.HTTP_204_NO_CONTENT


@pytest.mark.asyncio
async def test_delete_user_nonexistent(client, admin_token_headers):
    """Test deleting a non-existent user returns 404."""
    response = await client.delete("/api/v1/users/99999", headers=admin_token_headers)
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_get_my_profile(client, user_token_headers, test_user):
    """Test getting current user profile."""
    response = await client.get("/api/v1/users/me", headers=user_token_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["email"] == test_user.email
    assert data["id"] == test_user.id


@pytest.mark.asyncio
async def test_update_my_profile(client, user_token_headers, test_user):
    """Test updating current user profile."""
    response = await client.put(
        "/api/v1/users/me/profile",
        json={"full_name": "Updated Profile Name"},
        headers=user_token_headers,
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["full_name"] == "Updated Profile Name"


@pytest.mark.asyncio
async def test_change_password(client, user_token_headers, test_user):
    """Test changing password."""
    response = await client.post(
        "/api/v1/users/me/change-password",
        json={"current_password": "TestPassword123!", "new_password": "NewSecurePass123!"},
        headers=user_token_headers,
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["message"] == "Password changed successfully"


@pytest.mark.asyncio
async def test_change_password_wrong_current(client, user_token_headers, test_user):
    """Test changing password with wrong current password returns 400."""
    response = await client.post(
        "/api/v1/users/me/change-password",
        json={"current_password": "WrongPassword123!", "new_password": "NewSecurePass123!"},
        headers=user_token_headers,
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.asyncio
async def test_search_users(client, admin_token_headers, test_user):
    """Test searching users."""
    response = await client.get(
        "/api/v1/users/?search=testuser",
        headers=admin_token_headers,
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) >= 1
    assert any(u["email"] == "testuser@example.com" for u in data)
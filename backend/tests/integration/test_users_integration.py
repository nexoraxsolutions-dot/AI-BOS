"""Integration tests for users API endpoints."""
import pytest
from fastapi import status
from httpx import AsyncClient

from app.schemas.user import UserCreate, UserUpdate, UserProfileUpdate, PasswordChange
from app.core.security import get_password_hash

pytestmark = pytest.mark.asyncio


class TestUsersEndpoints:
    """Integration tests for users endpoints."""

    async def test_create_user_success(self, client: AsyncClient, admin_token_headers, test_company, db_session):
        """Test successful user creation via API."""
        # Arrange
        user_data = {
            "email": "newuser@example.com",
            "password": "ValidPass123!",
            "full_name": "New User",
            "username": "newuser",
            "company_id": test_company.id
        }
        
        # Act
        response = await client.post(
            "/api/v1/users/",
            json=user_data,
            headers=admin_token_headers
        )
        
        # Assert
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["email"] == "newuser@example.com"
        assert data["full_name"] == "New User"
        assert data["username"] == "newuser"
        assert "id" in data
        assert "hashed_password" not in data  # Password should not be returned
        
        # Verify user was persisted in database
        from app.services.user import get_user_by_email
        user = await get_user_by_email(db_session, "newuser@example.com")
        assert user is not None
        assert user.email == "newuser@example.com"
        assert user.company_id == test_company.id

    async def test_create_user_duplicate_email(self, client: AsyncClient, admin_token_headers, test_user):
        """Test user creation with duplicate email."""
        # Arrange
        user_data = {
            "email": "testuser@example.com",  # Already exists
            "password": "ValidPass123!",
            "full_name": "Duplicate User",
            "username": "duplicateuser"
        }
        
        # Act
        response = await client.post(
            "/api/v1/users/",
            json=user_data,
            headers=admin_token_headers
        )
        
        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert "detail" in data
        assert "email" in data["detail"].lower()

    async def test_create_user_duplicate_username(self, client: AsyncClient, admin_token_headers, test_company):
        """Test user creation with duplicate username."""
        # Arrange - Create first user
        user_data1 = {
            "email": "user1@example.com",
            "password": "ValidPass123!",
            "full_name": "User One",
            "username": "testuser",
            "company_id": test_company.id
        }
        response1 = await client.post(
            "/api/v1/users/",
            json=user_data1,
            headers=admin_token_headers
        )
        assert response1.status_code == status.HTTP_201_CREATED
        
        # Try to create second user with same username
        user_data2 = {
            "email": "user2@example.com",
            "password": "ValidPass123!",
            "full_name": "User Two",
            "username": "testuser",  # Same username
            "company_id": test_company.id
        }
        
        # Act
        response2 = await client.post(
            "/api/v1/users/",
            json=user_data2,
            headers=admin_token_headers
        )
        
        # Assert
        assert response2.status_code == status.HTTP_400_BAD_REQUEST
        data = response2.json()
        assert "username" in data["detail"].lower()

    async def test_create_user_unauthorized(self, client: AsyncClient):
        """Test user creation without authentication."""
        # Arrange
        user_data = {
            "email": "test@example.com",
            "password": "ValidPass123!",
            "full_name": "Test User"
        }
        
        # Act
        response = await client.post("/api/v1/users/", json=user_data)
        
        # Assert
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_create_user_validation_errors(self, client: AsyncClient, admin_token_headers):
        """Test user creation with validation errors."""
        # Test missing required fields
        response = await client.post(
            "/api/v1/users/",
            json={},
            headers=admin_token_headers
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        
        # Test invalid email format
        response = await client.post(
            "/api/v1/users/",
            json={
                "email": "invalid-email",
                "password": "ValidPass123!",
                "full_name": "Test User"
            },
            headers=admin_token_headers
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        
        # Test weak password
        response = await client.post(
            "/api/v1/users/",
            json={
                "email": "test@example.com",
                "password": "short",
                "full_name": "Test User"
            },
            headers=admin_token_headers
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    async def test_list_users_success(self, client: AsyncClient, user_token_headers, test_user):
        """Test getting list of users."""
        # Act
        response = await client.get("/api/v1/users/", headers=user_token_headers)
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        # Check that test_user is in the list
        user_emails = [u["email"] for u in data]
        assert test_user.email in user_emails

    async def test_list_users_with_pagination(self, client: AsyncClient, user_token_headers):
        """Test getting users with pagination."""
        # Act
        response = await client.get(
            "/api/v1/users/?skip=0&limit=10",
            headers=user_token_headers
        )
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) <= 10

    async def test_list_users_with_search(self, client: AsyncClient, user_token_headers, test_user):
        """Test searching users."""
        # Act
        response = await client.get(
            f"/api/v1/users/?search={test_user.full_name}",
            headers=user_token_headers
        )
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        # Check that test_user is in search results
        user_names = [u["full_name"] for u in data]
        assert test_user.full_name in user_names

    async def test_get_current_user_profile(self, client: AsyncClient, user_token_headers, test_user):
        """Test getting current user profile."""
        # Act
        response = await client.get("/api/v1/users/me", headers=user_token_headers)
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["email"] == test_user.email
        assert data["full_name"] == test_user.full_name
        assert "hashed_password" not in data

    async def test_update_my_profile_success(self, client: AsyncClient, user_token_headers, test_user, db_session):
        """Test successful profile update."""
        # Arrange
        update_data = {
            "full_name": "Updated Name",
            "username": "updatedusername"
        }
        
        # Act
        response = await client.put(
            "/api/v1/users/me/profile",
            json=update_data,
            headers=user_token_headers
        )
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["full_name"] == "Updated Name"
        assert data["username"] == "updatedusername"
        
        # Verify in database
        await db_session.refresh(test_user)
        assert test_user.full_name == "Updated Name"
        assert test_user.username == "updatedusername"

    async def test_update_my_profile_duplicate_username(self, client: AsyncClient, user_token_headers, test_company, db_session):
        """Test profile update with duplicate username."""
        # Arrange - Create another user
        from app.services.user import create_user
        from app.schemas.user import UserCreate
        other_user = await create_user(
            db_session,
            UserCreate(
                email="other@example.com",
                password="ValidPass123!",
                full_name="Other User",
                username="otheruser",
                company_id=test_company.id
            )
        )
        
        # Try to update current user's username to match other user
        update_data = {"username": "otheruser"}
        
        # Act
        response = await client.put(
            "/api/v1/users/me/profile",
            json=update_data,
            headers=user_token_headers
        )
        
        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert "username" in data["detail"].lower()

    async def test_change_password_success(self, client: AsyncClient, user_token_headers, test_user):
        """Test successful password change."""
        # Arrange
        password_data = {
            "current_password": "TestPassword123!",
            "new_password": "NewPassword456!"
        }
        
        # Act
        response = await client.post(
            "/api/v1/users/me/change-password",
            json=password_data,
            headers=user_token_headers
        )
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "message" in data
        assert "success" in data["message"].lower()

    async def test_change_password_wrong_current(self, client: AsyncClient, user_token_headers):
        """Test password change with wrong current password."""
        # Arrange
        password_data = {
            "current_password": "WrongPassword!",
            "new_password": "NewPassword456!"
        }
        
        # Act
        response = await client.post(
            "/api/v1/users/me/change-password",
            json=password_data,
            headers=user_token_headers
        )
        
        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert "incorrect" in data["detail"].lower() or "current" in data["detail"].lower()

    async def test_get_user_by_id_success(self, client: AsyncClient, user_token_headers, test_user):
        """Test getting a specific user by ID."""
        # Act
        response = await client.get(
            f"/api/v1/users/{test_user.id}",
            headers=user_token_headers
        )
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == test_user.id
        assert data["email"] == test_user.email
        assert "hashed_password" not in data

    async def test_get_user_by_id_not_found(self, client: AsyncClient, user_token_headers):
        """Test getting non-existent user."""
        # Act
        response = await client.get(
            "/api/v1/users/99999",
            headers=user_token_headers
        )
        
        # Assert
        assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_update_user_success(self, client: AsyncClient, admin_token_headers, test_user, db_session):
        """Test successful user update by admin."""
        # Arrange
        update_data = {
            "full_name": "Admin Updated Name",
            "is_active": False
        }
        
        # Act
        response = await client.put(
            f"/api/v1/users/{test_user.id}",
            json=update_data,
            headers=admin_token_headers
        )
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["full_name"] == "Admin Updated Name"
        assert data["is_active"] is False
        
        # Verify in database
        await db_session.refresh(test_user)
        assert test_user.full_name == "Admin Updated Name"
        assert test_user.is_active is False

    async def test_update_user_not_found(self, client: AsyncClient, admin_token_headers):
        """Test updating non-existent user."""
        # Arrange
        update_data = {"full_name": "Updated Name"}
        
        # Act
        response = await client.put(
            "/api/v1/users/99999",
            json=update_data,
            headers=admin_token_headers
        )
        
        # Assert
        assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_update_user_unauthorized(self, client: AsyncClient, test_user, user_token_headers):
        """Test that regular users cannot update other users."""
        # Arrange
        update_data = {"full_name": "Hacked Name"}
        
        # Act - Try to update test_user with regular user token
        response = await client.put(
            f"/api/v1/users/{test_user.id}",
            json=update_data,
            headers=user_token_headers
        )
        
        # Assert - Should be forbidden (requires superuser)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    async def test_delete_user_success(self, client: AsyncClient, admin_token_headers, db_session):
        """Test successful user deletion by admin."""
        # Arrange - Create a user to delete
        from app.services.user import create_user
        from app.schemas.user import UserCreate
        user_to_delete = await create_user(
            db_session,
            UserCreate(
                email="todelete@example.com",
                password="ValidPass123!",
                full_name="To Delete",
                username="todelete",
                company_id=test_company.id
            )
        )
        user_id = user_to_delete.id
        
        # Act
        response = await client.delete(
            f"/api/v1/users/{user_id}",
            headers=admin_token_headers
        )
        
        # Assert
        assert response.status_code == status.HTTP_204_NO_CONTENT
        
        # Verify user was deleted from database
        from app.services.user import get_user
        deleted_user = await get_user(db_session, user_id)
        assert deleted_user is None

    async def test_delete_user_not_found(self, client: AsyncClient, admin_token_headers):
        """Test deleting non-existent user."""
        # Act
        response = await client.delete(
            "/api/v1/users/99999",
            headers=admin_token_headers
        )
        
        # Assert
        assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_delete_user_unauthorized(self, client: AsyncClient, test_user, user_token_headers):
        """Test that regular users cannot delete other users."""
        # Act - Try to delete test_user with regular user token
        response = await client.delete(
            f"/api/v1/users/{test_user.id}",
            headers=user_token_headers
        )
        
        # Assert - Should be forbidden (requires superuser)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    async def test_user_crud_workflow(self, client: AsyncClient, admin_token_headers, test_company, db_session):
        """Test complete CRUD workflow for users."""
        # Create
        create_data = {
            "email": "workflow@example.com",
            "password": "ValidPass123!",
            "full_name": "Workflow User",
            "username": "workflowuser",
            "company_id": test_company.id
        }
        create_response = await client.post(
            "/api/v1/users/",
            json=create_data,
            headers=admin_token_headers
        )
        assert create_response.status_code == status.HTTP_201_CREATED
        user_id = create_response.json()["id"]
        
        # Read
        read_response = await client.get(
            f"/api/v1/users/{user_id}",
            headers=admin_token_headers
        )
        assert read_response.status_code == status.HTTP_200_OK
        assert read_response.json()["email"] == "workflow@example.com"
        
        # Update
        update_data = {"full_name": "Updated Workflow User"}
        update_response = await client.put(
            f"/api/v1/users/{user_id}",
            json=update_data,
            headers=admin_token_headers
        )
        assert update_response.status_code == status.HTTP_200_OK
        assert update_response.json()["full_name"] == "Updated Workflow User"
        
        # Delete
        delete_response = await client.delete(
            f"/api/v1/users/{user_id}",
            headers=admin_token_headers
        )
        assert delete_response.status_code == status.HTTP_204_NO_CONTENT
        
        # Verify deletion
        verify_response = await client.get(
            f"/api/v1/users/{user_id}",
            headers=admin_token_headers
        )
        assert verify_response.status_code == status.HTTP_404_NOT_FOUND
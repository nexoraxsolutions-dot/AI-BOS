"""Integration tests for authentication API endpoints."""
import pytest
from fastapi import status
from httpx import AsyncClient

from app.schemas.auth import RegisterRequest
from app.core.security import get_password_hash

pytestmark = pytest.mark.asyncio


class TestAuthenticationEndpoints:
    """Integration tests for authentication endpoints."""

    async def test_register_user_success(self, client: AsyncClient, db_session):
        """Test successful user registration via API."""
        # Arrange
        user_data = {
            "email": "newuser@example.com",
            "password": "ValidPass123!",
            "full_name": "New User",
            "username": "newuser"
        }
        
        # Act
        response = await client.post("/api/v1/auth/register", json=user_data)
        
        # Assert
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert "user" in data
        assert data["user"]["email"] == "newuser@example.com"
        assert data["user"]["full_name"] == "New User"
        assert "access_token" in data
        assert "refresh_token" in data
        
        # Verify user was persisted in database
        from app.services.user import get_user_by_email
        user = await get_user_by_email(db_session, "newuser@example.com")
        assert user is not None
        assert user.email == "newuser@example.com"

    async def test_register_user_duplicate_email(self, client: AsyncClient, test_user):
        """Test registration with duplicate email."""
        # Arrange
        user_data = {
            "email": "testuser@example.com",  # Already exists
            "password": "ValidPass123!",
            "full_name": "Duplicate User",
            "username": "duplicateuser"
        }
        
        # Act
        response = await client.post("/api/v1/auth/register", json=user_data)
        
        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert "detail" in data

    async def test_register_user_invalid_password(self, client: AsyncClient):
        """Test registration with invalid password."""
        # Arrange
        user_data = {
            "email": "test@example.com",
            "password": "short",  # Too short
            "full_name": "Test User"
        }
        
        # Act
        response = await client.post("/api/v1/auth/register", json=user_data)
        
        # Assert
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    async def test_login_success(self, client: AsyncClient, test_user):
        """Test successful login."""
        # Arrange
        login_data = {
            "username": "testuser@example.com",
            "password": "TestPassword123!"
        }
        
        # Act
        response = await client.post("/api/v1/auth/login", data=login_data)
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert "user" in data
        assert data["user"]["email"] == "testuser@example.com"

    async def test_login_invalid_credentials(self, client: AsyncClient):
        """Test login with invalid credentials."""
        # Arrange
        login_data = {
            "username": "wrong@example.com",
            "password": "wrongpassword"
        }
        
        # Act
        response = await client.post("/api/v1/auth/login", data=login_data)
        
        # Assert
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_login_json_success(self, client: AsyncClient, test_user):
        """Test successful JSON login."""
        # Arrange
        login_data = {
            "email": "testuser@example.com",
            "password": "TestPassword123!"
        }
        
        # Act
        response = await client.post("/api/v1/auth/login-json", json=login_data)
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data

    async def test_logout_success(self, client: AsyncClient, user_token_headers):
        """Test successful logout."""
        # Act
        response = await client.post("/api/v1/auth/logout", headers=user_token_headers)
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "message" in data

    async def test_validate_token_success(self, client: AsyncClient, user_token_headers):
        """Test token validation."""
        # Act
        response = await client.get("/api/v1/auth/validate", headers=user_token_headers)
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["valid"] is True
        assert "email" in data
        assert "user_id" in data

    async def test_validate_token_invalid(self, client: AsyncClient):
        """Test token validation with invalid token."""
        # Act
        response = await client.get(
            "/api/v1/auth/validate",
            headers={"Authorization": "Bearer invalid_token"}
        )
        
        # Assert
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_refresh_token_success(self, client: AsyncClient, test_user):
        """Test successful token refresh."""
        # Arrange - Login to get tokens
        login_response = await client.post(
            "/api/v1/auth/login",
            data={"username": "testuser@example.com", "password": "TestPassword123!"}
        )
        assert login_response.status_code == status.HTTP_200_OK
        login_data = login_response.json()
        refresh_token = login_data["refresh_token"]
        
        # Act
        response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token}
        )
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    async def test_refresh_token_invalid(self, client: AsyncClient):
        """Test token refresh with invalid token."""
        # Act
        response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "invalid_token"}
        )
        
        # Assert
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_health_check(self, client: AsyncClient):
        """Test health check endpoint."""
        # Act
        response = await client.get("/api/v1/health")
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data

    async def test_get_current_user(self, client: AsyncClient, user_token_headers, test_user):
        """Test getting current user information via validate endpoint."""
        # Act
        response = await client.get("/api/v1/auth/validate", headers=user_token_headers)
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["valid"] is True
        assert data["email"] == test_user.email

    async def test_get_current_user_unauthorized(self, client: AsyncClient):
        """Test getting current user without authentication."""
        # Act
        response = await client.get("/api/v1/auth/validate")
        
        # Assert
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_verify_email_success(self, client: AsyncClient, test_user, db_session):
        """Test successful email verification."""
        # Arrange - Generate verification token
        from app.services.auth import generate_email_verification_token
        verification_token = generate_email_verification_token()
        test_user.email_verification_token = verification_token
        test_user.is_email_verified = False
        await db_session.commit()
        await db_session.refresh(test_user)
        
        # Act
        response = await client.get(f"/api/v1/auth/verify-email/{verification_token}")
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["email_verified"] is True
        
        # Verify in database
        await db_session.refresh(test_user)
        assert test_user.is_email_verified is True
        assert test_user.email_verification_token is None

    async def test_verify_email_invalid_token(self, client: AsyncClient):
        """Test email verification with invalid token."""
        # Act
        response = await client.get("/api/v1/auth/verify-email/invalid_token")
        
        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    async def test_resend_verification_email_success(self, client: AsyncClient, test_user):
        """Test resending verification email."""
        # Arrange
        test_user.is_email_verified = False
        test_user.email_verification_token = None
        
        # Act
        response = await client.post(
            "/api/v1/auth/resend-verification",
            json={"email": test_user.email}
        )
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "message" in data

    async def test_resend_verification_email_already_verified(self, client: AsyncClient, test_user):
        """Test resending verification when already verified."""
        # Arrange
        test_user.is_email_verified = True
        
        # Act
        response = await client.post(
            "/api/v1/auth/resend-verification",
            json={"email": test_user.email}
        )
        
        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    async def test_request_password_reset(self, client: AsyncClient, test_user):
        """Test password reset request."""
        # Act
        response = await client.post(
            "/api/v1/auth/forgot-password",
            json={"email": test_user.email}
        )
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "message" in data

    async def test_request_password_reset_invalid_email(self, client: AsyncClient):
        """Test password reset request with invalid email."""
        # Act
        response = await client.post(
            "/api/v1/auth/forgot-password",
            json={"email": "nonexistent@example.com"}
        )
        
        # Assert
        # Should still return 200 to prevent email enumeration
        assert response.status_code == status.HTTP_200_OK

    async def test_registration_validation_errors(self, client: AsyncClient):
        """Test registration with various validation errors."""
        # Test missing required fields
        response = await client.post("/api/v1/auth/register", json={})
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        
        # Test invalid email format
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "invalid-email",
                "password": "ValidPass123!",
                "full_name": "Test User"
            }
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    async def test_login_missing_fields(self, client: AsyncClient):
        """Test login with missing fields."""
        # Missing password
        response = await client.post(
            "/api/v1/auth/login",
            data={"username": "test@example.com"}
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        
        # Missing username
        response = await client.post(
            "/api/v1/auth/login",
            data={"password": "password"}
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
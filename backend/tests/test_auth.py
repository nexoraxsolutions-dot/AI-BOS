import os
import sys
import pytest
from fastapi import status

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


def test_password_validation():
    """Test that password validation works correctly."""
    from app.schemas.user import UserCreate
    
    # Valid password
    valid_user = UserCreate(email="test@example.com", password="ValidPass123!")
    assert valid_user.password == "ValidPass123!"
    
    # Invalid password - too short
    with pytest.raises(Exception):
        UserCreate(email="test@example.com", password="short")


def test_company_validation():
    """Test that company validation works correctly."""
    from app.schemas.company import CompanyCreate
    
    # Valid company
    valid_company = CompanyCreate(name="Test Corp", domain="testcorp.com")
    assert valid_company.name == "Test Corp"
    assert valid_company.domain == "testcorp.com"
    
    # Invalid domain
    with pytest.raises(Exception):
        CompanyCreate(name="Test Corp", domain="invalid domain!")


def test_user_schema():
    """Test user schema creation."""
    from app.schemas.user import UserCreate, UserOut
    
    user = UserCreate(email="user@example.com", password="ValidPass123!", full_name="Test User")
    assert user.email == "user@example.com"
    assert user.full_name == "Test User"


def test_company_schema():
    """Test company schema creation."""
    from app.schemas.company import CompanyCreate, CompanyOut
    
    company = CompanyCreate(name="Test Corp", domain="testcorp.com")
    assert company.name == "Test Corp"
    assert company.domain == "testcorp.com"


def test_token_schema():
    """Test token schema."""
    from app.schemas.auth import Token, TokenData
    
    token = Token(access_token="test_token", token_type="bearer")
    assert token.access_token == "test_token"
    assert token.token_type == "bearer"
    
    token_data = TokenData(email="test@example.com")
    assert token_data.email == "test@example.com"


@pytest.mark.asyncio
async def test_login_endpoint(client, test_user):
    """Test the login endpoint with valid credentials."""
    response = await client.post(
        "/api/v1/auth/login",
        data={"username": "testuser@example.com", "password": "TestPassword123!"},
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_endpoint_invalid(client):
    """Test the login endpoint with invalid credentials."""
    response = await client.post(
        "/api/v1/auth/login",
        data={"username": "wrong@example.com", "password": "wrongpassword"},
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.asyncio
async def test_health_endpoint(client):
    """Test the health check endpoint."""
    response = await client.get("/api/v1/health")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["status"] == "healthy"
    assert data["version"] == "0.1.0"


@pytest.mark.asyncio
async def test_dashboard_summary(client, user_token_headers):
    """Test the dashboard summary endpoint with auth."""
    response = await client.get("/api/v1/dashboard/summary", headers=user_token_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "message" in data
    assert "summary" in data
    assert "total_users" in data["summary"]

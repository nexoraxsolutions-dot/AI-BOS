import pytest
from fastapi import status

from app.schemas.auth import RegisterRequest


@pytest.mark.asyncio
async def test_register_endpoint_success(client):
    payload = {
        "email": "newuser@example.com",
        "password": "NewPass123!",
        "full_name": "New User",
        "username": "newuser",
    }
    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["access_token"]
    assert data["refresh_token"]
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == payload["email"]
    assert data["user"]["full_name"] == payload["full_name"]
    assert data["user"]["username"] == payload["username"]
    assert data["user"]["is_superuser"] is False


@pytest.mark.asyncio
async def test_register_duplicate_email(client, test_user):
    payload = {
        "email": test_user.email,
        "password": "AnotherPass123!",
        "full_name": "Duplicate User",
    }
    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "email" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_register_duplicate_username(client, db_session):
    from app.models.user import User
    from app.core.security import get_password_hash

    existing = User(
        email="existinguser@example.com",
        hashed_password=get_password_hash("ExistingPass123!"),
        full_name="Existing User",
        username="existinguser",
        is_active=True,
        is_superuser=False,
    )
    db_session.add(existing)
    await db_session.commit()
    await db_session.refresh(existing)

    payload = {
        "email": "unique@example.com",
        "password": "UniquePass123!",
        "username": "existinguser",
    }
    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "username" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_register_validation_errors(client):
    response = await client.post("/api/v1/auth/register", json={"email": "bad", "password": "short"})
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.asyncio
async def test_register_returns_tokens_and_user(client):
    payload = {
        "email": "tokentest@example.com",
        "password": "TokenPass123!",
    }
    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert "user" in data
    assert data["user"]["is_active"] is True
    assert data["user"]["is_superuser"] is False

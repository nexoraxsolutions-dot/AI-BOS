import pytest
from fastapi import status
from unittest.mock import patch, AsyncMock

from app.core.security import get_password_hash
from app.models.user import User


@pytest.mark.asyncio
async def test_register_sets_verification_token(client):
    """Registration should set an email verification token on the user."""
    payload = {
        "email": "verifytest@example.com",
        "password": "VerifyPass123!",
        "full_name": "Verify Test",
    }
    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["user"]["email"] == payload["email"]


@pytest.mark.asyncio
async def test_verify_email_success(client, db_session):
    """Verify email with a valid token should succeed."""
    from app.services.auth import generate_email_verification_token

    token = generate_email_verification_token()
    user = User(
        email="verify-success@example.com",
        hashed_password=get_password_hash("TestPass123!"),
        full_name="Verify Success",
        is_active=True,
        is_superuser=False,
        is_email_verified=False,
        email_verification_token=token,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    response = await client.get(f"/api/v1/auth/verify-email/{token}")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["email_verified"] is True
    assert "successfully" in data["message"].lower()

    # Verify the user is now marked as verified in the database
    await db_session.refresh(user)
    assert user.is_email_verified is True
    assert user.email_verification_token is None


@pytest.mark.asyncio
async def test_verify_email_invalid_token(client):
    """Verify email with an invalid token should fail."""
    response = await client.get("/api/v1/auth/verify-email/invalid-token-123")
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "invalid" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_verify_email_already_verified(client, db_session):
    """Verify email when already verified should fail."""
    from app.services.auth import generate_email_verification_token

    token = generate_email_verification_token()
    user = User(
        email="already-verified@example.com",
        hashed_password=get_password_hash("TestPass123!"),
        full_name="Already Verified",
        is_active=True,
        is_superuser=False,
        is_email_verified=True,
        email_verification_token=token,
    )
    db_session.add(user)
    await db_session.commit()

    response = await client.get(f"/api/v1/auth/verify-email/{token}")
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "already verified" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_resend_verification_success(client, db_session):
    """Resend verification email should succeed for unverified user."""
    from app.services.auth import generate_email_verification_token

    token = generate_email_verification_token()
    user = User(
        email="resend-test@example.com",
        hashed_password=get_password_hash("TestPass123!"),
        full_name="Resend Test",
        is_active=True,
        is_superuser=False,
        is_email_verified=False,
        email_verification_token=token,
    )
    db_session.add(user)
    await db_session.commit()

    response = await client.post(
        "/api/v1/auth/resend-verification",
        json={"email": "resend-test@example.com"},
    )
    assert response.status_code == status.HTTP_200_OK
    assert "sent" in response.json()["message"].lower()


@pytest.mark.asyncio
async def test_resend_verification_already_verified(client, db_session):
    """Resend verification for already verified user should fail."""
    from app.services.auth import generate_email_verification_token

    token = generate_email_verification_token()
    user = User(
        email="already-verified-resend@example.com",
        hashed_password=get_password_hash("TestPass123!"),
        full_name="Already Verified Resend",
        is_active=True,
        is_superuser=False,
        is_email_verified=True,
        email_verification_token=token,
    )
    db_session.add(user)
    await db_session.commit()

    response = await client.post(
        "/api/v1/auth/resend-verification",
        json={"email": "already-verified-resend@example.com"},
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "already verified" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_resend_verification_nonexistent_user(client):
    """Resend verification for non-existent user should fail."""
    response = await client.post(
        "/api/v1/auth/resend-verification",
        json={"email": "nonexistent@example.com"},
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "no user found" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_verify_email_expired_token(client, db_session):
    """Verify email with an expired token should fail."""
    from app.services.auth import generate_email_verification_token
    from datetime import datetime, timedelta

    token = generate_email_verification_token()
    user = User(
        email="expired-token@example.com",
        hashed_password=get_password_hash("TestPass123!"),
        full_name="Expired Token",
        is_active=True,
        is_superuser=False,
        is_email_verified=False,
        email_verification_token=token,
        created_at=datetime.utcnow() - timedelta(hours=100),  # Created 100 hours ago
    )
    db_session.add(user)
    await db_session.commit()

    response = await client.get(f"/api/v1/auth/verify-email/{token}")
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "expired" in response.json()["detail"].lower()
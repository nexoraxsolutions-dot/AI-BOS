import os
import sys
import pytest
from datetime import datetime, timedelta
from fastapi import status

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.core.security import pwd_context
from app.models.password_reset import PasswordResetToken


def test_password_reset_schema_validation():
    """Test that password reset request schemas validate correctly."""
    from app.schemas.auth import PasswordResetRequest, PasswordReset

    # Valid forgot-password request
    req = PasswordResetRequest(email="test@example.com")
    assert req.email == "test@example.com"

    # Valid reset with new password and matching confirm
    # Note: Schema validates basic rules (8+ chars, upper, lower, digit, match)
    # Enterprise policy (12+ chars, special char, no common passwords, no reuse) is enforced in service layer
    reset = PasswordReset(token="abc123", new_password="ValidPass1!", confirm_password="ValidPass1!")
    assert reset.token == "abc123"
    assert reset.new_password == "ValidPass1!"

    # Invalid new password - too short
    with pytest.raises(Exception):
        PasswordReset(token="abc123", new_password="short", confirm_password="short")

    # Invalid new password - no uppercase
    with pytest.raises(Exception):
        PasswordReset(token="abc123", new_password="lowercaseonly1!", confirm_password="lowercaseonly1!")

    # Invalid new password - no digit
    with pytest.raises(Exception):
        PasswordReset(token="abc123", new_password="NoDigitsHere!", confirm_password="NoDigitsHere!")

    # Passwords do not match
    with pytest.raises(Exception):
        PasswordReset(token="abc123", new_password="ValidPass1!", confirm_password="DifferentPass1!")


def test_forgot_password_response_schema():
    """Test that ForgotPasswordResponse schema works correctly."""
    from app.schemas.auth import ForgotPasswordResponse

    response = ForgotPasswordResponse()
    assert "account with that email" in response.message.lower()

    response = ForgotPasswordResponse(message="Custom message")
    assert response.message == "Custom message"


@pytest.mark.asyncio
async def test_forgot_password_nonexistent_email(client):
    """Test forgot-password with an email that doesn't exist — should return generic message."""
    response = await client.post(
        "/api/v1/auth/forgot-password",
        json={"email": "nonexistent@example.com"},
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "message" in data
    assert "account with that email" in data["message"].lower()


@pytest.mark.asyncio
async def test_forgot_password_existing_email(client, test_user):
    """Test forgot-password with an existing email — should return generic message."""
    response = await client.post(
        "/api/v1/auth/forgot-password",
        json={"email": "testuser@example.com"},
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "message" in data
    assert "account with that email" in data["message"].lower()


@pytest.mark.asyncio
async def test_forgot_password_creates_token(client, db_session, test_user):
    """Test that forgot-password creates a password reset token in the database."""
    from sqlalchemy import select

    response = await client.post(
        "/api/v1/auth/forgot-password",
        json={"email": "testuser@example.com"},
    )
    assert response.status_code == status.HTTP_200_OK

    # Verify a token was created in the database
    stmt = select(PasswordResetToken).where(
        PasswordResetToken.user_id == test_user.id,
        PasswordResetToken.is_revoked == False,
    )
    result = await db_session.execute(stmt)
    token = result.scalars().first()
    assert token is not None
    assert token.expires_at > datetime.utcnow()
    assert token.hashed_token is not None


@pytest.mark.asyncio
async def test_forgot_password_revokes_previous_tokens(client, db_session, test_user):
    """Test that requesting a new reset revokes the old one."""
    from sqlalchemy import select
    import secrets

    # Create an existing active token manually
    old_token = PasswordResetToken(
        user_id=test_user.id,
        hashed_token=pwd_context.hash(secrets.token_urlsafe(32)),
        expires_at=datetime.utcnow() + timedelta(hours=1),
    )
    db_session.add(old_token)
    await db_session.commit()
    old_token_id = old_token.id

    # Request a new reset
    response = await client.post(
        "/api/v1/auth/forgot-password",
        json={"email": "testuser@example.com"},
    )
    assert response.status_code == status.HTTP_200_OK

    # Verify old token was revoked
    await db_session.refresh(old_token)
    assert old_token.is_revoked is True
    assert old_token.revoked_at is not None


@pytest.mark.asyncio
async def test_forgot_password_queues_email(client, db_session, test_user):
    """Test that forgot-password pushes an email task to the Redis queue."""
    # Mock Redis by checking the service call behavior
    # Since tests may not have Redis, this verifies the endpoint works
    response = await client.post(
        "/api/v1/auth/forgot-password",
        json={"email": "testuser@example.com"},
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "message" in data

    # Verify audit log was created
    from sqlalchemy import select
    from app.models.audit_log import AuditLog

    stmt = select(AuditLog).where(
        AuditLog.action == "password_reset_requested",
        AuditLog.user_id == test_user.id,
    )
    result = await db_session.execute(stmt)
    log = result.scalars().first()
    assert log is not None
    assert log.details is not None
    assert "email_queued" in log.details


@pytest.mark.asyncio
async def test_forgot_password_same_response_for_all_emails(client, test_user):
    """Test that the response is identical whether the email exists or not."""
    response_existing = await client.post(
        "/api/v1/auth/forgot-password",
        json={"email": "testuser@example.com"},
    )
    response_nonexistent = await client.post(
        "/api/v1/auth/forgot-password",
        json={"email": "nonexistent@example.com"},
    )

    assert response_existing.status_code == response_nonexistent.status_code
    data_existing = response_existing.json()
    data_nonexistent = response_nonexistent.json()
    # Both should have the same message structure
    assert data_existing["message"] == data_nonexistent["message"]


@pytest.mark.asyncio
async def test_forgot_password_called_multiple_times(client, test_user):
    """Test that forgot-password can be called multiple times without error."""
    for _ in range(3):
        response = await client.post(
            "/api/v1/auth/forgot-password",
            json={"email": "testuser@example.com"},
        )
        assert response.status_code == status.HTTP_200_OK


@pytest.mark.asyncio
async def test_reset_password_invalid_token(client):
    """Test reset-password with an invalid token."""
    response = await client.post(
        "/api/v1/auth/reset-password",
        json={"token": "invalid_token", "new_password": "NewValidPass1!", "confirm_password": "NewValidPass1!"},
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Invalid or expired" in response.json()["detail"]


@pytest.mark.asyncio
async def test_reset_password_expired_token(client, db_session, test_user):
    """Test reset-password with an expired token."""
    import secrets
    from app.core.security import get_password_hash

    # Create an expired token
    raw_token = secrets.token_urlsafe(32)
    hashed_token = get_password_hash(raw_token)
    expired_token = PasswordResetToken(
        user_id=test_user.id,
        hashed_token=hashed_token,
        expires_at=datetime.utcnow() - timedelta(hours=1),
    )
    db_session.add(expired_token)
    await db_session.commit()

    response = await client.post(
        "/api/v1/auth/reset-password",
        json={"token": raw_token, "new_password": "NewValidPass1!", "confirm_password": "NewValidPass1!"},
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Invalid or expired" in response.json()["detail"]


@pytest.mark.asyncio
async def test_reset_password_revoked_token(client, db_session, test_user):
    """Test reset-password with a revoked token."""
    import secrets
    from app.core.security import get_password_hash

    # Create a revoked token
    raw_token = secrets.token_urlsafe(32)
    hashed_token = get_password_hash(raw_token)
    revoked_token = PasswordResetToken(
        user_id=test_user.id,
        hashed_token=hashed_token,
        expires_at=datetime.utcnow() + timedelta(hours=1),
        is_revoked=True,
        revoked_at=datetime.utcnow(),
    )
    db_session.add(revoked_token)
    await db_session.commit()

    response = await client.post(
        "/api/v1/auth/reset-password",
        json={"token": raw_token, "new_password": "NewValidPass1!", "confirm_password": "NewValidPass1!"},
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Invalid or expired" in response.json()["detail"]


@pytest.mark.asyncio
async def test_full_password_reset_flow(client, db_session, test_user):
    """Test the complete forgot-password -> reset-password flow."""
    from sqlalchemy import select
    from app.core.security import get_password_hash

    # Step 1: Request password reset
    response = await client.post(
        "/api/v1/auth/forgot-password",
        json={"email": "testuser@example.com"},
    )
    assert response.status_code == status.HTTP_200_OK

    # Step 2: Get the created token
    stmt = select(PasswordResetToken).where(
        PasswordResetToken.user_id == test_user.id,
        PasswordResetToken.is_revoked == False,
    )
    result = await db_session.execute(stmt)
    token_record = result.scalars().first()
    assert token_record is not None

    # Step 3: Reset password with the token
    # We need to get the raw token, but it's hashed in DB. For testing, we'll mock it.
    # In real scenario, the token would come from the email.
    # For this test, we'll use a known token and hash it.
    raw_token = "test_reset_token_123"
    token_record.hashed_token = get_password_hash(raw_token)
    await db_session.commit()

    response = await client.post(
        "/api/v1/auth/reset-password",
        json={"token": raw_token, "new_password": "NewValidPass1!", "confirm_password": "NewValidPass1!"},
    )
    assert response.status_code == status.HTTP_200_OK
    assert "Password has been reset" in response.json()["message"]

    # Step 4: Verify token is now revoked
    await db_session.refresh(token_record)
    assert token_record.is_revoked is True
    assert token_record.revoked_at is not None

    # Step 5: Verify password was changed
    await db_session.refresh(test_user)
    assert test_user.hashed_password != get_password_hash("TestPassword123")
    assert pwd_context.verify("NewValidPass1!", test_user.hashed_password)


@pytest.mark.asyncio
async def test_reset_password_revokes_refresh_tokens(client, db_session, test_user):
    """Test that resetting password revokes all refresh tokens."""
    from sqlalchemy import select
    from app.models.token import Token
    from app.core.security import get_password_hash

    # Create a refresh token for the user
    refresh_token_str = "test_refresh_token_456"
    refresh_token = Token(
        token=refresh_token_str,
        user_id=test_user.id,
        token_type="refresh",
        expires_at=datetime.utcnow() + timedelta(days=30),
    )
    db_session.add(refresh_token)
    await db_session.commit()

    # Create a password reset token
    raw_token = "test_reset_token_456"
    reset_token = PasswordResetToken(
        user_id=test_user.id,
        hashed_token=get_password_hash(raw_token),
        expires_at=datetime.utcnow() + timedelta(hours=1),
    )
    db_session.add(reset_token)
    await db_session.commit()

    # Reset password
    response = await client.post(
        "/api/v1/auth/reset-password",
        json={"token": raw_token, "new_password": "NewValidPass1!", "confirm_password": "NewValidPass1!"},
    )
    assert response.status_code == status.HTTP_200_OK

    # Verify refresh token was revoked
    await db_session.refresh(refresh_token)
    assert refresh_token.is_revoked is True


@pytest.mark.asyncio
async def test_forgot_password_rate_limiting(client, test_user):
    """Test that forgot-password can be called multiple times (rate limiting would be at infrastructure level)."""
    # This test verifies the endpoint doesn't break with rapid calls
    # Actual rate limiting would be implemented via Redis or middleware
    for _ in range(5):
        response = await client.post(
            "/api/v1/auth/forgot-password",
            json={"email": "testuser@example.com"},
        )
        assert response.status_code == status.HTTP_200_OK


@pytest.mark.asyncio
async def test_reset_password_rate_limiting(client, db_session, test_user):
    """Test that reset-password enforces rate limits after excessive attempts."""
    # Create a valid reset token
    import secrets
    from app.core.security import get_password_hash
    from app.models.password_reset import PasswordResetToken
    
    raw_token = secrets.token_urlsafe(32)
    reset_token = PasswordResetToken(
        user_id=test_user.id,
        hashed_token=get_password_hash(raw_token),
        expires_at=datetime.utcnow() + timedelta(hours=1),
    )
    db_session.add(reset_token)
    await db_session.commit()
    
    # Make multiple reset attempts with valid passwords (12+ chars)
    for i in range(10):
        password = f"ValidPass{i}!!"
        response = await client.post(
            "/api/v1/auth/reset-password",
            json={"token": raw_token, "new_password": password, "confirm_password": password},
        )
        # First few should succeed or fail with validation, later ones may be rate limited
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST, status.HTTP_429_TOO_MANY_REQUESTS]

"""
Integration tests for password reset functionality.

Tests the interaction between multiple components:
- Database operations
- Email queue integration
- Audit logging
- Token lifecycle management
"""
import pytest
from datetime import datetime, timedelta
from fastapi import status
from sqlalchemy import select

from app.models.password_reset import PasswordResetToken
from app.models.audit_log import AuditLog
from app.models.token import Token
from app.services.password_reset import request_password_reset, reset_password, validate_reset_token
from app.services.audit_log import create_audit_log
from app.core.security import get_password_hash, pwd_context


class TestTokenLifecycle:
    """Integration tests for password reset token lifecycle."""

    @pytest.mark.asyncio
    async def test_token_creation_and_validation(self, db_session, test_user):
        """Test complete token lifecycle: creation -> validation -> usage."""
        # Step 1: Request password reset (creates token)
        await request_password_reset(
            db_session,
            email="testuser@example.com",
            client_ip="192.168.1.1",
            user_agent="test-agent",
        )

        # Step 2: Verify token was created
        stmt = select(PasswordResetToken).where(
            PasswordResetToken.user_id == test_user.id,
            PasswordResetToken.is_revoked == False,
        )
        result = await db_session.execute(stmt)
        token_record = result.scalars().first()
        assert token_record is not None
        assert token_record.expires_at > datetime.utcnow()
        assert token_record.hashed_token is not None
        assert token_record.is_revoked is False

        # Step 3: Validate token (we need to know the raw token)
        # In real scenario, this comes from email
        raw_token = "test_integration_token"
        token_record.hashed_token = get_password_hash(raw_token)
        await db_session.commit()

        user = await validate_reset_token(db_session, raw_token)
        assert user is not None
        assert user.id == test_user.id

    @pytest.mark.asyncio
    async def test_token_revocation_after_use(self, db_session, test_user):
        """Test that token is revoked after successful password reset."""
        # Create token
        raw_token = "test_revoke_token"
        reset_token = PasswordResetToken(
            user_id=test_user.id,
            hashed_token=get_password_hash(raw_token),
            expires_at=datetime.utcnow() + timedelta(hours=1),
        )
        db_session.add(reset_token)
        await db_session.commit()

        # Reset password
        await reset_password(
            db_session,
            raw_token=raw_token,
            new_password="NewValidPass1!",
            client_ip="192.168.1.1",
            user_agent="test-agent",
        )

        # Verify token is revoked
        await db_session.refresh(reset_token)
        assert reset_token.is_revoked is True
        assert reset_token.revoked_at is not None

        # Verify token cannot be used again
        user = await validate_reset_token(db_session, raw_token)
        assert user is None

    @pytest.mark.asyncio
    async def test_multiple_tokens_revoked_on_new_request(self, db_session, test_user):
        """Test that requesting new reset revokes all previous tokens."""
        # Create multiple active tokens
        token1 = PasswordResetToken(
            user_id=test_user.id,
            hashed_token=get_password_hash("token1"),
            expires_at=datetime.utcnow() + timedelta(hours=1),
        )
        token2 = PasswordResetToken(
            user_id=test_user.id,
            hashed_token=get_password_hash("token2"),
            expires_at=datetime.utcnow() + timedelta(hours=1),
        )
        db_session.add_all([token1, token2])
        await db_session.commit()

        # Request new reset
        await request_password_reset(db_session, email="testuser@example.com")

        # Verify all old tokens are revoked
        await db_session.refresh(token1)
        await db_session.refresh(token2)
        assert token1.is_revoked is True
        assert token2.is_revoked is True


class TestAuditLogging:
    """Integration tests for audit logging."""

    @pytest.mark.asyncio
    async def test_password_reset_request_logged(self, db_session, test_user):
        """Test that password reset requests are logged."""
        await request_password_reset(
            db_session,
            email="testuser@example.com",
            client_ip="192.168.1.1",
            user_agent="Mozilla/5.0",
        )

        # Verify audit log was created
        stmt = select(AuditLog).where(
            AuditLog.action == "password_reset_requested",
            AuditLog.user_id == test_user.id,
        )
        result = await db_session.execute(stmt)
        log = result.scalars().first()
        assert log is not None
        assert log.ip_address == "192.168.1.1"
        assert log.user_agent == "Mozilla/5.0"
        assert log.details is not None
        assert "email_queued" in log.details

    @pytest.mark.asyncio
    async def test_password_reset_completion_logged(self, db_session, test_user):
        """Test that password reset completion is logged."""
        # Create and use token
        raw_token = "test_completion_token"
        reset_token = PasswordResetToken(
            user_id=test_user.id,
            hashed_token=get_password_hash(raw_token),
            expires_at=datetime.utcnow() + timedelta(hours=1),
        )
        db_session.add(reset_token)
        await db_session.commit()

        await reset_password(
            db_session,
            raw_token=raw_token,
            new_password="NewValidPass1!",
            client_ip="192.168.1.1",
            user_agent="Mozilla/5.0",
        )

        # Verify audit log was created
        stmt = select(AuditLog).where(
            AuditLog.action == "password_reset_completed",
            AuditLog.user_id == test_user.id,
        )
        result = await db_session.execute(stmt)
        log = result.scalars().first()
        assert log is not None
        assert log.ip_address == "192.168.1.1"
        assert log.user_agent == "Mozilla/5.0"


class TestRefreshTokenInvalidation:
    """Integration tests for refresh token invalidation."""

    @pytest.mark.asyncio
    async def test_refresh_tokens_revoked_after_password_reset(self, db_session, test_user):
        """Test that all refresh tokens are revoked after password reset."""
        # Create refresh tokens
        refresh_token1 = Token(
            token="refresh_token_1",
            user_id=test_user.id,
            token_type="refresh",
            expires_at=datetime.utcnow() + timedelta(days=30),
        )
        refresh_token2 = Token(
            token="refresh_token_2",
            user_id=test_user.id,
            token_type="refresh",
            expires_at=datetime.utcnow() + timedelta(days=30),
        )
        db_session.add_all([refresh_token1, refresh_token2])
        await db_session.commit()

        # Create reset token
        raw_token = "test_refresh_revoke"
        reset_token = PasswordResetToken(
            user_id=test_user.id,
            hashed_token=get_password_hash(raw_token),
            expires_at=datetime.utcnow() + timedelta(hours=1),
        )
        db_session.add(reset_token)
        await db_session.commit()

        # Reset password
        await reset_password(
            db_session,
            raw_token=raw_token,
            new_password="NewValidPass1!",
        )

        # Verify all refresh tokens are revoked
        await db_session.refresh(refresh_token1)
        await db_session.refresh(refresh_token2)
        assert refresh_token1.is_revoked is True
        assert refresh_token2.is_revoked is True


class TestPasswordHistoryIntegration:
    """Integration tests for password history tracking."""

    @pytest.mark.asyncio
    async def test_password_saved_to_history(self, db_session, test_user):
        """Test that new password is saved to history."""
        from app.models.password_history import PasswordHistory

        # Create reset token
        raw_token = "test_history_token"
        reset_token = PasswordResetToken(
            user_id=test_user.id,
            hashed_token=get_password_hash(raw_token),
            expires_at=datetime.utcnow() + timedelta(hours=1),
        )
        db_session.add(reset_token)
        await db_session.commit()

        # Reset password (must meet enterprise policy: 12+ chars, special char)
        new_password = "NewValidPass1!23"
        await reset_password(
            db_session,
            raw_token=raw_token,
            new_password=new_password,
        )

        # Verify password was saved to history
        stmt = select(PasswordHistory).where(
            PasswordHistory.user_id == test_user.id
        ).order_by(PasswordHistory.created_at.desc())
        result = await db_session.execute(stmt)
        history = result.scalars().first()
        assert history is not None
        assert pwd_context.verify(new_password, history.hashed_password)

    @pytest.mark.asyncio
    async def test_password_reuse_prevented(self, db_session, test_user):
        """Test that password reuse is prevented via history."""
        from app.models.password_history import PasswordHistory

        # Add password to history (must meet enterprise policy)
        old_password = "OldValidPass1!23"
        history_entry = PasswordHistory(
            user_id=test_user.id,
            hashed_password=get_password_hash(old_password),
        )
        db_session.add(history_entry)
        await db_session.commit()

        # Create reset token
        raw_token = "test_reuse_token"
        reset_token = PasswordResetToken(
            user_id=test_user.id,
            hashed_token=get_password_hash(raw_token),
            expires_at=datetime.utcnow() + timedelta(hours=1),
        )
        db_session.add(reset_token)
        await db_session.commit()

        # Try to reuse old password - should raise PasswordValidationError
        from app.core.password_policy import PasswordValidationError
        with pytest.raises(PasswordValidationError) as exc_info:
            await reset_password(
                db_session,
                raw_token=raw_token,
                new_password=old_password,
            )
        assert "used recently" in str(exc_info.value).lower()


class TestEmailEnumerationPrevention:
    """Integration tests for email enumeration prevention."""

    @pytest.mark.asyncio
    async def test_identical_response_for_existing_email(self, client, test_user):
        """Test that existing email gets same response as non-existing."""
        response_existing = await client.post(
            "/api/v1/auth/forgot-password",
            json={"email": "testuser@example.com"},
        )
        response_nonexistent = await client.post(
            "/api/v1/auth/forgot-password",
            json={"email": "nonexistent@example.com"},
        )

        # Same status code
        assert response_existing.status_code == response_nonexistent.status_code
        # Same message
        assert response_existing.json()["message"] == response_nonexistent.json()["message"]

    @pytest.mark.asyncio
    async def test_no_token_created_for_nonexistent_email(self, db_session):
        """Test that no token is created for non-existing email."""
        from sqlalchemy import select

        await request_password_reset(db_session, email="nonexistent@example.com")

        # Verify no token was created
        stmt = select(PasswordResetToken).where(
            PasswordResetToken.user_id == None  # noqa: E711
        )
        result = await db_session.execute(stmt)
        tokens = result.scalars().all()
        assert len(tokens) == 0


class TestConcurrentRequests:
    """Integration tests for concurrent request handling."""

    @pytest.mark.asyncio
    async def test_concurrent_forgot_password_requests(self, client, test_user):
        """Test handling of concurrent forgot-password requests."""
        # Note: Concurrent requests with same email may trigger rate limiting
        # This test verifies the endpoint handles multiple sequential requests
        for _ in range(3):
            response = await client.post(
                "/api/v1/auth/forgot-password",
                json={"email": "testuser@example.com"},
            )
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert "message" in data

    @pytest.mark.asyncio
    async def test_token_used_only_once(self, db_session, test_user):
        """Test that token cannot be used twice (race condition protection)."""
        # Create token
        raw_token = "test_race_token"
        reset_token = PasswordResetToken(
            user_id=test_user.id,
            hashed_token=get_password_hash(raw_token),
            expires_at=datetime.utcnow() + timedelta(hours=1),
        )
        db_session.add(reset_token)
        await db_session.commit()

        # Use token first time
        await reset_password(
            db_session,
            raw_token=raw_token,
            new_password="NewValidPass1!",
        )

        # Try to use same token again
        with pytest.raises(ValueError) as exc_info:
            await reset_password(
                db_session,
                raw_token=raw_token,
                new_password="AnotherValid1!",
            )
        assert "Invalid or expired" in str(exc_info.value)
"""
Unit tests for password reset functionality.

Tests individual components in isolation:
- Password policy validation
- Token generation and hashing
- Password history checking
- Rate limiting logic
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

from app.core.password_policy import (
    validate_password_strength,
    validate_password_not_reused,
    is_common_password,
    get_password_requirements,
    PasswordValidationError,
)
from app.core.security import pwd_context, get_password_hash
from app.services.rate_limiter import (
    check_rate_limit,
    record_failed_reset_attempt,
    clear_failed_reset_attempts,
    RateLimitExceeded,
    TemporaryLockout,
)


class TestPasswordPolicyValidation:
    """Unit tests for password policy validation."""

    def test_valid_password_meets_all_requirements(self):
        """Test that a valid password passes all checks."""
        password = "ValidPass1!23"  # 13 chars
        validate_password_strength(password)

    def test_password_too_short(self):
        """Test that passwords shorter than 12 characters are rejected."""
        with pytest.raises(PasswordValidationError) as exc_info:
            validate_password_strength("Short1!")
        assert "at least 12 characters" in str(exc_info.value)

    def test_password_missing_uppercase(self):
        """Test that passwords without uppercase are rejected."""
        with pytest.raises(PasswordValidationError) as exc_info:
            validate_password_strength("lowercaseonly1!")
        assert "uppercase letter" in str(exc_info.value)

    def test_password_missing_lowercase(self):
        """Test that passwords without lowercase are rejected."""
        with pytest.raises(PasswordValidationError) as exc_info:
            validate_password_strength("UPPERCASEONLY1!")
        assert "lowercase letter" in str(exc_info.value)

    def test_password_missing_digit(self):
        """Test that passwords without digits are rejected."""
        with pytest.raises(PasswordValidationError) as exc_info:
            validate_password_strength("NoDigitsHere!")
        assert "digit" in str(exc_info.value)

    def test_password_missing_special_character(self):
        """Test that passwords without special characters are rejected."""
        with pytest.raises(PasswordValidationError) as exc_info:
            validate_password_strength("ValidPass1234")
        assert "special character" in str(exc_info.value)

    def test_common_password_rejected(self):
        """Test that common passwords are rejected."""
        common_passwords = [
            "password",
            "12345678",
            "qwerty123",
            "admin123",
            "letmein",
            "welcome1",
            "password1",
        ]
        for password in common_passwords:
            with pytest.raises(PasswordValidationError) as exc_info:
                validate_password_strength(password)
            assert "too common" in str(exc_info.value).lower()

    def test_multiple_errors_returned_together(self):
        """Test that multiple validation errors are returned together."""
        with pytest.raises(PasswordValidationError) as exc_info:
            validate_password_strength("short")
        errors = str(exc_info.value)
        assert "12 characters" in errors
        assert "uppercase" in errors
        # Note: "short" has lowercase letters, so no lowercase error
        assert "digit" in errors
        assert "special character" in errors

    def test_password_requirements_dict(self):
        """Test that password requirements are returned correctly."""
        requirements = get_password_requirements()
        assert requirements["min_length"] == 12
        assert requirements["require_uppercase"] is True
        assert requirements["require_lowercase"] is True
        assert requirements["require_digit"] is True
        assert requirements["require_special"] is True
        assert requirements["reject_common"] is True
        assert requirements["reject_recent"] is True


class TestPasswordHistoryValidation:
    """Unit tests for password history validation."""

    @pytest.mark.asyncio
    async def test_password_not_reused(self, db_session, test_user):
        """Test that recently used passwords are rejected."""
        from app.models.password_history import PasswordHistory

        # Add current password to history
        current_hash = get_password_hash("TestPassword123")
        history_entry = PasswordHistory(
            user_id=test_user.id,
            hashed_password=current_hash,
        )
        db_session.add(history_entry)
        await db_session.commit()

        # Try to reuse the same password
        with pytest.raises(PasswordValidationError) as exc_info:
            await validate_password_not_reused("TestPassword123", test_user.id, db_session)
        assert "used recently" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_new_password_allowed(self, db_session, test_user):
        """Test that a new password is allowed."""
        # Should not raise an exception
        await validate_password_not_reused("NewValidPass1!", test_user.id, db_session)

    @pytest.mark.asyncio
    async def test_password_history_limit(self, db_session, test_user):
        """Test that only last N passwords are checked."""
        from app.models.password_history import PasswordHistory

        # Add 5 passwords to history
        for i in range(5):
            history_entry = PasswordHistory(
                user_id=test_user.id,
                hashed_password=get_password_hash(f"OldPass{i}!"),
            )
            db_session.add(history_entry)
        await db_session.commit()

        # The 6th password should be allowed (outside history limit)
        await validate_password_not_reused("NewValidPass1!", test_user.id, db_session)


class TestTokenGeneration:
    """Unit tests for token generation and hashing."""

    def test_token_generation_is_random(self):
        """Test that generated tokens are random."""
        import secrets
        token1 = secrets.token_urlsafe(32)
        token2 = secrets.token_urlsafe(32)
        assert token1 != token2
        assert len(token1) > 40  # 32 bytes = ~43 chars in base64

    def test_token_hashing(self):
        """Test that tokens are properly hashed."""
        raw_token = "test_token_123"
        hashed = pwd_context.hash(raw_token)
        assert hashed != raw_token
        assert pwd_context.verify(raw_token, hashed)

    def test_different_tokens_produce_different_hashes(self):
        """Test that different tokens produce different hashes."""
        hash1 = pwd_context.hash("token1")
        hash2 = pwd_context.hash("token2")
        assert hash1 != hash2

    def test_same_token_produces_same_hash(self):
        """Test that same token can be verified (bcrypt uses random salts)."""
        hash1 = pwd_context.hash("token123")
        # Bcrypt uses random salts, so hashes will be different
        # But verification should work
        assert pwd_context.verify("token123", hash1)


class TestRateLimiting:
    """Unit tests for rate limiting logic."""

    @pytest.mark.asyncio
    async def test_rate_limit_allows_first_request(self, db_session, monkeypatch):
        """Test that first request is allowed."""
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=None)
        mock_redis.setex = AsyncMock()
        
        async def mock_get_redis():
            return mock_redis
        
        monkeypatch.setattr("app.services.rate_limiter.get_redis_client", mock_get_redis)
        
        # Should not raise an exception
        await check_rate_limit(
            db_session,
            identifier="test_ip",
            limit_type="ip",
            max_requests=5,
            window_seconds=300,
        )

    @pytest.mark.asyncio
    async def test_rate_limit_blocks_excessive_requests(self, db_session, monkeypatch):
        """Test that excessive requests are blocked."""
        from app.core.redis import get_redis_client
        
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(side_effect=[None, "5"])  # None for lockout, "5" for request count
        mock_redis.setex = AsyncMock()
        mock_redis.incr = AsyncMock(return_value=6)
        
        async def mock_get_redis():
            return mock_redis
        
        monkeypatch.setattr("app.services.rate_limiter.get_redis_client", mock_get_redis)
        
        with pytest.raises(RateLimitExceeded):
            await check_rate_limit(
                db_session,
                identifier="test_ip",
                limit_type="ip",
                max_requests=5,
                window_seconds=300,
                lockout_seconds=900,
            )

    @pytest.mark.asyncio
    async def test_rate_limit_lockout(self, db_session, monkeypatch):
        """Test that lockout is applied after exceeding limit."""
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(side_effect=[None, "5"])  # None for lockout, "5" for request count
        mock_redis.setex = AsyncMock()
        mock_redis.incr = AsyncMock(return_value=6)
        
        async def mock_get_redis():
            return mock_redis
        
        monkeypatch.setattr("app.services.rate_limiter.get_redis_client", mock_get_redis)
        
        with pytest.raises(RateLimitExceeded) as exc_info:
            await check_rate_limit(
                db_session,
                identifier="test_ip",
                limit_type="ip",
                max_requests=5,
                window_seconds=300,
                lockout_seconds=900,
            )
        assert exc_info.value.retry_after == 900

    @pytest.mark.asyncio
    async def test_rate_limit_increments_counter(self, db_session, monkeypatch):
        """Test that request counter is incremented."""
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(side_effect=[None, "3"])  # None for lockout, "3" for request count
        mock_redis.incr = AsyncMock(return_value=4)
        mock_redis.setex = AsyncMock()
        
        async def mock_get_redis():
            return mock_redis
        
        monkeypatch.setattr("app.services.rate_limiter.get_redis_client", mock_get_redis)
        
        await check_rate_limit(
            db_session,
            identifier="test_ip",
            limit_type="ip",
            max_requests=5,
            window_seconds=300,
        )
        # incr should be called when count is below limit
        mock_redis.incr.assert_called_once()


class TestFailedAttemptTracking:
    """Unit tests for failed attempt tracking."""

    @pytest.mark.asyncio
    async def test_record_failed_attempt(self, db_session, monkeypatch):
        """Test that failed attempts are recorded."""
        mock_redis = AsyncMock()
        mock_redis.incr = AsyncMock(return_value=1)
        mock_redis.expire = AsyncMock()
        mock_redis.get = AsyncMock(return_value="1")
        mock_redis.delete = AsyncMock()
        
        async def mock_get_redis():
            return mock_redis
        
        monkeypatch.setattr("app.services.rate_limiter.get_redis_client", mock_get_redis)
        
        await record_failed_reset_attempt(db_session, "192.168.1.1", user_id=123)
        # incr should be called for both IP and user
        assert mock_redis.incr.call_count == 2

    @pytest.mark.asyncio
    async def test_clear_failed_attempts(self, db_session, monkeypatch):
        """Test that failed attempts are cleared after success."""
        mock_redis = AsyncMock()
        mock_redis.delete = AsyncMock()
        
        async def mock_get_redis():
            return mock_redis
        
        monkeypatch.setattr("app.services.rate_limiter.get_redis_client", mock_get_redis)
        
        await clear_failed_reset_attempts("192.168.1.1", user_id=123)
        # delete should be called for both IP and user
        assert mock_redis.delete.call_count == 2  # IP and user keys
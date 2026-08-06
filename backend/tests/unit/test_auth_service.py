"""Unit tests for authentication service layer."""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime, timedelta

from app.services.auth import (
    authenticate_user,
    generate_email_verification_token,
    register_user,
    verify_email,
    resend_verification_email,
)
from app.schemas.auth import RegisterRequest
from app.core.security import get_password_hash, verify_password

pytestmark = pytest.mark.asyncio


class TestAuthenticateUser:
    """Test cases for authenticate_user function."""

    async def test_authenticate_user_success(self, mock_database_session):
        """Test successful user authentication."""
        # Arrange
        from tests.unit.factories import MockDataFactory
        
        mock_user = MockDataFactory.create_mock_user(
            email="test@example.com",
            hashed_password=get_password_hash("TestPassword123!")
        )
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_database_session.execute.return_value = mock_result
        
        mock_request = MockDataFactory.create_mock_request()
        
        # Mock AccountLockService
        mock_lock_service = MockDataFactory.create_mock_account_lock_service()
        
        with patch('app.services.user.get_user_by_email', new_callable=AsyncMock) as mock_get_user:
            with patch('app.services.auth.AccountLockService', return_value=mock_lock_service):
                mock_get_user.return_value = mock_user
                
                # Act
                result = await authenticate_user(
                    mock_database_session,
                    "test@example.com",
                    "TestPassword123!",
                    mock_request
                )
                
                # Assert
                assert result is not None
                assert result.email == "test@example.com"
                mock_lock_service.reset_failed_attempts.assert_called_once_with(mock_user)

    async def test_authenticate_user_wrong_password(self, mock_database_session):
        """Test authentication with wrong password."""
        # Arrange
        from tests.unit.factories import MockDataFactory
        
        mock_user = MockDataFactory.create_mock_user(
            email="test@example.com",
            hashed_password=get_password_hash("CorrectPassword123!")
        )
        
        mock_request = MockDataFactory.create_mock_request()
        
        with patch('app.services.user.get_user_by_email', new_callable=AsyncMock) as mock_get_user:
            mock_get_user.return_value = mock_user
            
            # Act
            result = await authenticate_user(
                mock_database_session,
                "test@example.com",
                "WrongPassword123!",
                mock_request
            )
            
            # Assert
            assert result is None

    async def test_authenticate_user_not_found(self, mock_database_session):
        """Test authentication with non-existent user."""
        # Arrange
        from tests.unit.factories import MockDataFactory
        
        mock_request = MockDataFactory.create_mock_request()
        
        with patch('app.services.user.get_user_by_email', new_callable=AsyncMock) as mock_get_user:
            mock_get_user.return_value = None
            
            # Act
            result = await authenticate_user(
                mock_database_session,
                "nonexistent@example.com",
                "TestPassword123!",
                mock_request
            )
            
            # Assert
            assert result is None

    async def test_authenticate_user_account_locked(self, mock_database_session):
        """Test authentication with locked account."""
        # Arrange
        from tests.unit.factories import MockDataFactory
        
        mock_user = MockDataFactory.create_mock_user(
            email="test@example.com",
            hashed_password=get_password_hash("TestPassword123!")
        )
        
        mock_request = MockDataFactory.create_mock_request()
        
        # Mock AccountLockService to return locked account
        mock_lock_service = MockDataFactory.create_mock_account_lock_service()
        mock_lock_service.is_account_locked = AsyncMock(return_value=(True, "Too many failed attempts"))
        
        with patch('app.services.user.get_user_by_email', new_callable=AsyncMock) as mock_get_user:
            with patch('app.services.auth.AccountLockService', return_value=mock_lock_service):
                with patch('app.services.audit_log.create_audit_log', new_callable=AsyncMock):
                    mock_get_user.return_value = mock_user
                    
                    # Act
                    result = await authenticate_user(
                        mock_database_session,
                        "test@example.com",
                        "TestPassword123!",
                        mock_request
                    )
                    
                    # Assert
                    assert result is None
                    mock_lock_service.is_account_locked.assert_called_once_with(mock_user)

    async def test_authenticate_user_no_request(self, mock_database_session):
        """Test authentication without request object (no account lock checks)."""
        # Arrange
        from tests.unit.factories import MockDataFactory
        
        mock_user = MockDataFactory.create_mock_user(
            email="test@example.com",
            hashed_password=get_password_hash("TestPassword123!")
        )
        
        with patch('app.services.user.get_user_by_email', new_callable=AsyncMock) as mock_get_user:
            mock_get_user.return_value = mock_user
            
            # Act
            result = await authenticate_user(
                mock_database_session,
                "test@example.com",
                "TestPassword123!"
            )
            
            # Assert
            assert result is not None
            assert result.email == "test@example.com"


class TestGenerateEmailVerificationToken:
    """Test cases for generate_email_verification_token function."""

    def test_generate_token_returns_string(self):
        """Test that token generation returns a string."""
        token = generate_email_verification_token()
        assert isinstance(token, str)
        assert len(token) > 0

    def test_generate_token_unique(self):
        """Test that generated tokens are unique."""
        token1 = generate_email_verification_token()
        token2 = generate_email_verification_token()
        assert token1 != token2

    def test_generate_token_length(self):
        """Test that token has appropriate length."""
        token = generate_email_verification_token()
        # secrets.token_urlsafe(48) should produce a string of length ~64
        assert len(token) >= 60


class TestRegisterUser:
    """Test cases for register_user function."""

    async def test_register_user_success(self, mock_database_session):
        """Test successful user registration."""
        # Arrange
        from tests.unit.factories import MockDataFactory
        
        mock_user = MockDataFactory.create_mock_user(
            email="newuser@example.com",
            username="newuser"
        )
        
        register_data = MockDataFactory.create_mock_register_request(
            email="newuser@example.com",
            username="newuser"
        )
        
        mock_email_service = MockDataFactory.create_mock_email_service()
        
        with patch('app.services.user.get_user_by_email', new_callable=AsyncMock) as mock_get_email:
            with patch('app.services.user.get_user_by_username', new_callable=AsyncMock) as mock_get_username:
                with patch('app.services.user.create_user', new_callable=AsyncMock) as mock_create_user:
                    with patch('app.services.email.send_verification_email', new_callable=AsyncMock) as mock_send_email:
                        mock_get_email.return_value = None
                        mock_get_username.return_value = None
                        mock_create_user.return_value = mock_user
                        mock_send_email.return_value = True
                        
                        # Act
                        result = await register_user(mock_database_session, register_data)
                        
                        # Assert
                        assert result is not None
                        assert result.email == "newuser@example.com"
                        mock_create_user.assert_called_once()
                        mock_send_email.assert_called_once()

    async def test_register_user_duplicate_email(self, mock_database_session):
        """Test registration with duplicate email."""
        # Arrange
        from tests.unit.factories import MockDataFactory
        
        mock_existing_user = MockDataFactory.create_mock_user(email="existing@example.com")
        register_data = MockDataFactory.create_mock_register_request(email="existing@example.com")
        
        with patch('app.services.user.get_user_by_email', new_callable=AsyncMock) as mock_get_email:
            mock_get_email.return_value = mock_existing_user
            
            # Act & Assert
            with pytest.raises(ValueError, match="A user with this email already exists"):
                await register_user(mock_database_session, register_data)

    async def test_register_user_duplicate_username(self, mock_database_session):
        """Test registration with duplicate username."""
        # Arrange
        from tests.unit.factories import MockDataFactory
        
        mock_existing_user = MockDataFactory.create_mock_user(username="existinguser")
        register_data = MockDataFactory.create_mock_register_request(
            email="new@example.com",
            username="existinguser"
        )
        
        with patch('app.services.user.get_user_by_email', new_callable=AsyncMock) as mock_get_email:
            with patch('app.services.user.get_user_by_username', new_callable=AsyncMock) as mock_get_username:
                mock_get_email.return_value = None
                mock_get_username.return_value = mock_existing_user
                
                # Act & Assert
                with pytest.raises(ValueError, match="A user with this username already exists"):
                    await register_user(mock_database_session, register_data)

    async def test_register_user_no_username(self, mock_database_session):
        """Test registration without username (should skip username check)."""
        # Arrange
        from tests.unit.factories import MockDataFactory
        
        mock_user = MockDataFactory.create_mock_user(email="newuser@example.com", username=None)
        register_data = MockDataFactory.create_mock_register_request(
            email="newuser@example.com",
            username=None
        )
        
        with patch('app.services.user.get_user_by_email', new_callable=AsyncMock) as mock_get_email:
            with patch('app.services.user.create_user', new_callable=AsyncMock) as mock_create_user:
                with patch('app.services.email.send_verification_email', new_callable=AsyncMock):
                    mock_get_email.return_value = None
                    mock_create_user.return_value = mock_user
                    
                    # Act
                    result = await register_user(mock_database_session, register_data)
                    
                    # Assert
                    assert result is not None
                    mock_create_user.assert_called_once()


class TestVerifyEmail:
    """Test cases for verify_email function."""

    async def test_verify_email_success(self, mock_database_session):
        """Test successful email verification."""
        # Arrange
        from tests.unit.factories import MockDataFactory
        from app.models.user import User
        
        verification_token = "test_verification_token_123"
        mock_user = MockDataFactory.create_mock_user(
            email="test@example.com",
            is_email_verified=False
        )
        mock_user.email_verification_token = verification_token
        mock_user.created_at = datetime.utcnow() - timedelta(hours=1)
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_database_session.execute.return_value = mock_result
        
        # Act
        result = await verify_email(mock_database_session, verification_token)
        
        # Assert
        assert result is not None
        assert result.is_email_verified is True
        assert result.email_verification_token is None

    async def test_verify_email_invalid_token(self, mock_database_session):
        """Test email verification with invalid token."""
        # Arrange
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_database_session.execute.return_value = mock_result
        
        # Act & Assert
        with pytest.raises(ValueError, match="Invalid or expired verification token"):
            await verify_email(mock_database_session, "invalid_token")

    async def test_verify_email_already_verified(self, mock_database_session):
        """Test email verification when already verified."""
        # Arrange
        from tests.unit.factories import MockDataFactory
        
        verification_token = "test_verification_token_123"
        mock_user = MockDataFactory.create_mock_user(
            email="test@example.com",
            is_email_verified=True
        )
        mock_user.email_verification_token = verification_token
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_database_session.execute.return_value = mock_result
        
        # Act & Assert
        with pytest.raises(ValueError, match="Email is already verified"):
            await verify_email(mock_database_session, verification_token)

    async def test_verify_email_expired_token(self, mock_database_session):
        """Test email verification with expired token."""
        # Arrange
        from tests.unit.factories import MockDataFactory
        from app.core.config import settings
        
        verification_token = "test_verification_token_123"
        # Create user with token created 25 hours ago (assuming 24 hour expiry)
        mock_user = MockDataFactory.create_mock_user(
            email="test@example.com",
            is_email_verified=False
        )
        mock_user.email_verification_token = verification_token
        mock_user.created_at = datetime.utcnow() - timedelta(hours=25)
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_database_session.execute.return_value = mock_result
        
        # Mock settings to ensure we have the right expiry time
        with patch('app.services.auth.settings') as mock_settings:
            mock_settings.email_verification_token_expire_hours = 24
            
            # Act & Assert
            with pytest.raises(ValueError, match="Verification token has expired"):
                await verify_email(mock_database_session, verification_token)


class TestResendVerificationEmail:
    """Test cases for resend_verification_email function."""

    async def test_resend_verification_success(self, mock_database_session):
        """Test successful resend of verification email."""
        # Arrange
        from tests.unit.factories import MockDataFactory
        
        mock_user = MockDataFactory.create_mock_user(
            email="test@example.com",
            is_email_verified=False
        )
        
        with patch('app.services.user.get_user_by_email', new_callable=AsyncMock) as mock_get_user:
            with patch('app.services.email.send_verification_email', new_callable=AsyncMock) as mock_send_email:
                mock_get_user.return_value = mock_user
                mock_send_email.return_value = True
                
                # Act
                result = await resend_verification_email(mock_database_session, "test@example.com")
                
                # Assert
                assert result is not None
                assert result.email == "test@example.com"
                assert result.email_verification_token is not None
                mock_send_email.assert_called_once()

    async def test_resend_verification_user_not_found(self, mock_database_session):
        """Test resend verification with non-existent user."""
        # Arrange
        with patch('app.services.user.get_user_by_email', new_callable=AsyncMock) as mock_get_user:
            mock_get_user.return_value = None
            
            # Act & Assert
            with pytest.raises(ValueError, match="No user found with this email address"):
                await resend_verification_email(mock_database_session, "nonexistent@example.com")

    async def test_resend_verification_already_verified(self, mock_database_session):
        """Test resend verification when email already verified."""
        # Arrange
        from tests.unit.factories import MockDataFactory
        
        mock_user = MockDataFactory.create_mock_user(
            email="test@example.com",
            is_email_verified=True
        )
        
        with patch('app.services.user.get_user_by_email', new_callable=AsyncMock) as mock_get_user:
            mock_get_user.return_value = mock_user
            
            # Act & Assert
            with pytest.raises(ValueError, match="Email is already verified"):
                await resend_verification_email(mock_database_session, "test@example.com")
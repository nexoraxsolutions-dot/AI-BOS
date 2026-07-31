"""Tests for account lock functionality."""
import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock
from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.account_lock import AccountLockService, MAX_FAILED_LOGIN_ATTEMPTS, LOCK_DURATION_MINUTES
from app.models.user import User
from app.services.audit_log import create_audit_log


@pytest.fixture
def mock_db():
    """Create a mock database session."""
    db = AsyncMock(spec=AsyncSession)
    return db


@pytest.fixture
def mock_user():
    """Create a mock user."""
    user = MagicMock(spec=User)
    user.id = 1
    user.email = "test@example.com"
    user.failed_login_attempts = 0
    user.locked_until = None
    user.lock_reason = None
    return user


@pytest.fixture
def mock_request():
    """Create a mock request object."""
    request = MagicMock(spec=Request)
    request.client.host = "127.0.0.1"
    request.headers.get.return_value = "Test User Agent"
    return request


@pytest.mark.asyncio
async def test_record_failed_login_under_threshold(mock_db, mock_user, mock_request):
    """Test recording failed login when under threshold."""
    service = AccountLockService(mock_db)
    
    await service.record_failed_login(mock_user, mock_request)
    
    assert mock_user.failed_login_attempts == 1
    assert mock_user.locked_until is None
    assert mock_user.lock_reason is None
    mock_db.commit.assert_called_once()
    mock_db.refresh.assert_called_once_with(mock_user)


@pytest.mark.asyncio
async def test_record_failed_login_reaches_threshold(mock_db, mock_user, mock_request):
    """Test recording failed login when threshold is reached."""
    service = AccountLockService(mock_db)
    mock_user.failed_login_attempts = MAX_FAILED_LOGIN_ATTEMPTS - 1
    
    await service.record_failed_login(mock_user, mock_request)
    
    assert mock_user.failed_login_attempts == MAX_FAILED_LOGIN_ATTEMPTS
    assert mock_user.locked_until is not None
    assert mock_user.lock_reason is not None
    assert "failed login attempts" in mock_user.lock_reason
    assert mock_db.commit.call_count >= 1
    # refresh is called twice: once for audit log, once for user
    assert mock_db.refresh.call_count >= 1


@pytest.mark.asyncio
async def test_reset_failed_attempts(mock_db, mock_user):
    """Test resetting failed login attempts."""
    service = AccountLockService(mock_db)
    mock_user.failed_login_attempts = 3
    mock_user.locked_until = datetime.utcnow()
    mock_user.lock_reason = "Account locked"
    
    await service.reset_failed_attempts(mock_user)
    
    assert mock_user.failed_login_attempts == 0
    assert mock_user.locked_until is None
    assert mock_user.lock_reason is None
    mock_db.commit.assert_called_once()
    mock_db.refresh.assert_called_once_with(mock_user)


@pytest.mark.asyncio
async def test_is_account_locked_not_locked(mock_db, mock_user):
    """Test checking if account is locked when it's not locked."""
    service = AccountLockService(mock_db)
    
    is_locked, reason = await service.is_account_locked(mock_user)
    
    assert is_locked is False
    assert reason is None


@pytest.mark.asyncio
async def test_is_account_locked_expired(mock_db, mock_user):
    """Test checking if account is locked when lock has expired."""
    service = AccountLockService(mock_db)
    mock_user.locked_until = datetime.utcnow() - timedelta(minutes=1)
    
    is_locked, reason = await service.is_account_locked(mock_user)
    
    assert is_locked is False
    assert reason is None
    # Should auto-unlock
    assert mock_user.failed_login_attempts == 0
    assert mock_user.locked_until is None


@pytest.mark.asyncio
async def test_is_account_locked_active(mock_db, mock_user):
    """Test checking if account is locked when lock is active."""
    service = AccountLockService(mock_db)
    mock_user.locked_until = datetime.utcnow() + timedelta(minutes=30)
    mock_user.lock_reason = "Too many failed attempts"
    
    is_locked, reason = await service.is_account_locked(mock_user)
    
    assert is_locked is True
    assert reason == "Too many failed attempts"


@pytest.mark.asyncio
async def test_unlock_account_success(mock_db, mock_user, mock_request):
    """Test successfully unlocking an account."""
    service = AccountLockService(mock_db)
    mock_user.locked_until = datetime.utcnow() + timedelta(minutes=30)
    mock_user.lock_reason = "Account locked"
    
    # Mock the database query
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_user
    mock_db.execute.return_value = mock_result
    
    unlocked_user = await service.unlock_account(1, mock_request, unlocked_by=2)
    
    assert unlocked_user.id == 1
    assert mock_user.failed_login_attempts == 0
    assert mock_user.locked_until is None
    assert mock_user.lock_reason is None
    assert mock_db.commit.call_count >= 1
    # refresh is called twice: once for audit log, once for user
    assert mock_db.refresh.call_count >= 1


@pytest.mark.asyncio
async def test_unlock_account_not_found(mock_db, mock_request):
    """Test unlocking an account that doesn't exist."""
    service = AccountLockService(mock_db)
    
    # Mock the database query
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db.execute.return_value = mock_result
    
    with pytest.raises(ValueError, match="User not found"):
        await service.unlock_account(999, mock_request)


@pytest.mark.asyncio
async def test_unlock_account_not_locked(mock_db, mock_user, mock_request):
    """Test unlocking an account that is not locked."""
    service = AccountLockService(mock_db)
    mock_user.locked_until = None
    
    # Mock the database query
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_user
    mock_db.execute.return_value = mock_result
    
    with pytest.raises(ValueError, match="Account is not locked"):
        await service.unlock_account(1, mock_request)


@pytest.mark.asyncio
async def test_get_locked_accounts(mock_db, mock_user):
    """Test getting list of locked accounts."""
    service = AccountLockService(mock_db)
    now = datetime.utcnow()
    mock_user.locked_until = now + timedelta(minutes=30)
    
    # Mock the database query
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [mock_user]
    mock_db.execute.return_value = mock_result
    
    locked_accounts = await service.get_locked_accounts(skip=0, limit=20)
    
    assert len(locked_accounts) == 1
    assert locked_accounts[0].id == 1
    mock_db.execute.assert_called_once()
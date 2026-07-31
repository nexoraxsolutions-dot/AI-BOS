"""Integration tests for account lock functionality."""
import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from app.core.security import get_password_hash
from app.models.user import User
from app.services.audit_log import create_audit_log


@pytest.fixture
async def test_user(db: AsyncSession):
    """Create a test user."""
    user = User(
        email="test@example.com",
        username="testuser",
        hashed_password=get_password_hash("TestPassword123!"),
        full_name="Test User",
        is_active=True,
        is_email_verified=True,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@pytest.mark.asyncio
async def test_login_with_invalid_password_records_failed_attempt(client: TestClient, test_user: User):
    """Test that login with invalid password records failed attempt."""
    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": test_user.email,
            "password": "WrongPassword123!",
        }
    )
    
    assert response.status_code == 401
    
    # Verify failed attempt was recorded
    await db.get(test_user)  # Refresh user
    assert test_user.failed_login_attempts == 1


@pytest.mark.asyncio
async def test_account_locks_after_max_failed_attempts(client: TestClient, test_user: User):
    """Test that account locks after maximum failed login attempts."""
    # Make MAX_FAILED_LOGIN_ATTEMPTS failed login attempts
    for i in range(5):
        response = client.post(
            "/api/v1/auth/login",
            data={
                "username": test_user.email,
                "password": "WrongPassword123!",
            }
        )
        assert response.status_code == 401
    
    # Verify account is locked
    await db.get(test_user)  # Refresh user
    assert test_user.failed_login_attempts == 5
    assert test_user.locked_until is not None
    assert test_user.lock_reason is not None


@pytest.mark.asyncio
async def test_login_fails_when_account_is_locked(client: TestClient, test_user: User):
    """Test that login fails when account is locked."""
    # Lock the account
    test_user.failed_login_attempts = 5
    test_user.locked_until = datetime.utcnow() + timedelta(minutes=30)
    test_user.lock_reason = "Account locked due to 5 failed login attempts"
    await db.commit()
    await db.refresh(test_user)
    
    # Try to login with correct password
    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": test_user.email,
            "password": "TestPassword123!",
        }
    )
    
    assert response.status_code == 401
    assert "Incorrect username or password" in response.json()["detail"]


@pytest.mark.asyncio
async def test_successful_login_resets_failed_attempts(client: TestClient, test_user: User):
    """Test that successful login resets failed login attempts."""
    # Record some failed attempts
    test_user.failed_login_attempts = 2
    await db.commit()
    
    # Login successfully
    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": test_user.email,
            "password": "TestPassword123!",
        }
    )
    
    assert response.status_code == 200
    assert "access_token" in response.json()
    
    # Verify failed attempts were reset
    await db.get(test_user)  # Refresh user
    assert test_user.failed_login_attempts == 0
    assert test_user.locked_until is None
    assert test_user.lock_reason is None


@pytest.mark.asyncio
async def test_account_unlock_endpoint(client: TestClient, test_user: User, admin_token: str):
    """Test admin can unlock locked accounts."""
    # Lock the account
    test_user.failed_login_attempts = 5
    test_user.locked_until = datetime.utcnow() + timedelta(minutes=30)
    test_user.lock_reason = "Account locked"
    await db.commit()
    await db.refresh(test_user)
    
    # Unlock the account
    response = client.post(
        f"/api/v1/account-lock/{test_user.id}/unlock",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    assert response.status_code == 200
    assert response.json()["id"] == test_user.id
    
    # Verify account is unlocked
    await db.get(test_user)  # Refresh user
    assert test_user.failed_login_attempts == 0
    assert test_user.locked_until is None
    assert test_user.lock_reason is None


@pytest.mark.asyncio
async def test_get_locked_accounts_endpoint(client: TestClient, test_user: User, admin_token: str):
    """Test admin can view locked accounts."""
    # Lock the account
    test_user.failed_login_attempts = 5
    test_user.locked_until = datetime.utcnow() + timedelta(minutes=30)
    test_user.lock_reason = "Account locked"
    await db.commit()
    
    # Get locked accounts
    response = client.get(
        "/api/v1/account-lock/locked",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    assert response.status_code == 200
    accounts = response.json()
    assert len(accounts) > 0
    assert any(account["id"] == test_user.id for account in accounts)


@pytest.mark.asyncio
async def test_get_my_account_lock_status(client: TestClient, test_user: User):
    """Test user can view their own account lock status."""
    # Lock the account
    test_user.failed_login_attempts = 5
    test_user.locked_until = datetime.utcnow() + timedelta(minutes=30)
    test_user.lock_reason = "Account locked"
    await db.commit()
    
    # Login to get token
    login_response = client.post(
        "/api/v1/auth/login",
        data={
            "username": test_user.email,
            "password": "TestPassword123!",
        }
    )
    # This will fail because account is locked, but we need to test the status endpoint
    # So we'll create a token manually for the test
    from app.core.token import create_access_token
    token = create_access_token(data={"sub": test_user.email})
    
    # Get account lock status
    response = client.get(
        "/api/v1/account-lock/me/status",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    status = response.json()
    assert status["is_locked"] is True
    assert status["reason"] == "Account locked"
    assert status["failed_attempts"] == 5
    assert status["locked_until"] is not None


@pytest.mark.asyncio
async def test_account_auto_unlock_after_expiration(client: TestClient, test_user: User):
    """Test that account is automatically unlocked after lock expiration."""
    # Lock the account with expired lock
    test_user.failed_login_attempts = 5
    test_user.locked_until = datetime.utcnow() - timedelta(minutes=1)  # Expired
    test_user.lock_reason = "Account locked"
    await db.commit()
    
    # Try to login
    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": test_user.email,
            "password": "TestPassword123!",
        }
    )
    
    # Should succeed because lock expired
    assert response.status_code == 200
    
    # Verify account was auto-unlocked
    await db.get(test_user)  # Refresh user
    assert test_user.failed_login_attempts == 0
    assert test_user.locked_until is None
    assert test_user.lock_reason is None


@pytest.mark.asyncio
async def test_audit_logs_for_account_lock_events(client: TestClient, test_user: User, admin_token: str):
    """Test that account lock events are logged in audit log."""
    # Lock the account
    for i in range(5):
        client.post(
            "/api/v1/auth/login",
            data={
                "username": test_user.email,
                "password": "WrongPassword123!",
            }
        )
    
    # Check audit log for account lock event
    response = client.get(
        "/api/v1/audit-logs/",
        params={"action": "account_locked", "resource_type": "user", "resource_id": test_user.id},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    assert response.status_code == 200
    logs = response.json()["items"]
    assert len(logs) > 0
    assert logs[0]["action"] == "account_locked"
    assert logs[0]["resource_id"] == test_user.id
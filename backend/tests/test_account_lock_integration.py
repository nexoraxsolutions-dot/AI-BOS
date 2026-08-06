"""Integration tests for account lock API endpoints."""
import pytest
from datetime import datetime, timedelta
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User

pytestmark = pytest.mark.asyncio


class TestAccountLockEndpoints:
    """Integration tests for account lock endpoints using shared fixtures."""

    async def test_login_with_invalid_password_records_failed_attempt(
        self, client: AsyncClient, db_session: AsyncSession, test_user: User
    ):
        """Test that login with invalid password records failed attempt."""
        response = await client.post(
            "/api/v1/auth/login",
            data={
                "username": test_user.email,
                "password": "WrongPassword123!",
            }
        )

        assert response.status_code == 401

        # Verify failed attempt was recorded
        await db_session.refresh(test_user)
        assert test_user.failed_login_attempts == 1

    async def test_account_locks_after_max_failed_attempts(
        self, client: AsyncClient, db_session: AsyncSession, test_user: User
    ):
        """Test that account locks after maximum failed login attempts."""
        # Make 5 failed login attempts
        for i in range(5):
            response = await client.post(
                "/api/v1/auth/login",
                data={
                    "username": test_user.email,
                    "password": "WrongPassword123!",
                }
            )
            assert response.status_code == 401

        # Verify account is locked
        await db_session.refresh(test_user)
        assert test_user.failed_login_attempts == 5
        assert test_user.locked_until is not None
        assert test_user.lock_reason is not None

    async def test_login_fails_when_account_is_locked(
        self, client: AsyncClient, db_session: AsyncSession, test_user: User
    ):
        """Test that login fails when account is locked."""
        # Lock the account
        test_user.failed_login_attempts = 5
        test_user.locked_until = datetime.utcnow() + timedelta(minutes=30)
        test_user.lock_reason = "Account locked due to 5 failed login attempts"
        await db_session.commit()
        await db_session.refresh(test_user)

        # Try to login with correct password
        response = await client.post(
            "/api/v1/auth/login",
            data={
                "username": test_user.email,
                "password": "TestPassword123!",
            }
        )

        assert response.status_code == 401
        assert "Incorrect username or password" in response.json()["detail"]

    async def test_successful_login_resets_failed_attempts(
        self, client: AsyncClient, db_session: AsyncSession, test_user: User
    ):
        """Test that successful login resets failed login attempts."""
        # Record some failed attempts
        test_user.failed_login_attempts = 2
        await db_session.commit()

        # Login successfully
        response = await client.post(
            "/api/v1/auth/login",
            data={
                "username": test_user.email,
                "password": "TestPassword123!",
            }
        )

        assert response.status_code == 200
        assert "access_token" in response.json()

        # Verify failed attempts were reset
        await db_session.refresh(test_user)
        assert test_user.failed_login_attempts == 0
        assert test_user.locked_until is None
        assert test_user.lock_reason is None

    async def test_account_unlock_endpoint(
        self, client: AsyncClient, db_session: AsyncSession, test_user: User, admin_token_headers: dict
    ):
        """Test admin can unlock locked accounts."""
        # Lock the account
        test_user.failed_login_attempts = 5
        test_user.locked_until = datetime.utcnow() + timedelta(minutes=30)
        test_user.lock_reason = "Account locked"
        await db_session.commit()
        await db_session.refresh(test_user)

        # Unlock the account
        response = await client.post(
            f"/api/v1/account-lock/{test_user.id}/unlock",
            headers=admin_token_headers
        )

        assert response.status_code == 200
        assert response.json()["id"] == test_user.id

        # Verify account is unlocked
        await db_session.refresh(test_user)
        assert test_user.failed_login_attempts == 0
        assert test_user.locked_until is None
        assert test_user.lock_reason is None

    async def test_get_locked_accounts_endpoint(
        self, client: AsyncClient, db_session: AsyncSession, test_user: User, admin_token_headers: dict
    ):
        """Test admin can view locked accounts."""
        # Lock the account
        test_user.failed_login_attempts = 5
        test_user.locked_until = datetime.utcnow() + timedelta(minutes=30)
        test_user.lock_reason = "Account locked"
        await db_session.commit()

        # Get locked accounts
        response = await client.get(
            "/api/v1/account-lock/locked",
            headers=admin_token_headers
        )

        assert response.status_code == 200
        accounts = response.json()
        assert len(accounts) > 0
        assert any(account["id"] == test_user.id for account in accounts)

    async def test_get_my_account_lock_status(
        self, client: AsyncClient, db_session: AsyncSession, test_user: User
    ):
        """Test user can view their own account lock status."""
        # Lock the account
        test_user.failed_login_attempts = 5
        test_user.locked_until = datetime.utcnow() + timedelta(minutes=30)
        test_user.lock_reason = "Account locked"
        await db_session.commit()

        # Get account lock status
        from app.core.security import create_access_token
        token = create_access_token(data={"sub": test_user.email})
        response = await client.get(
            "/api/v1/account-lock/me/status",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        status = response.json()
        assert status["is_locked"] is True
        assert status["reason"] == "Account locked"
        assert status["failed_attempts"] == 5
        assert status["locked_until"] is not None

    async def test_account_auto_unlock_after_expiration(
        self, client: AsyncClient, db_session: AsyncSession, test_user: User
    ):
        """Test that account is automatically unlocked after lock expiration."""
        # Lock the account with expired lock
        test_user.failed_login_attempts = 5
        test_user.locked_until = datetime.utcnow() - timedelta(minutes=1)  # Expired
        test_user.lock_reason = "Account locked"
        await db_session.commit()

        # Try to login
        response = await client.post(
            "/api/v1/auth/login",
            data={
                "username": test_user.email,
                "password": "TestPassword123!",
            }
        )

        # Should succeed because lock expired
        assert response.status_code == 200

        # Verify account was auto-unlocked
        await db_session.refresh(test_user)
        assert test_user.failed_login_attempts == 0
        assert test_user.locked_until is None
        assert test_user.lock_reason is None

    async def test_audit_logs_for_account_lock_events(
        self, client: AsyncClient, db_session: AsyncSession, test_user: User, admin_token_headers: dict
    ):
        """Test that account lock events are logged in audit log."""
        # Lock the account
        for i in range(5):
            await client.post(
                "/api/v1/auth/login",
                data={
                    "username": test_user.email,
                    "password": "WrongPassword123!",
                }
            )

        # Check audit log for account lock event
        response = await client.get(
            "/api/v1/audit-logs/",
            params={"action": "account_locked", "resource_type": "user", "resource_id": test_user.id},
            headers=admin_token_headers
        )

        assert response.status_code == 200
        logs = response.json()["items"]
        assert len(logs) > 0
        assert logs[0]["action"] == "account_locked"
        assert logs[0]["resource_id"] == test_user.id
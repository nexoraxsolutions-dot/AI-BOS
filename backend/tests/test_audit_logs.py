import os
import sys
import pytest
from fastapi import status

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


def test_audit_log_model():
    """Test audit log model fields."""
    from app.models.audit_log import AuditLog

    log = AuditLog(
        action="login",
        resource_type="auth",
        resource_id=1,
        user_id=1,
        ip_address="127.0.0.1",
        user_agent="TestAgent/1.0",
        details={"method": "password"},
    )
    assert log.action == "login"
    assert log.resource_type == "auth"
    assert log.resource_id == 1
    assert log.user_id == 1
    assert log.ip_address == "127.0.0.1"
    assert log.user_agent == "TestAgent/1.0"


def test_audit_log_schema():
    """Test audit log schema validation."""
    from app.schemas.audit_log import AuditLogBase, AuditLogCreate, AuditLogOut, AuditLogListResponse

    # Base schema
    base = AuditLogBase(action="login", resource_type="auth")
    assert base.action == "login"
    assert base.resource_type == "auth"

    # Create schema
    create = AuditLogCreate(action="logout", resource_type="auth", user_id=1)
    assert create.action == "logout"
    assert create.user_id == 1

    # List response
    response = AuditLogListResponse(items=[], total=0, page=1, page_size=50)
    assert response.total == 0
    assert response.page == 1


def test_audit_log_service_functions():
    """Test audit log service functions exist."""
    from app.services.audit_log import (
        create_audit_log,
        get_audit_logs,
        get_audit_log,
        count_audit_logs,
        delete_audit_logs,
    )
    assert callable(create_audit_log)
    assert callable(get_audit_logs)
    assert callable(get_audit_log)
    assert callable(count_audit_logs)
    assert callable(delete_audit_logs)


@pytest.mark.asyncio
async def test_create_audit_log(db_session):
    """Test creating an audit log entry."""
    from app.services.audit_log import create_audit_log

    log = await create_audit_log(
        db_session,
        action="login",
        resource_type="auth",
        resource_id=1,
        user_id=1,
        ip_address="127.0.0.1",
        details={"method": "password"},
    )
    assert log.id is not None
    assert log.action == "login"
    assert log.resource_type == "auth"
    assert log.user_id == 1


@pytest.mark.asyncio
async def test_get_audit_logs(client, admin_token_headers, db_session):
    """Test listing audit logs as admin."""
    from app.services.audit_log import create_audit_log

    # Create an audit log first
    await create_audit_log(db_session, action="login", resource_type="auth", user_id=1)

    response = await client.get("/api/v1/audit-logs/", headers=admin_token_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert "page" in data
    assert "page_size" in data


@pytest.mark.asyncio
async def test_get_my_audit_logs(client, user_token_headers, db_session):
    """Test getting current user's audit logs."""
    from app.services.audit_log import create_audit_log

    # Create an audit log for the test user
    await create_audit_log(db_session, action="login", resource_type="auth", user_id=1)

    response = await client.get("/api/v1/audit-logs/my-logs/", headers=user_token_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "items" in data
    assert "total" in data


@pytest.mark.asyncio
async def test_audit_logs_unauthorized(client, user_token_headers):
    """Test that non-superuser cannot list all audit logs."""
    response = await client.get("/api/v1/audit-logs/", headers=user_token_headers)
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.asyncio
async def test_audit_log_not_found(client, admin_token_headers):
    """Test getting non-existent audit log returns 404."""
    response = await client.get("/api/v1/audit-logs/99999", headers=admin_token_headers)
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_audit_log_filter_by_action(client, admin_token_headers, db_session):
    """Test filtering audit logs by action."""
    from app.services.audit_log import create_audit_log

    await create_audit_log(db_session, action="login", resource_type="auth")
    await create_audit_log(db_session, action="logout", resource_type="auth")

    response = await client.get(
        "/api/v1/audit-logs/?action=login",
        headers=admin_token_headers,
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert all(log["action"] == "login" for log in data["items"])


@pytest.mark.asyncio
async def test_audit_log_filter_by_resource_type(client, admin_token_headers, db_session):
    """Test filtering audit logs by resource type."""
    from app.services.audit_log import create_audit_log

    await create_audit_log(db_session, action="login", resource_type="auth")
    await create_audit_log(db_session, action="create", resource_type="user")

    response = await client.get(
        "/api/v1/audit-logs/?resource_type=user",
        headers=admin_token_headers,
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert all(log["resource_type"] == "user" for log in data["items"])


@pytest.mark.asyncio
async def test_audit_log_filter_by_user_id(client, admin_token_headers, db_session, test_user):
    """Test filtering audit logs by user ID."""
    from app.services.audit_log import create_audit_log

    await create_audit_log(db_session, action="login", resource_type="auth", user_id=test_user.id)

    response = await client.get(
        f"/api/v1/audit-logs/?user_id={test_user.id}",
        headers=admin_token_headers,
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert all(log["user_id"] == test_user.id for log in data["items"])


@pytest.mark.asyncio
async def test_audit_logs_require_auth(client):
    """Test that audit logs require authentication."""
    response = await client.get("/api/v1/audit-logs/")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.asyncio
async def test_audit_log_service_create_and_get(db_session):
    """Test audit log service create and get operations."""
    from app.services.audit_log import create_audit_log, get_audit_log, get_audit_logs

    # Create
    log = await create_audit_log(
        db_session,
        action="create",
        resource_type="user",
        resource_id=1,
        user_id=1,
    )
    assert log.id is not None

    # Get by ID
    fetched = await get_audit_log(db_session, log.id)
    assert fetched is not None
    assert fetched.action == "create"

    # Get list
    logs = await get_audit_logs(db_session, limit=10)
    assert len(logs) >= 1

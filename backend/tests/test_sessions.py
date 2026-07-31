import os
import sys
import pytest
from datetime import timedelta
from fastapi import status

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


def test_session_model_fields():
    """Test that UserSession model has the correct fields."""
    from app.models.session import UserSession
    
    fields = [c.name for c in UserSession.__table__.columns]
    assert "id" in fields
    assert "user_id" in fields
    assert "session_token" in fields
    assert "ip_address" in fields
    assert "user_agent" in fields
    assert "device_name" in fields
    assert "device_type" in fields
    assert "browser" in fields
    assert "os" in fields
    assert "is_active" in fields
    assert "last_activity_at" in fields
    assert "expires_at" in fields
    assert "created_at" in fields
    assert "terminated_at" in fields


def test_session_schemas():
    """Test Session Pydantic schemas."""
    from app.schemas.session import (
        SessionOut, SessionListResponse, SessionTerminateRequest,
        SessionTerminateResponse, SessionCleanupResponse
    )
    from datetime import datetime
    
    session_out = SessionOut(
        id=1,
        user_id=1,
        session_token="test_session_token",
        ip_address="192.168.1.1",
        user_agent="test-agent",
        device_name="Test Device",
        device_type="desktop",
        browser="Chrome",
        os="Windows",
        is_active=True,
        expires_at=datetime.utcnow() + timedelta(hours=1),
    )
    assert session_out.id == 1
    assert session_out.user_id == 1
    assert session_out.device_name == "Test Device"
    assert session_out.is_active is True
    
    list_response = SessionListResponse(items=[session_out], total=1, page=1, page_size=10)
    assert len(list_response.items) == 1
    assert list_response.total == 1
    
    terminate_req = SessionTerminateRequest(session_id=1)
    assert terminate_req.session_id == 1
    
    terminate_resp = SessionTerminateResponse(message="Terminated", session_id=1, terminated=True)
    assert terminate_resp.terminated is True
    
    cleanup_resp = SessionCleanupResponse(message="Cleaned up", deleted_count=5)
    assert cleanup_resp.deleted_count == 5


def test_generate_session_token():
    """Test session token generation."""
    from app.services.session import generate_session_token
    
    token1 = generate_session_token()
    token2 = generate_session_token()
    
    assert isinstance(token1, str)
    assert len(token1) > 20  # URL-safe base64 encoded 32 bytes
    assert token1 != token2  # Should be unique


@pytest.mark.asyncio
async def test_create_and_get_session(db_session):
    """Test creating and retrieving a session."""
    from app.services.session import create_session, get_session_by_token
    
    # Create a session
    session = await create_session(
        db=db_session,
        user_id=1,
        ip_address="192.168.1.1",
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    )
    
    assert session.id is not None
    assert session.user_id == 1
    assert session.ip_address == "192.168.1.1"
    assert session.is_active is True
    assert session.device_name is not None
    assert session.browser is not None
    assert session.os is not None
    
    # Retrieve by token
    retrieved = await get_session_by_token(db_session, session.session_token)
    assert retrieved is not None
    assert retrieved.id == session.id
    assert retrieved.user_id == 1


@pytest.mark.asyncio
async def test_get_session_by_id(db_session):
    """Test getting a session by ID."""
    from app.services.session import create_session, get_session_by_id
    
    session = await create_session(
        db=db_session,
        user_id=1,
        ip_address="192.168.1.1",
    )
    
    # Get by ID with correct user
    retrieved = await get_session_by_id(db_session, session.id, 1)
    assert retrieved is not None
    assert retrieved.id == session.id
    
    # Get by ID with wrong user
    retrieved_wrong = await get_session_by_id(db_session, session.id, 999)
    assert retrieved_wrong is None


@pytest.mark.asyncio
async def test_terminate_session(db_session):
    """Test terminating a session."""
    from app.services.session import create_session, terminate_session
    
    session = await create_session(
        db=db_session,
        user_id=1,
        ip_address="192.168.1.1",
    )
    
    assert session.is_active is True
    
    # Terminate the session
    terminated = await terminate_session(db_session, session.id, 1)
    assert terminated is not None
    assert terminated.is_active is False
    assert terminated.terminated_at is not None


@pytest.mark.asyncio
async def test_terminate_user_sessions(db_session):
    """Test terminating all sessions for a user."""
    from app.services.session import create_session, terminate_user_sessions, get_user_sessions
    
    # Create multiple sessions
    session1 = await create_session(db=db_session, user_id=1, ip_address="192.168.1.1")
    session2 = await create_session(db=db_session, user_id=1, ip_address="192.168.1.2")
    session3 = await create_session(db=db_session, user_id=2, ip_address="192.168.1.3")
    
    # Terminate all sessions for user 1
    count = await terminate_user_sessions(db_session, user_id=1)
    assert count == 2
    
    # Verify user 1's sessions are terminated
    sessions_user1, _ = await get_user_sessions(db_session, user_id=1, include_inactive=True)
    assert all(not s.is_active for s in sessions_user1)
    
    # Verify user 2's session is still active
    sessions_user2, _ = await get_user_sessions(db_session, user_id=2, include_inactive=True)
    assert all(s.is_active for s in sessions_user2)


@pytest.mark.asyncio
async def test_get_user_sessions(db_session):
    """Test getting user sessions with pagination."""
    from app.services.session import create_session, get_user_sessions
    
    # Create multiple sessions
    for i in range(5):
        await create_session(db=db_session, user_id=1, ip_address=f"192.168.1.{i}")
    
    # Get all sessions
    sessions, total = await get_user_sessions(db_session, user_id=1, include_inactive=True)
    assert total == 5
    assert len(sessions) == 5
    
    # Get with pagination
    sessions_page, total = await get_user_sessions(
        db_session, user_id=1, skip=2, limit=2, include_inactive=True
    )
    assert len(sessions_page) == 2
    assert total == 5


@pytest.mark.asyncio
async def test_cleanup_expired_sessions(db_session):
    """Test cleaning up expired sessions."""
    from app.services.session import create_session, cleanup_expired_sessions, get_user_sessions
    
    # Create a session that expires immediately
    session = await create_session(
        db=db_session,
        user_id=1,
        ip_address="192.168.1.1",
        expires_delta=timedelta(seconds=-1)  # Already expired
    )
    
    # Create a valid session
    valid_session = await create_session(
        db=db_session,
        user_id=1,
        ip_address="192.168.1.2",
        expires_delta=timedelta(hours=1)
    )
    
    # Cleanup expired sessions
    deleted_count = await cleanup_expired_sessions(db_session)
    assert deleted_count == 1
    
    # Verify only valid session remains
    sessions, _ = await get_user_sessions(db_session, user_id=1, include_inactive=True)
    assert len(sessions) == 1
    assert sessions[0].id == valid_session.id


@pytest.mark.asyncio
async def test_get_session_stats(db_session):
    """Test getting session statistics."""
    from app.services.session import create_session, terminate_session, get_session_stats
    
    # Create sessions
    session1 = await create_session(db=db_session, user_id=1, ip_address="192.168.1.1")
    session2 = await create_session(db=db_session, user_id=1, ip_address="192.168.1.2")
    session3 = await create_session(db=db_session, user_id=1, ip_address="192.168.1.3")
    
    # Terminate one session
    await terminate_session(db_session, session2.id, 1)
    
    # Get stats
    stats = await get_session_stats(db_session, user_id=1)
    
    assert stats["total_sessions"] == 3
    assert stats["active_sessions"] == 2
    assert stats["inactive_sessions"] == 1
    assert "device_type_breakdown" in stats


@pytest.mark.asyncio
async def test_session_endpoints(client, test_user, user_token_headers, db_session):
    """Test session API endpoints."""
    from app.services.session import create_session
    
    # Create a test session
    session = await create_session(
        db=db_session,
        user_id=test_user.id,
        ip_address="192.168.1.1",
    )
    
    # Test list sessions
    response = await client.get("/api/v1/sessions/", headers=user_token_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "items" in data
    assert "total" in data
    
    # Test get session stats
    response = await client.get("/api/v1/sessions/stats", headers=user_token_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "total_sessions" in data
    assert "active_sessions" in data
    
    # Test get specific session
    response = await client.get(f"/api/v1/sessions/{session.id}", headers=user_token_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == session.id
    
    # Test terminate session
    response = await client.post(
        "/api/v1/sessions/terminate",
        headers=user_token_headers,
        json={"session_id": session.id}
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["terminated"] is True
    
    # Test terminate all sessions
    response = await client.post("/api/v1/sessions/terminate-all", headers=user_token_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "terminated_count" in data


@pytest.mark.asyncio
async def test_session_cleanup_endpoint(client, user_token_headers, admin_user):
    """Test session cleanup endpoint (superuser only)."""
    # Test cleanup as regular user (should fail)
    response = await client.post("/api/v1/sessions/cleanup", headers=user_token_headers)
    assert response.status_code == status.HTTP_403_FORBIDDEN
    
    # Test cleanup as superuser (should succeed)
    admin_token_headers = await get_auth_headers(client, admin_user.email, "SecurePass123!")
    response = await client.post("/api/v1/sessions/cleanup", headers=admin_token_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "deleted_count" in data


@pytest.mark.asyncio
async def test_session_ownership(client, test_user, user_token_headers, db_session):
    """Test that users can only access their own sessions."""
    from app.services.session import create_session
    from app.models.user import User
    from app.core.security import get_password_hash
    
    # Create another user
    other_user = User(
        email="other@example.com",
        hashed_password=get_password_hash("TestPassword123!"),
        full_name="Other User",
        is_active=True,
        is_superuser=False,
        company_id=test_user.company_id,
    )
    db_session.add(other_user)
    await db_session.commit()
    await db_session.refresh(other_user)
    
    # Create a session for other user
    other_session = await create_session(
        db=db_session,
        user_id=other_user.id,
        ip_address="192.168.1.1",
    )
    
    # Try to access other user's session
    response = await client.get(f"/api/v1/sessions/{other_session.id}", headers=user_token_headers)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    
    # Try to terminate other user's session
    response = await client.post(
        "/api/v1/sessions/terminate",
        headers=user_token_headers,
        json={"session_id": other_session.id}
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


async def get_auth_headers(client, email: str, password: str):
    """Helper to get authentication headers."""
    response = await client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": password}
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
import os
import sys
import pytest
from datetime import datetime, timedelta
from fastapi import status

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


def test_log_entry_model():
    """Test log entry model fields."""
    from app.models.logging_history import LogEntry

    entry = LogEntry(
        level="ERROR",
        logger_name="ai_bos",
        message="Test error message",
        module="test_module",
        func_name="test_func",
        line_no=42,
        pathname="/app/test_module.py",
        thread_name="MainThread",
        process="1234",
        user_id=1,
        ip_address="127.0.0.1",
        user_agent="TestAgent/1.0",
        extra_data={"key": "value"},
    )
    assert entry.level == "ERROR"
    assert entry.logger_name == "ai_bos"
    assert entry.message == "Test error message"
    assert entry.module == "test_module"
    assert entry.func_name == "test_func"
    assert entry.line_no == 42
    assert entry.user_id == 1
    assert entry.ip_address == "127.0.0.1"


def test_log_entry_schema():
    """Test log entry schema validation."""
    from app.schemas.logging_history import (
        LogEntryBase,
        LogEntryCreate,
        LogEntryOut,
        LogEntryListResponse,
        LogStats,
    )

    # Base schema
    base = LogEntryBase(level="INFO", logger_name="ai_bos", message="Test message")
    assert base.level == "INFO"
    assert base.logger_name == "ai_bos"

    # Level validation - uppercase
    base_upper = LogEntryBase(level="info", logger_name="ai_bos", message="Test")
    assert base_upper.level == "INFO"

    # Invalid level
    with pytest.raises(ValueError):
        LogEntryBase(level="INVALID", logger_name="ai_bos", message="Test")

    # Create schema
    create = LogEntryCreate(
        level="WARNING",
        logger_name="ai_bos",
        message="Warning message",
        user_id=1,
    )
    assert create.level == "WARNING"
    assert create.user_id == 1

    # List response
    response = LogEntryListResponse(items=[], total=0, page=1, page_size=50)
    assert response.total == 0
    assert response.page == 1

    # Stats
    stats = LogStats(
        total_entries=100,
        by_level={"INFO": 80, "ERROR": 20},
        top_loggers=[{"logger_name": "ai_bos", "count": 100}],
    )
    assert stats.total_entries == 100
    assert stats.by_level["INFO"] == 80


def test_log_entry_service_functions_exist():
    """Test that logging history service functions exist."""
    from app.services.logging_history import (
        create_log_entry,
        get_log_entries,
        get_log_entry,
        count_log_entries,
        get_log_stats,
        cleanup_old_logs,
    )
    assert callable(create_log_entry)
    assert callable(get_log_entries)
    assert callable(get_log_entry)
    assert callable(count_log_entries)
    assert callable(get_log_stats)
    assert callable(cleanup_old_logs)


@pytest.mark.asyncio
async def test_create_log_entry(db_session):
    """Test creating a log entry."""
    from app.services.logging_history import create_log_entry

    entry = await create_log_entry(
        db_session,
        level="ERROR",
        logger_name="ai_bos",
        message="Test error message",
        module="test_module",
        user_id=1,
    )
    assert entry.id is not None
    assert entry.level == "ERROR"
    assert entry.logger_name == "ai_bos"
    assert entry.message == "Test error message"
    assert entry.user_id == 1


@pytest.mark.asyncio
async def test_get_log_entries(client, admin_token_headers, db_session):
    """Test listing log entries as admin."""
    from app.services.logging_history import create_log_entry

    await create_log_entry(db_session, level="INFO", logger_name="ai_bos", message="Test info")
    await create_log_entry(db_session, level="ERROR", logger_name="ai_bos", message="Test error")

    response = await client.get("/api/v1/logging/", headers=admin_token_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert "page" in data
    assert "page_size" in data


@pytest.mark.asyncio
async def test_get_log_entry_by_id(client, admin_token_headers, db_session):
    """Test getting a single log entry by ID."""
    from app.services.logging_history import create_log_entry

    entry = await create_log_entry(
        db_session, level="WARNING", logger_name="ai_bos", message="Test warning"
    )

    response = await client.get(f"/api/v1/logging/{entry.id}", headers=admin_token_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["level"] == "WARNING"
    assert data["message"] == "Test warning"


@pytest.mark.asyncio
async def test_log_entries_unauthorized(client, user_token_headers):
    """Test that non-superuser cannot list all log entries."""
    response = await client.get("/api/v1/logging/", headers=user_token_headers)
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.asyncio
async def test_log_entries_require_auth(client):
    """Test that log entries require authentication."""
    response = await client.get("/api/v1/logging/")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.asyncio
async def test_log_entry_not_found(client, admin_token_headers):
    """Test getting non-existent log entry returns 404."""
    response = await client.get("/api/v1/logging/99999", headers=admin_token_headers)
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_log_entries_filter_by_level(client, admin_token_headers, db_session):
    """Test filtering log entries by level."""
    from app.services.logging_history import create_log_entry

    await create_log_entry(db_session, level="INFO", logger_name="ai_bos", message="Info message")
    await create_log_entry(db_session, level="ERROR", logger_name="ai_bos", message="Error message")

    response = await client.get(
        "/api/v1/logging/?level=ERROR",
        headers=admin_token_headers,
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert all(log["level"] == "ERROR" for log in data["items"])


@pytest.mark.asyncio
async def test_log_entries_filter_by_logger_name(client, admin_token_headers, db_session):
    """Test filtering log entries by logger name."""
    from app.services.logging_history import create_log_entry

    await create_log_entry(db_session, level="INFO", logger_name="ai_bos", message="Message 1")
    await create_log_entry(db_session, level="INFO", logger_name="other_logger", message="Message 2")

    response = await client.get(
        "/api/v1/logging/?logger_name=ai_bos",
        headers=admin_token_headers,
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert all(log["logger_name"] == "ai_bos" for log in data["items"])


@pytest.mark.asyncio
async def test_log_entries_filter_by_user_id(client, admin_token_headers, db_session, test_user):
    """Test filtering log entries by user ID."""
    from app.services.logging_history import create_log_entry

    await create_log_entry(
        db_session, level="INFO", logger_name="ai_bos", message="User log", user_id=test_user.id
    )

    response = await client.get(
        f"/api/v1/logging/?user_id={test_user.id}",
        headers=admin_token_headers,
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert all(log["user_id"] == test_user.id for log in data["items"])


@pytest.mark.asyncio
async def test_log_stats(client, admin_token_headers, db_session):
    """Test getting log statistics."""
    from app.services.logging_history import create_log_entry

    await create_log_entry(db_session, level="INFO", logger_name="ai_bos", message="Info")
    await create_log_entry(db_session, level="ERROR", logger_name="ai_bos", message="Error")
    await create_log_entry(db_session, level="WARNING", logger_name="other", message="Warning")

    response = await client.get("/api/v1/logging/stats", headers=admin_token_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "total_entries" in data
    assert "by_level" in data
    assert "top_loggers" in data
    assert data["total_entries"] >= 3


@pytest.mark.asyncio
async def test_log_stats_unauthorized(client, user_token_headers):
    """Test that non-superuser cannot get log stats."""
    response = await client.get("/api/v1/logging/stats", headers=user_token_headers)
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.asyncio
async def test_log_cleanup(client, admin_token_headers, db_session):
    """Test cleaning up old log entries."""
    from app.services.logging_history import create_log_entry

    # Create an old log entry
    old_date = datetime.utcnow() - timedelta(days=100)
    await create_log_entry(
        db_session,
        level="INFO",
        logger_name="ai_bos",
        message="Old log entry",
        timestamp=old_date,
    )

    # Create a recent log entry
    await create_log_entry(
        db_session,
        level="INFO",
        logger_name="ai_bos",
        message="Recent log entry",
    )

    response = await client.delete(
        "/api/v1/logging/?older_than_days=90",
        headers=admin_token_headers,
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["deleted_count"] >= 1


@pytest.mark.asyncio
async def test_log_cleanup_unauthorized(client, user_token_headers):
    """Test that non-superuser cannot cleanup logs."""
    response = await client.delete(
        "/api/v1/logging/?older_than_days=90",
        headers=user_token_headers,
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.asyncio
async def test_log_entry_service_create_and_get(db_session):
    """Test log entry service create and get operations."""
    from app.services.logging_history import (
        create_log_entry,
        get_log_entry,
        get_log_entries,
    )

    # Create
    entry = await create_log_entry(
        db_session,
        level="INFO",
        logger_name="ai_bos",
        message="Test message",
        user_id=1,
    )
    assert entry.id is not None

    # Get by ID
    fetched = await get_log_entry(db_session, entry.id)
    assert fetched is not None
    assert fetched.level == "INFO"

    # Get list
    entries = await get_log_entries(db_session, limit=10)
    assert len(entries) >= 1


@pytest.mark.asyncio
async def test_log_entry_service_count(db_session):
    """Test log entry count with filters."""
    from app.services.logging_history import create_log_entry, count_log_entries

    await create_log_entry(db_session, level="INFO", logger_name="ai_bos", message="Info")
    await create_log_entry(db_session, level="ERROR", logger_name="ai_bos", message="Error")
    await create_log_entry(db_session, level="INFO", logger_name="other", message="Info 2")

    total = await count_log_entries(db_session)
    assert total >= 3

    info_count = await count_log_entries(db_session, level="INFO")
    assert info_count >= 2

    error_count = await count_log_entries(db_session, level="ERROR")
    assert error_count >= 1


@pytest.mark.asyncio
async def test_log_entry_service_stats(db_session):
    """Test log entry statistics."""
    from app.services.logging_history import create_log_entry, get_log_stats

    await create_log_entry(db_session, level="INFO", logger_name="ai_bos", message="Info")
    await create_log_entry(db_session, level="ERROR", logger_name="ai_bos", message="Error")
    await create_log_entry(db_session, level="WARNING", logger_name="other", message="Warning")

    stats = await get_log_stats(db_session)
    assert stats["total_entries"] >= 3
    assert "INFO" in stats["by_level"]
    assert "ERROR" in stats["by_level"]
    assert len(stats["top_loggers"]) > 0
    assert stats["oldest_entry"] is not None
    assert stats["newest_entry"] is not None


@pytest.mark.asyncio
async def test_log_entry_service_cleanup(db_session):
    """Test log entry cleanup."""
    from app.services.logging_history import create_log_entry, cleanup_old_logs

    # Create old entry
    old_date = datetime.utcnow() - timedelta(days=100)
    await create_log_entry(
        db_session,
        level="INFO",
        logger_name="ai_bos",
        message="Old entry",
        timestamp=old_date,
    )

    # Create recent entry
    await create_log_entry(
        db_session,
        level="INFO",
        logger_name="ai_bos",
        message="Recent entry",
    )

    deleted = await cleanup_old_logs(db_session, older_than_days=90)
    assert deleted >= 1

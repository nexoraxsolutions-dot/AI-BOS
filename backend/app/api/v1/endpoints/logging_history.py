"""Logging History API Endpoints.

Provides:
- GET /logging/ - List log entries with filtering (superuser only)
- GET /logging/stats - Get log statistics (superuser only)
- GET /logging/{id} - Get a single log entry (superuser only)
- DELETE /logging/ - Cleanup old log entries (superuser only)
"""
import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import require_superuser
from app.db.dependencies import get_async_session
from app.schemas import logging_history as logging_schema
from app.services import logging_history as logging_service

logger = logging.getLogger("ai_bos")

router = APIRouter()


@router.get("/", response_model=logging_schema.LogEntryListResponse)
async def list_log_entries(
    skip: int = 0,
    limit: int = Query(default=50, le=100),
    level: Optional[str] = Query(None, description="Filter by log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)"),
    logger_name: Optional[str] = Query(None, description="Filter by logger name"),
    user_id: Optional[int] = Query(None, description="Filter by user ID"),
    start_date: Optional[datetime] = Query(None, description="Filter entries from this date"),
    end_date: Optional[datetime] = Query(None, description="Filter entries up to this date"),
    search: Optional[str] = Query(None, description="Search in log messages"),
    db: AsyncSession = Depends(get_async_session),
    current_user=Depends(require_superuser),
):
    """List log entries with optional filtering. Superuser only."""
    entries = await logging_service.get_log_entries(
        db,
        skip=skip,
        limit=limit,
        level=level,
        logger_name=logger_name,
        user_id=user_id,
        start_date=start_date,
        end_date=end_date,
        search=search,
    )
    total = await logging_service.count_log_entries(
        db,
        level=level,
        logger_name=logger_name,
        user_id=user_id,
        start_date=start_date,
        end_date=end_date,
        search=search,
    )
    page = skip // limit + 1 if limit > 0 else 1
    return logging_schema.LogEntryListResponse(
        items=entries,
        total=total,
        page=page,
        page_size=limit,
    )


@router.get("/stats", response_model=dict)
async def get_log_stats(
    db: AsyncSession = Depends(get_async_session),
    current_user=Depends(require_superuser),
):
    """Get log statistics including level distribution and top loggers. Superuser only."""
    return await logging_service.get_log_stats(db)


@router.get("/{entry_id}", response_model=logging_schema.LogEntryOut)
async def get_log_entry(
    entry_id: int,
    db: AsyncSession = Depends(get_async_session),
    current_user=Depends(require_superuser),
):
    """Get a specific log entry by ID. Superuser only."""
    entry = await logging_service.get_log_entry(db, entry_id)
    if not entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Log entry not found",
        )
    return entry


@router.delete("/", response_model=dict)
async def cleanup_logs(
    older_than_days: int = Query(default=90, ge=1, description="Delete entries older than this many days"),
    db: AsyncSession = Depends(get_async_session),
    current_user=Depends(require_superuser),
):
    """Delete log entries older than specified days. Superuser only."""
    deleted_count = await logging_service.cleanup_old_logs(db, older_than_days)
    logger.info("Log cleanup: deleted %d entries older than %d days", deleted_count, older_than_days)
    return {
        "message": f"Deleted {deleted_count} log entries older than {older_than_days} days",
        "deleted_count": deleted_count,
    }

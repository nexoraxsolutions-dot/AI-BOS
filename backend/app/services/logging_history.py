"""Logging History Service.

Provides CRUD and query operations for persisted application log entries,
including filtering by level, logger name, user, and date range, as well
as statistics and cleanup of old entries.
"""
import logging
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.logging_history import LogEntry
from app.services.cache import cache_service

logger = logging.getLogger("ai_bos")

VALID_LEVELS = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}


async def create_log_entry(
    db: AsyncSession,
    level: str,
    logger_name: str,
    message: str,
    module: str | None = None,
    func_name: str | None = None,
    line_no: int | None = None,
    pathname: str | None = None,
    thread_name: str | None = None,
    process: str | None = None,
    user_id: int | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
    extra_data: dict | None = None,
    timestamp: datetime | None = None,
) -> LogEntry:
    """Create a new log entry in the database."""
    log_entry = LogEntry(
        level=level.upper(),
        logger_name=logger_name,
        message=message,
        module=module,
        func_name=func_name,
        line_no=line_no,
        pathname=pathname,
        thread_name=thread_name,
        process=process,
        user_id=user_id,
        ip_address=ip_address,
        user_agent=user_agent,
        extra_data=extra_data,
        timestamp=timestamp or datetime.utcnow(),
    )
    db.add(log_entry)
    await db.commit()
    await db.refresh(log_entry)

    # Invalidate log entries cache
    await cache_service.delete_pattern("log_entries:list:*")
    await cache_service.delete_pattern("log_entries:stats:*")

    return log_entry


async def get_log_entries(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 50,
    level: str | None = None,
    logger_name: str | None = None,
    user_id: int | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    search: str | None = None,
) -> list[LogEntry]:
    """Get log entries with optional filtering."""
    cache_key = (
        f"log_entries:list:{skip}:{limit}:"
        f"{level or 'all'}:{logger_name or 'all'}:"
        f"{user_id or 'all'}:{start_date or 'all'}:"
        f"{end_date or 'all'}:{search or 'all'}"
    )
    cached = await cache_service.get(cache_key)
    if cached:
        return cached

    query = select(LogEntry).order_by(LogEntry.timestamp.desc())

    if level:
        query = query.where(LogEntry.level == level.upper())
    if logger_name:
        query = query.where(LogEntry.logger_name == logger_name)
    if user_id:
        query = query.where(LogEntry.user_id == user_id)
    if start_date:
        query = query.where(LogEntry.timestamp >= start_date)
    if end_date:
        query = query.where(LogEntry.timestamp <= end_date)
    if search:
        query = query.where(LogEntry.message.ilike(f"%{search}%"))

    query = query.offset(skip).limit(limit)

    result = await db.execute(query)
    entries = result.scalars().all()

    entries_list = [entry.__dict__ for entry in entries]
    await cache_service.set(cache_key, entries_list, ttl=300)

    return entries


async def get_log_entry(db: AsyncSession, entry_id: int) -> LogEntry | None:
    """Get a single log entry by ID."""
    cache_key = f"log_entry:{entry_id}"
    cached = await cache_service.get(cache_key)
    if cached:
        return cached

    result = await db.execute(select(LogEntry).where(LogEntry.id == entry_id))
    entry = result.scalar_one_or_none()

    if entry:
        await cache_service.set(cache_key, entry.__dict__, ttl=600)

    return entry


async def count_log_entries(
    db: AsyncSession,
    level: str | None = None,
    logger_name: str | None = None,
    user_id: int | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    search: str | None = None,
) -> int:
    """Count total log entries with optional filtering."""
    query = select(func.count()).select_from(LogEntry)

    if level:
        query = query.where(LogEntry.level == level.upper())
    if logger_name:
        query = query.where(LogEntry.logger_name == logger_name)
    if user_id:
        query = query.where(LogEntry.user_id == user_id)
    if start_date:
        query = query.where(LogEntry.timestamp >= start_date)
    if end_date:
        query = query.where(LogEntry.timestamp <= end_date)
    if search:
        query = query.where(LogEntry.message.ilike(f"%{search}%"))

    result = await db.execute(query)
    return result.scalar_one()


async def get_log_stats(db: AsyncSession) -> dict:
    """Get log statistics including level distribution and top loggers."""
    cache_key = "log_entries:stats:all"
    cached = await cache_service.get(cache_key)
    if cached:
        return cached

    # Total entries
    total_result = await db.execute(select(func.count()).select_from(LogEntry))
    total = total_result.scalar_one()

    # By level
    level_result = await db.execute(
        select(LogEntry.level, func.count(LogEntry.id))
        .group_by(LogEntry.level)
        .order_by(func.count(LogEntry.id).desc())
    )
    by_level = {row[0]: row[1] for row in level_result.fetchall()}

    # Top loggers
    logger_result = await db.execute(
        select(LogEntry.logger_name, func.count(LogEntry.id))
        .group_by(LogEntry.logger_name)
        .order_by(func.count(LogEntry.id).desc())
        .limit(10)
    )
    top_loggers = [
        {"logger_name": row[0], "count": row[1]} for row in logger_result.fetchall()
    ]

    # Oldest and newest entries
    oldest_result = await db.execute(
        select(func.min(LogEntry.timestamp)).select_from(LogEntry)
    )
    oldest = oldest_result.scalar_one()

    newest_result = await db.execute(
        select(func.max(LogEntry.timestamp)).select_from(LogEntry)
    )
    newest = newest_result.scalar_one()

    stats = {
        "total_entries": total,
        "by_level": by_level,
        "top_loggers": top_loggers,
        "oldest_entry": oldest.isoformat() if oldest else None,
        "newest_entry": newest.isoformat() if newest else None,
    }

    await cache_service.set(cache_key, stats, ttl=300)
    return stats


async def cleanup_old_logs(db: AsyncSession, older_than_days: int = 90) -> int:
    """Delete log entries older than specified days.

    Args:
        db: Database session
        older_than_days: Delete entries older than this many days

    Returns:
        Number of entries deleted
    """
    cutoff = datetime.utcnow() - timedelta(days=older_than_days)
    result = await db.execute(
        delete(LogEntry).where(LogEntry.timestamp < cutoff)
    )
    await db.commit()

    # Invalidate cache
    await cache_service.delete_pattern("log_entries:list:*")
    await cache_service.delete_pattern("log_entries:stats:*")

    logger.info("Cleaned up %d log entries older than %d days", result.rowcount, older_than_days)
    return result.rowcount

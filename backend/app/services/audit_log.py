import logging
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog
from app.services.cache import cache_service

logger = logging.getLogger("ai_bos")


async def create_audit_log(
    db: AsyncSession,
    action: str,
    resource_type: str,
    resource_id: int | None = None,
    user_id: int | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
    details: dict | None = None,
) -> AuditLog:
    """Create a new audit log entry."""
    audit_log = AuditLog(
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        user_id=user_id,
        ip_address=ip_address,
        user_agent=user_agent,
        details=details,
    )
    db.add(audit_log)
    await db.commit()
    await db.refresh(audit_log)

    # Invalidate audit logs cache
    await cache_service.delete_pattern("audit_logs:list:*")

    return audit_log


async def get_audit_logs(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 50,
    action: str | None = None,
    resource_type: str | None = None,
    user_id: int | None = None,
) -> list[AuditLog]:
    """Get audit logs with optional filtering."""
    cache_key = f"audit_logs:list:{skip}:{limit}:{action or 'all'}:{resource_type or 'all'}:{user_id or 'all'}"
    cached = await cache_service.get(cache_key)
    if cached:
        return cached

    query = select(AuditLog).order_by(AuditLog.created_at.desc())

    if action:
        query = query.where(AuditLog.action == action)
    if resource_type:
        query = query.where(AuditLog.resource_type == resource_type)
    if user_id:
        query = query.where(AuditLog.user_id == user_id)

    query = query.offset(skip).limit(limit)

    result = await db.execute(query)
    logs = result.scalars().all()

    logs_list = [log.__dict__ for log in logs]
    await cache_service.set(cache_key, logs_list, ttl=300)

    return logs


async def get_audit_log(db: AsyncSession, log_id: int) -> AuditLog | None:
    """Get a single audit log by ID."""
    cache_key = f"audit_log:{log_id}"
    cached = await cache_service.get(cache_key)
    if cached:
        return cached

    result = await db.execute(select(AuditLog).where(AuditLog.id == log_id))
    log = result.scalar_one_or_none()

    if log:
        await cache_service.set(cache_key, log.__dict__, ttl=600)

    return log


async def count_audit_logs(
    db: AsyncSession,
    action: str | None = None,
    resource_type: str | None = None,
    user_id: int | None = None,
) -> int:
    """Count total audit logs with optional filtering."""
    query = select(func.count()).select_from(AuditLog)

    if action:
        query = query.where(AuditLog.action == action)
    if resource_type:
        query = query.where(AuditLog.resource_type == resource_type)
    if user_id:
        query = query.where(AuditLog.user_id == user_id)

    result = await db.execute(query)
    return result.scalar_one()


async def delete_audit_logs(db: AsyncSession, older_than_days: int = 90) -> int:
    """Delete audit logs older than specified days (for cleanup)."""
    from datetime import datetime, timedelta

    cutoff = datetime.utcnow() - timedelta(days=older_than_days)
    result = await db.execute(
        AuditLog.__table__.delete().where(AuditLog.created_at < cutoff)
    )
    await db.commit()

    # Invalidate cache
    await cache_service.delete_pattern("audit_logs:list:*")

    return result.rowcount

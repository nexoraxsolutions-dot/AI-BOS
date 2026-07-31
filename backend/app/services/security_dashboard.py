from datetime import datetime, timedelta
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.audit_log import AuditLog
from app.models.session import UserSession
from app.models.token import Token
from app.services.cache import cache_service


async def get_security_dashboard_data(db: AsyncSession) -> dict:
    """Aggregate security dashboard statistics from the database with caching."""
    cache_key = "security:dashboard:summary"
    cached_data = await cache_service.get(cache_key)
    if cached_data:
        return cached_data

    now = datetime.utcnow()
    last_24_hours = now - timedelta(hours=24)
    last_7_days = now - timedelta(days=7)
    last_30_days = now - timedelta(days=30)

    # Account security metrics
    total_users_result = await db.execute(select(func.count(User.id)))
    total_users = total_users_result.scalar() or 0

    # Users with 2FA enabled
    users_with_2fa_result = await db.execute(
        select(func.count(User.id)).where(User.is_2fa_enabled == True)
    )
    users_with_2fa = users_with_2fa_result.scalar() or 0

    # Locked accounts
    locked_accounts_result = await db.execute(
        select(func.count(User.id)).where(
            and_(
                User.locked_until.isnot(None),
                User.locked_until > now
            )
        )
    )
    locked_accounts = locked_accounts_result.scalar() or 0

    # Users with failed login attempts
    failed_login_users_result = await db.execute(
        select(func.count(User.id)).where(User.failed_login_attempts > 0)
    )
    users_with_failed_logins = failed_login_users_result.scalar() or 0

    # Active sessions
    active_sessions_result = await db.execute(
        select(func.count(UserSession.id)).where(
            and_(
                UserSession.is_active == True,
                UserSession.expires_at > now
            )
        )
    )
    active_sessions = active_sessions_result.scalar() or 0

    # Audit log metrics
    # Failed login attempts (last 24h)
    failed_logins_24h_result = await db.execute(
        select(func.count(AuditLog.id)).where(
            and_(
                AuditLog.action == "login_failed",
                AuditLog.created_at >= last_24_hours
            )
        )
    )
    failed_logins_24h = failed_logins_24h_result.scalar() or 0

    # Failed login attempts (last 7 days)
    failed_logins_7d_result = await db.execute(
        select(func.count(AuditLog.id)).where(
            and_(
                AuditLog.action == "login_failed",
                AuditLog.created_at >= last_7_days
            )
        )
    )
    failed_logins_7d = failed_logins_7d_result.scalar() or 0

    # Account lockouts (last 30 days)
    account_lockouts_result = await db.execute(
        select(func.count(AuditLog.id)).where(
            and_(
                AuditLog.action == "account_locked",
                AuditLog.created_at >= last_30_days
            )
        )
    )
    account_lockouts_30d = account_lockouts_result.scalar() or 0

    # Password changes (last 30 days)
    password_changes_result = await db.execute(
        select(func.count(AuditLog.id)).where(
            and_(
                AuditLog.action == "password_changed",
                AuditLog.created_at >= last_30_days
            )
        )
    )
    password_changes_30d = password_changes_result.scalar() or 0

    # 2FA enabled events (last 30 days)
    two_fa_enabled_result = await db.execute(
        select(func.count(AuditLog.id)).where(
            and_(
                AuditLog.action == "2fa_enabled",
                AuditLog.created_at >= last_30_days
            )
        )
    )
    two_fa_enabled_30d = two_fa_enabled_result.scalar() or 0

    # Suspicious activities (multiple failed logins from same IP)
    suspicious_activities_result = await db.execute(
        select(AuditLog.ip_address, func.count(AuditLog.id).label('count'))
        .where(
            and_(
                AuditLog.action == "login_failed",
                AuditLog.created_at >= last_24_hours
            )
        )
        .group_by(AuditLog.ip_address)
        .having(func.count(AuditLog.id) >= 5)
    )
    suspicious_activities = suspicious_activities_result.all()
    suspicious_ips_count = len(suspicious_activities)

    # Security score calculation
    security_score = 100
    if total_users > 0:
        # Deduct for low 2FA adoption
        two_fa_adoption_rate = (users_with_2fa / total_users) * 100
        if two_fa_adoption_rate < 50:
            security_score -= 20
        elif two_fa_adoption_rate < 80:
            security_score -= 10

        # Deduct for locked accounts
        locked_rate = (locked_accounts / total_users) * 100
        if locked_rate > 5:
            security_score -= 15

        # Deduct for high failed login rate
        if total_users > 0 and failed_logins_24h > total_users * 0.5:
            security_score -= 15

    # Deduct for suspicious activities
    security_score -= min(suspicious_ips_count * 5, 20)

    # Ensure score doesn't go below 0
    security_score = max(0, security_score)

    # Recent security events
    recent_events_result = await db.execute(
        select(AuditLog)
        .where(
            and_(
                AuditLog.action.in_([
                    "login_failed",
                    "account_locked",
                    "password_changed",
                    "2fa_enabled",
                    "2fa_disabled",
                    "suspicious_activity"
                ]),
                AuditLog.created_at >= last_7_days
            )
        )
        .order_by(AuditLog.created_at.desc())
        .limit(10)
    )
    recent_events = recent_events_result.scalars().all()

    result = {
        "security_score": security_score,
        "total_users": total_users,
        "users_with_2fa": users_with_2fa,
        "locked_accounts": locked_accounts,
        "users_with_failed_logins": users_with_failed_logins,
        "active_sessions": active_sessions,
        "failed_logins_24h": failed_logins_24h,
        "failed_logins_7d": failed_logins_7d,
        "account_lockouts_30d": account_lockouts_30d,
        "password_changes_30d": password_changes_30d,
        "two_fa_enabled_30d": two_fa_enabled_30d,
        "suspicious_ips_count": suspicious_ips_count,
        "recent_events": [
            {
                "id": event.id,
                "action": event.action,
                "user_id": event.user_id,
                "ip_address": event.ip_address,
                "created_at": event.created_at.isoformat(),
                "details": event.details
            }
            for event in recent_events
        ]
    }

    # Cache the result for 2 minutes (shorter TTL for security data)
    await cache_service.set(cache_key, result, ttl=120)

    return result
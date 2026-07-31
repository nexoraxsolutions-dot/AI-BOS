"""
Session Management Service

Provides session tracking and management functionality. Sessions represent
active user logins across devices with activity tracking and expiration.
"""
import logging
import secrets
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import select, delete, func, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.session import UserSession
from app.schemas.session import SessionCreate, SessionOut
from app.services.device import parse_user_agent

logger = logging.getLogger("ai_bos")


def generate_session_token() -> str:
    """Generate a secure random session token."""
    return secrets.token_urlsafe(32)


async def create_session(
    db: AsyncSession,
    user_id: int,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    expires_delta: Optional[timedelta] = None,
) -> UserSession:
    """Create a new session for a user.
    
    Args:
        db: Database session
        user_id: The user's ID
        ip_address: Client IP address
        user_agent: User agent string
        expires_delta: Custom expiration time (default: 24 hours)
    
    Returns:
        The created UserSession
    """
    from app.core.config import settings
    
    if expires_delta is None:
        expires_delta = timedelta(hours=settings.session_expire_hours)
    
    expires_at = datetime.utcnow() + expires_delta
    session_token = generate_session_token()
    
    # Parse user agent for device info
    device_info = parse_user_agent(user_agent)
    
    session = UserSession(
        user_id=user_id,
        session_token=session_token,
        ip_address=ip_address,
        user_agent=user_agent,
        device_name=device_info.device_name,
        device_type=device_info.device_type,
        browser=device_info.browser,
        os=device_info.os,
        expires_at=expires_at,
        is_active=True,
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)
    
    logger.info(
        "Session created: user_id=%d, session_id=%d, device=%s",
        user_id, session.id, device_info.device_name
    )
    
    return session


async def get_session_by_token(db: AsyncSession, session_token: str) -> Optional[UserSession]:
    """Get an active session by token.
    
    Args:
        db: Database session
        session_token: The session token
    
    Returns:
        The UserSession if found and active, None otherwise
    """
    result = await db.execute(
        select(UserSession).where(
            UserSession.session_token == session_token,
            UserSession.is_active == True,  # noqa: E712
        )
    )
    session = result.scalars().first()
    
    if not session:
        return None
    
    # Check if session has expired
    if session.expires_at < datetime.utcnow():
        return None
    
    return session


async def update_session_activity(db: AsyncSession, session_id: int) -> Optional[UserSession]:
    """Update the last activity timestamp for a session.
    
    Args:
        db: Database session
        session_id: The session ID
    
    Returns:
        The updated UserSession, or None if not found
    """
    result = await db.execute(
        select(UserSession).where(UserSession.id == session_id)
    )
    session = result.scalars().first()
    
    if not session:
        return None
    
    session.last_activity_at = datetime.utcnow()
    await db.commit()
    await db.refresh(session)
    
    return session


async def terminate_session(db: AsyncSession, session_id: int, user_id: int) -> Optional[UserSession]:
    """Terminate a specific session.
    
    Args:
        db: Database session
        session_id: The session ID to terminate
        user_id: The user's ID (for ownership check)
    
    Returns:
        The terminated UserSession, or None if not found
    """
    result = await db.execute(
        select(UserSession).where(
            UserSession.id == session_id,
            UserSession.user_id == user_id,
        )
    )
    session = result.scalars().first()
    
    if not session:
        return None
    
    session.is_active = False
    session.terminated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(session)
    
    logger.info(
        "Session terminated: user_id=%d, session_id=%d",
        user_id, session_id
    )
    
    return session


async def terminate_user_sessions(
    db: AsyncSession,
    user_id: int,
    exclude_session_id: Optional[int] = None,
) -> int:
    """Terminate all active sessions for a user.
    
    Args:
        db: Database session
        user_id: The user's ID
        exclude_session_id: Optional session ID to exclude from termination
    
    Returns:
        Number of sessions terminated
    """
    query = select(UserSession).where(
        UserSession.user_id == user_id,
        UserSession.is_active == True,  # noqa: E712
    )
    
    if exclude_session_id:
        query = query.where(UserSession.id != exclude_session_id)
    
    result = await db.execute(query)
    sessions = result.scalars().all()
    
    count = 0
    for session in sessions:
        session.is_active = False
        session.terminated_at = datetime.utcnow()
        count += 1
    
    if count > 0:
        await db.commit()
        logger.info(
            "All sessions terminated for user_id=%d, count=%d",
            user_id, count
        )
    
    return count


async def get_user_sessions(
    db: AsyncSession,
    user_id: int,
    skip: int = 0,
    limit: int = 50,
    include_inactive: bool = False,
) -> tuple[list[UserSession], int]:
    """Get sessions for a user with pagination.
    
    Args:
        db: Database session
        user_id: The user's ID
        skip: Pagination offset
        limit: Page size
        include_inactive: Whether to include inactive sessions
    
    Returns:
        Tuple of (sessions list, total count)
    """
    query = select(UserSession).where(UserSession.user_id == user_id)
    count_query = select(func.count(UserSession.id)).where(UserSession.user_id == user_id)
    
    if not include_inactive:
        query = query.where(UserSession.is_active == True)  # noqa: E712
        count_query = count_query.where(UserSession.is_active == True)  # noqa: E712
    
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    query = query.order_by(UserSession.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    sessions = result.scalars().all()
    
    return list(sessions), total


async def get_session_by_id(db: AsyncSession, session_id: int, user_id: int) -> Optional[UserSession]:
    """Get a specific session by ID, verifying ownership.
    
    Args:
        db: Database session
        session_id: The session ID
        user_id: The user's ID (for ownership check)
    
    Returns:
        The UserSession if found and owned by user, None otherwise
    """
    result = await db.execute(
        select(UserSession).where(
            UserSession.id == session_id,
            UserSession.user_id == user_id,
        )
    )
    return result.scalars().first()


async def cleanup_expired_sessions(db: AsyncSession) -> int:
    """Delete expired sessions from the database.
    
    Args:
        db: Database session
    
    Returns:
        Number of sessions deleted
    """
    result = await db.execute(
        delete(UserSession).where(UserSession.expires_at < datetime.utcnow())
    )
    deleted_count = result.rowcount
    await db.commit()
    
    if deleted_count > 0:
        logger.info("Cleaned up %d expired sessions", deleted_count)
    
    return deleted_count


async def get_session_stats(db: AsyncSession, user_id: int) -> dict:
    """Get session statistics for a user.
    
    Args:
        db: Database session
        user_id: The user's ID
    
    Returns:
        Dict with session statistics
    """
    result = await db.execute(
        select(UserSession).where(UserSession.user_id == user_id)
    )
    sessions = result.scalars().all()
    
    total = len(sessions)
    active = sum(1 for s in sessions if s.is_active and s.expires_at > datetime.utcnow())
    inactive = sum(1 for s in sessions if not s.is_active)
    expired = sum(1 for s in sessions if s.expires_at < datetime.utcnow())
    
    # Device type breakdown
    type_breakdown = {}
    for s in sessions:
        dt = s.device_type or "unknown"
        type_breakdown[dt] = type_breakdown.get(dt, 0) + 1
    
    return {
        "total_sessions": total,
        "active_sessions": active,
        "inactive_sessions": inactive,
        "expired_sessions": expired,
        "device_type_breakdown": type_breakdown,
    }


def session_to_out(session: UserSession) -> SessionOut:
    """Convert a UserSession model to a SessionOut schema.
    
    Args:
        session: The UserSession model
    
    Returns:
        SessionOut schema
    """
    return SessionOut(
        id=session.id,
        user_id=session.user_id,
        session_token=session.session_token,
        ip_address=session.ip_address,
        user_agent=session.user_agent,
        device_name=session.device_name,
        device_type=session.device_type,
        browser=session.browser,
        os=session.os,
        is_active=session.is_active,
        last_activity_at=session.last_activity_at,
        expires_at=session.expires_at,
        created_at=session.created_at,
        terminated_at=session.terminated_at,
    )
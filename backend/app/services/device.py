"""
Device Management Service

Provides device/session tracking and management by extending the existing
Token model with device-specific fields. Parses user-agent strings to
extract device type, browser, and OS information.
"""
import re
import logging
from datetime import datetime
from typing import Optional

from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.token import Token
from app.schemas.token import DeviceInfo, DeviceOut

logger = logging.getLogger("ai_bos")


def parse_user_agent(user_agent: Optional[str]) -> DeviceInfo:
    """Parse a user-agent string to extract device information.

    Args:
        user_agent: The raw user-agent string from the HTTP request

    Returns:
        DeviceInfo with parsed device type, browser, OS, and device name
    """
    if not user_agent:
        return DeviceInfo(
            device_type="unknown",
            device_name="Unknown Device",
            browser="Unknown",
            os="Unknown",
            is_desktop=True,
        )

    ua = user_agent.lower()

    # Detect device type (check tablet before mobile since iPad UAs contain "mobile")
    is_tablet = "ipad" in ua or "tablet" in ua or "playbook" in ua
    is_mobile = ("mobile" in ua or "android" in ua or "iphone" in ua) and not is_tablet
    is_desktop = not is_mobile and not is_tablet

    if is_mobile:
        device_type = "mobile"
    elif is_tablet:
        device_type = "tablet"
    else:
        device_type = "desktop"

    # Detect browser
    browser = "Unknown"
    if "edg/" in ua:
        browser = "Edge"
    elif "chrome/" in ua and "chromium" not in ua:
        browser = "Chrome"
    elif "firefox/" in ua:
        browser = "Firefox"
    elif "safari/" in ua and "chrome" not in ua:
        browser = "Safari"
    elif "opera" in ua or "opr/" in ua:
        browser = "Opera"

    # Detect OS (check iPhone OS before Mac OS since iPhone UAs contain "Mac OS X")
    os_name = "Unknown"
    if "windows" in ua:
        os_name = "Windows"
    elif "iphone os" in ua or "ipad" in ua:
        os_name = "iOS"
    elif "mac os" in ua or "macintosh" in ua:
        os_name = "macOS"
    elif "android" in ua:
        os_name = "Android"
    elif "linux" in ua:
        os_name = "Linux"

    # Generate device name
    if is_mobile:
        device_name = f"{os_name} Mobile"
    elif is_tablet:
        device_name = f"{os_name} Tablet"
    else:
        device_name = f"{os_name} ({browser})"

    return DeviceInfo(
        device_type=device_type,
        device_name=device_name,
        browser=browser,
        os=os_name,
        is_mobile=is_mobile,
        is_tablet=is_tablet,
        is_desktop=is_desktop,
    )


def generate_device_name(user_agent: Optional[str]) -> str:
    """Generate a human-readable device name from user-agent."""
    info = parse_user_agent(user_agent)
    return info.device_name


def generate_device_type(user_agent: Optional[str]) -> str:
    """Generate device type from user-agent."""
    info = parse_user_agent(user_agent)
    return info.device_type


async def get_user_devices(
    db: AsyncSession,
    user_id: int,
    skip: int = 0,
    limit: int = 50,
    include_revoked: bool = False,
) -> tuple[list[Token], int]:
    """Get all active devices/sessions for a user.

    Args:
        db: Database session
        user_id: The user's ID
        skip: Pagination offset
        limit: Page size
        include_revoked: Whether to include revoked tokens

    Returns:
        Tuple of (devices list, total count)
    """
    query = select(Token).where(Token.user_id == user_id)
    count_query = select(func.count(Token.id)).where(Token.user_id == user_id)

    if not include_revoked:
        query = query.where(Token.is_revoked == False)
        count_query = count_query.where(Token.is_revoked == False)

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    query = query.order_by(Token.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    tokens = result.scalars().all()
    return list(tokens), total


async def get_device_by_id(db: AsyncSession, device_id: int, user_id: int) -> Optional[Token]:
    """Get a specific device by ID, verifying ownership."""
    result = await db.execute(
        select(Token).where(Token.id == device_id, Token.user_id == user_id)
    )
    return result.scalars().first()


async def revoke_device(db: AsyncSession, device_id: int, user_id: int) -> Optional[Token]:
    """Revoke a specific device/session.

    Args:
        db: Database session
        device_id: The token/device ID
        user_id: The user's ID (for ownership check)

    Returns:
        The revoked token, or None if not found
    """
    token = await get_device_by_id(db, device_id, user_id)
    if not token:
        return None

    token.is_revoked = True
    await db.commit()
    await db.refresh(token)
    logger.info("Device revoked: user_id=%d, device_id=%d", user_id, device_id)
    return token


async def revoke_all_devices(db: AsyncSession, user_id: int) -> int:
    """Revoke all active devices/sessions for a user.

    Args:
        db: Database session
        user_id: The user's ID

    Returns:
        Number of devices revoked
    """
    result = await db.execute(
        select(Token).where(
            Token.user_id == user_id,
            Token.is_revoked == False,
        )
    )
    tokens = result.scalars().all()
    count = 0
    for token in tokens:
        token.is_revoked = True
        count += 1
    if count > 0:
        await db.commit()
    logger.info("All devices revoked: user_id=%d, count=%d", user_id, count)
    return count


async def update_device_last_used(db: AsyncSession, token_id: int) -> None:
    """Update the last_used_at timestamp for a device."""
    await db.execute(
        update(Token)
        .where(Token.id == token_id)
        .values(last_used_at=datetime.utcnow())
    )
    await db.commit()


async def mark_current_device(db: AsyncSession, token_id: int, user_id: int) -> None:
    """Mark a specific device as current, unmarking all others for the user."""
    # Unmark all current devices for this user
    await db.execute(
        update(Token)
        .where(Token.user_id == user_id, Token.is_current == True)
        .values(is_current=False)
    )
    # Mark the specified device as current
    await db.execute(
        update(Token)
        .where(Token.id == token_id, Token.user_id == user_id)
        .values(is_current=True)
    )
    await db.commit()


async def get_device_stats(db: AsyncSession, user_id: int) -> dict:
    """Get device statistics for a user.

    Returns:
        Dict with total devices, active devices, revoked devices,
        devices expiring soon, and device type breakdown
    """
    result = await db.execute(
        select(Token).where(Token.user_id == user_id)
    )
    tokens = result.scalars().all()

    total = len(tokens)
    active = sum(1 for t in tokens if not t.is_revoked and t.expires_at > datetime.utcnow())
    revoked = sum(1 for t in tokens if t.is_revoked)
    expiring_soon = sum(
        1 for t in tokens
        if not t.is_revoked
        and t.expires_at > datetime.utcnow()
        and (t.expires_at - datetime.utcnow()).total_seconds() < 86400  # < 24 hours
    )

    type_breakdown = {}
    for t in tokens:
        dt = t.device_type or "unknown"
        type_breakdown[dt] = type_breakdown.get(dt, 0) + 1

    return {
        "total_devices": total,
        "active_devices": active,
        "revoked_devices": revoked,
        "expiring_soon": expiring_soon,
        "device_type_breakdown": type_breakdown,
    }


def token_to_device_out(token: Token) -> DeviceOut:
    """Convert a Token model to a DeviceOut schema with parsed device info."""
    info = parse_user_agent(token.user_agent)
    return DeviceOut(
        id=token.id,
        user_id=token.user_id,
        device_name=token.device_name or info.device_name,
        device_type=token.device_type or info.device_type,
        browser=info.browser,
        os=info.os,
        client_ip=token.client_ip,
        is_current=token.is_current,
        is_revoked=token.is_revoked,
        expires_at=token.expires_at,
        created_at=token.created_at,
        last_used_at=token.last_used_at,
        user_agent=token.user_agent,
    )

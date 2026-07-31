import hashlib
import logging
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import select, delete, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.token import Token
from app.schemas.token import TokenCreate, TokenOut
from app.services.device import generate_device_name, generate_device_type

logger = logging.getLogger("ai_bos")


def hash_token(token_str: str) -> str:
    """Hash a token string for secure storage."""
    return hashlib.sha256(token_str.encode()).hexdigest()


async def store_token(
    db: AsyncSession,
    token_str: str,
    user_id: int,
    token_type: str = "refresh",
    client_ip: Optional[str] = None,
    user_agent: Optional[str] = None,
    expires_delta: Optional[timedelta] = None,
) -> Token:
    """Store a token in the database."""
    from app.core.config import settings

    if expires_delta is None:
        if token_type == "access":
            expires_delta = timedelta(minutes=settings.access_token_expire_minutes)
        else:
            expires_delta = timedelta(minutes=settings.refresh_token_expire_minutes)

    expires_at = datetime.utcnow() + expires_delta
    hashed = hash_token(token_str)

    token = Token(
        token=hashed,
        user_id=user_id,
        token_type=token_type,
        client_ip=client_ip,
        user_agent=user_agent,
        expires_at=expires_at,
        device_name=generate_device_name(user_agent) if user_agent else None,
        device_type=generate_device_type(user_agent) if user_agent else None,
    )
    db.add(token)
    await db.commit()
    await db.refresh(token)
    return token


async def verify_token(db: AsyncSession, token_str: str, token_type: str = "refresh") -> Optional[Token]:
    """Verify a token exists, is not revoked, and has not expired."""
    hashed = hash_token(token_str)
    result = await db.execute(
        select(Token).where(
            Token.token == hashed,
            Token.token_type == token_type,
            Token.is_revoked == False,  # noqa: E712
        )
    )
    token = result.scalars().first()
    if not token:
        return None
    if token.expires_at < datetime.utcnow():
        return None
    return token


async def revoke_token(db: AsyncSession, token_id: int, user_id: int) -> Optional[Token]:
    """Revoke a specific token by ID."""
    result = await db.execute(
        select(Token).where(Token.id == token_id, Token.user_id == user_id)
    )
    token = result.scalars().first()
    if not token:
        return None
    token.is_revoked = True
    await db.commit()
    await db.refresh(token)
    return token


async def revoke_user_tokens(db: AsyncSession, user_id: int, token_type: Optional[str] = None) -> int:
    """Revoke all tokens for a user, optionally filtered by type."""
    query = select(Token).where(Token.user_id == user_id, Token.is_revoked == False)  # noqa: E712
    if token_type:
        query = query.where(Token.token_type == token_type)
    result = await db.execute(query)
    tokens = result.scalars().all()
    count = 0
    for token in tokens:
        token.is_revoked = True
        count += 1
    if count > 0:
        await db.commit()
    return count


async def get_user_tokens(
    db: AsyncSession,
    user_id: int,
    skip: int = 0,
    limit: int = 50,
    include_revoked: bool = False,
) -> tuple[list[Token], int]:
    """Get tokens for a user with pagination."""
    query = select(Token).where(Token.user_id == user_id)
    count_query = select(func.count(Token.id)).where(Token.user_id == user_id)

    if not include_revoked:
        query = query.where(Token.is_revoked == False)  # noqa: E712
        count_query = count_query.where(Token.is_revoked == False)  # noqa: E712

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    query = query.order_by(Token.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    tokens = result.scalars().all()
    return list(tokens), total


async def cleanup_expired_tokens(db: AsyncSession) -> int:
    """Delete expired tokens from the database."""
    result = await db.execute(
        delete(Token).where(Token.expires_at < datetime.utcnow())
    )
    deleted_count = result.rowcount
    await db.commit()
    if deleted_count > 0:
        logger.info("Cleaned up %d expired tokens", deleted_count)
    return deleted_count


async def get_all_tokens(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 50,
    include_revoked: bool = False,
) -> tuple[list[Token], int]:
    """Get all tokens (superuser) with pagination."""
    query = select(Token)
    count_query = select(func.count(Token.id))

    if not include_revoked:
        query = query.where(Token.is_revoked == False)  # noqa: E712
        count_query = count_query.where(Token.is_revoked == False)  # noqa: E712

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    query = query.order_by(Token.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    tokens = result.scalars().all()
    return list(tokens), total


async def get_token_by_id(db: AsyncSession, token_id: int) -> Optional[Token]:
    """Get a specific token by ID."""
    result = await db.execute(select(Token).where(Token.id == token_id))
    return result.scalars().first()
from datetime import timedelta
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token as create_security_access_token
from app.core.security import create_refresh_token as create_security_refresh_token
from app.services import token as token_service

# Re-export the hash function
hash_token = token_service.hash_token


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    return create_security_access_token(data=data, expires_delta=expires_delta)


def create_refresh_token(data: dict) -> str:
    return create_security_refresh_token(data=data)


async def store_refresh_token(
    db: AsyncSession,
    token_str: str,
    user_id: int,
    client_ip: Optional[str] = None,
    user_agent: Optional[str] = None,
) -> object:
    """Store a refresh token in the database with metadata."""
    return await token_service.store_token(
        db=db,
        token_str=token_str,
        user_id=user_id,
        token_type="refresh",
        client_ip=client_ip,
        user_agent=user_agent,
    )


async def verify_refresh_token(db: AsyncSession, token_str: str) -> Optional[object]:
    """Verify a refresh token exists and is not revoked."""
    return await token_service.verify_token(db, token_str, token_type="refresh")


async def revoke_token(db: AsyncSession, token_id: int, user_id: int) -> Optional[object]:
    """Revoke a specific token."""
    return await token_service.revoke_token(db, token_id, user_id)


async def revoke_all_user_tokens(db: AsyncSession, user_id: int, token_type: Optional[str] = None) -> int:
    """Revoke all tokens for a user."""
    return await token_service.revoke_user_tokens(db, user_id, token_type)
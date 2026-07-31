import secrets
import hashlib
import logging
from datetime import datetime
from typing import Optional

from sqlalchemy import select, delete, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.api_key import ApiKey
from app.schemas.api_key import ApiKeyCreate, ApiKeyUpdate

logger = logging.getLogger("ai_bos")


def hash_api_key(api_key: str) -> str:
    """Hash an API key for secure storage."""
    return hashlib.sha256(api_key.encode()).hexdigest()


def generate_api_key() -> str:
    """Generate a secure random API key."""
    return secrets.token_urlsafe(32)


async def create_api_key(
    db: AsyncSession,
    user_id: int,
    key_name: str,
    permissions: Optional[str] = None,
    expires_at: Optional[datetime] = None,
) -> tuple[ApiKey, str]:
    """Create a new API key. Returns the API key object and the plain text key (shown only once)."""
    plain_key = generate_api_key()
    hashed = hash_api_key(plain_key)

    api_key = ApiKey(
        user_id=user_id,
        key_name=key_name,
        api_key=hashed,
        permissions=permissions,
        expires_at=expires_at,
    )
    db.add(api_key)
    await db.commit()
    await db.refresh(api_key)
    
    logger.info("Created API key '%s' for user %d", key_name, user_id)
    return api_key, plain_key


async def get_api_key_by_id(db: AsyncSession, api_key_id: int) -> Optional[ApiKey]:
    """Get an API key by ID."""
    result = await db.execute(select(ApiKey).where(ApiKey.id == api_key_id))
    return result.scalars().first()


async def get_api_key_by_hash(db: AsyncSession, hashed_key: str) -> Optional[ApiKey]:
    """Get an API key by its hashed value."""
    result = await db.execute(select(ApiKey).where(ApiKey.api_key == hashed_key))
    return result.scalars().first()


async def get_user_api_keys(
    db: AsyncSession,
    user_id: int,
    skip: int = 0,
    limit: int = 50,
    include_inactive: bool = False,
) -> tuple[list[ApiKey], int]:
    """Get API keys for a user with pagination."""
    query = select(ApiKey).where(ApiKey.user_id == user_id)
    count_query = select(func.count(ApiKey.id)).where(ApiKey.user_id == user_id)

    if not include_inactive:
        query = query.where(ApiKey.is_active == True)  # noqa: E712
        count_query = count_query.where(ApiKey.is_active == True)  # noqa: E712

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    query = query.order_by(ApiKey.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    keys = result.scalars().all()
    return list(keys), total


async def get_all_api_keys(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 50,
    include_inactive: bool = False,
) -> tuple[list[ApiKey], int]:
    """Get all API keys (superuser) with pagination."""
    query = select(ApiKey)
    count_query = select(func.count(ApiKey.id))

    if not include_inactive:
        query = query.where(ApiKey.is_active == True)  # noqa: E712
        count_query = count_query.where(ApiKey.is_active == True)  # noqa: E712

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    query = query.order_by(ApiKey.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    keys = result.scalars().all()
    return list(keys), total


async def update_api_key(
    db: AsyncSession,
    api_key_id: int,
    user_id: int,
    data: ApiKeyUpdate,
) -> Optional[ApiKey]:
    """Update an API key (owner or superuser only)."""
    result = await db.execute(select(ApiKey).where(ApiKey.id == api_key_id))
    api_key = result.scalars().first()
    if not api_key:
        return None
    if api_key.user_id != user_id:
        return None

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(api_key, field, value)

    await db.commit()
    await db.refresh(api_key)
    
    logger.info("Updated API key '%s' for user %d", api_key.key_name, user_id)
    return api_key


async def delete_api_key(db: AsyncSession, api_key_id: int, user_id: int) -> bool:
    """Delete an API key (owner or superuser only)."""
    result = await db.execute(select(ApiKey).where(ApiKey.id == api_key_id))
    api_key = result.scalars().first()
    if not api_key:
        return False
    if api_key.user_id != user_id:
        return False

    await db.delete(api_key)
    await db.commit()
    
    logger.info("Deleted API key '%s' for user %d", api_key.key_name, user_id)
    return True


async def revoke_api_key(db: AsyncSession, api_key_id: int, user_id: int) -> Optional[ApiKey]:
    """Revoke an API key by setting is_active to False."""
    result = await db.execute(select(ApiKey).where(ApiKey.id == api_key_id))
    api_key = result.scalars().first()
    if not api_key:
        return None
    if api_key.user_id != user_id:
        return None

    api_key.is_active = False
    await db.commit()
    await db.refresh(api_key)
    
    logger.info("Revoked API key '%s' for user %d", api_key.key_name, user_id)
    return api_key


async def verify_api_key(db: AsyncSession, plain_key: str) -> Optional[ApiKey]:
    """Verify an API key is valid, active, and not expired."""
    hashed = hash_api_key(plain_key)
    api_key = await get_api_key_by_hash(db, hashed)
    
    if not api_key:
        return None
    if not api_key.is_active:
        return None
    if api_key.expires_at and api_key.expires_at < datetime.utcnow():
        return None

    # Update last_used_at
    api_key.last_used_at = datetime.utcnow()
    await db.commit()
    await db.refresh(api_key)
    
    return api_key
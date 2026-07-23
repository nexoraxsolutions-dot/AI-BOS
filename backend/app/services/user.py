from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_password_hash, verify_password
from app.models.user import User
from app.services.cache import cache_service


async def create_user(db: AsyncSession, payload):
    hashed_password = get_password_hash(payload.password)
    user = User(
        email=payload.email,
        username=payload.username,
        hashed_password=hashed_password,
        full_name=payload.full_name,
        is_active=True,
        is_superuser=False,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    # Invalidate users list cache
    await cache_service.delete_pattern("users:list:*")
    
    return user


async def get_user(db: AsyncSession, user_id: int):
    # Try cache first
    cache_key = f"user:{user_id}"
    cached_user = await cache_service.get(cache_key)
    if cached_user:
        return cached_user
    
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    # Cache user data
    if user:
        await cache_service.set(cache_key, user.__dict__, ttl=600)
    
    return user


async def get_user_by_email(db: AsyncSession, email: str):
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def get_user_by_username(db: AsyncSession, username: str):
    result = await db.execute(select(User).where(User.username == username))
    return result.scalar_one_or_none()


async def get_users(db: AsyncSession, skip: int = 0, limit: int = 20):
    # Try cache first
    cache_key = f"users:list:{skip}:{limit}"
    cached_users = await cache_service.get(cache_key)
    if cached_users:
        return cached_users
    
    result = await db.execute(select(User).offset(skip).limit(limit))
    users = result.scalars().all()
    
    # Cache users list
    users_list = [user.__dict__ for user in users]
    await cache_service.set(cache_key, users_list, ttl=300)
    
    return users


async def update_user(db: AsyncSession, user_id: int, payload):
    user = await get_user(db, user_id)
    if not user:
        return None
    update_data = payload.model_dump(exclude_unset=True)
    if "password" in update_data:
        update_data["hashed_password"] = get_password_hash(update_data.pop("password"))
    for field, value in update_data.items():
        setattr(user, field, value)
    await db.commit()
    await db.refresh(user)
    
    # Invalidate caches
    await cache_service.delete(f"user:{user_id}")
    await cache_service.delete_pattern("users:list:*")
    
    return user


async def delete_user(db: AsyncSession, user_id: int) -> bool:
    user = await get_user(db, user_id)
    if not user:
        return False
    await db.delete(user)
    await db.commit()
    
    # Invalidate caches
    await cache_service.delete(f"user:{user_id}")
    await cache_service.delete_pattern("users:list:*")
    
    return True


async def change_password(db: AsyncSession, user_id: int, current_password: str, new_password: str) -> bool:
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        return False
    if not verify_password(current_password, user.hashed_password):
        return False
    user.hashed_password = get_password_hash(new_password)
    await db.commit()
    await db.refresh(user)
    
    # Invalidate caches
    await cache_service.delete(f"user:{user_id}")
    
    return True


async def update_profile(db: AsyncSession, user_id: int, payload):
    user = await get_user(db, user_id)
    if not user:
        return None
    update_data = payload.model_dump(exclude_unset=True, exclude_none=True)
    for field, value in update_data.items():
        setattr(user, field, value)
    await db.commit()
    await db.refresh(user)
    
    # Invalidate caches
    await cache_service.delete(f"user:{user_id}")
    await cache_service.delete_pattern("users:list:*")
    
    return user


async def search_users(db: AsyncSession, query: str, skip: int = 0, limit: int = 20):
    search_filter = or_(
        User.email.ilike(f"%{query}%"),
        User.full_name.ilike(f"%{query}%"),
        User.username.ilike(f"%{query}%"),
    )
    result = await db.execute(
        select(User).where(search_filter).offset(skip).limit(limit)
    )
    return result.scalars().all()

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app.models.environment_variable import EnvironmentVariable
from app.services.cache import cache_service


def mask_secret_value(value: str) -> str:
    """Mask a secret value for display purposes."""
    if len(value) <= 8:
        return "****"
    return f"{value[:4]}{'*' * (len(value) - 8)}{value[-4:]}"


async def create_environment_variable(db: AsyncSession, payload) -> EnvironmentVariable:
    """Create a new environment variable."""
    env_var = EnvironmentVariable(
        key=payload.key,
        value=payload.value,
        description=payload.description,
        is_secret=payload.is_secret,
    )
    db.add(env_var)
    await db.commit()
    await db.refresh(env_var)
    
    # Invalidate environment variables cache
    await cache_service.delete_pattern("env_vars:*")
    
    return env_var


async def get_environment_variable(db: AsyncSession, env_var_id: int) -> Optional[EnvironmentVariable]:
    """Get an environment variable by ID."""
    result = await db.execute(select(EnvironmentVariable).where(EnvironmentVariable.id == env_var_id))
    return result.scalar_one_or_none()


async def get_environment_variable_by_key(db: AsyncSession, key: str) -> Optional[EnvironmentVariable]:
    """Get an environment variable by key."""
    result = await db.execute(select(EnvironmentVariable).where(EnvironmentVariable.key == key))
    return result.scalar_one_or_none()


async def get_environment_variables(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[EnvironmentVariable]:
    """Get all environment variables with pagination."""
    # Try cache first
    cache_key = f"env_vars:list:{skip}:{limit}"
    cached_vars = await cache_service.get(cache_key)
    if cached_vars:
        return cached_vars
    
    result = await db.execute(select(EnvironmentVariable).offset(skip).limit(limit))
    env_vars = result.scalars().all()
    
    # Cache the list
    env_vars_list = list(env_vars)
    await cache_service.set(cache_key, env_vars_list, ttl=300)
    
    return env_vars_list


async def update_environment_variable(db: AsyncSession, env_var_id: int, payload) -> Optional[EnvironmentVariable]:
    """Update an environment variable."""
    env_var = await get_environment_variable(db, env_var_id)
    if not env_var:
        return None
    
    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(env_var, field, value)
    
    await db.commit()
    await db.refresh(env_var)
    
    # Invalidate caches
    await cache_service.delete(f"env_var:{env_var_id}")
    await cache_service.delete_pattern("env_vars:*")
    
    return env_var


async def delete_environment_variable(db: AsyncSession, env_var_id: int) -> bool:
    """Delete an environment variable."""
    env_var = await get_environment_variable(db, env_var_id)
    if not env_var:
        return False
    
    await db.delete(env_var)
    await db.commit()
    
    # Invalidate caches
    await cache_service.delete(f"env_var:{env_var_id}")
    await cache_service.delete_pattern("env_vars:*")
    
    return True


async def get_all_environment_variables_dict(db: AsyncSession) -> dict:
    """Get all environment variables as a dictionary (for .env file generation)."""
    env_vars = await get_environment_variables(db, skip=0, limit=1000)
    return {env_var.key: env_var.value for env_var in env_vars}
import logging
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.environment_variable import EnvironmentVariable
from app.services.cache import cache_service
from app.core.tenant import TenantContext

logger = logging.getLogger("ai_bos")


def _mask_secret_value(value: str) -> str:
    """Mask a secret value, showing first 4 and last 4 characters."""
    if len(value) <= 8:
        return "*" * 8
    return value[:4] + "*" * (len(value) - 8) + value[-4:]


async def create_environment_variable(
    db: AsyncSession,
    payload,
    company_id: Optional[int] = None,
):
    """Create a new environment variable."""
    env_var = EnvironmentVariable(
        key=payload.key,
        value=payload.value,
        description=payload.description,
        is_secret=payload.is_secret,
        company_id=company_id or payload.company_id,
    )
    db.add(env_var)
    await db.commit()
    await db.refresh(env_var)

    # Invalidate caches
    await cache_service.delete_pattern("env_vars:list:*")
    await cache_service.delete("tenant:global_stats")

    return env_var


async def get_environment_variable(
    db: AsyncSession,
    env_var_id: int,
    company_id: Optional[int] = None,
):
    """Get an environment variable by ID, scoped to company."""
    cache_key = f"env_var:{env_var_id}"
    cached = await cache_service.get(cache_key)
    if cached:
        if company_id and cached.get("company_id") and cached.get("company_id") != company_id:
            return None
        return cached

    query = select(EnvironmentVariable).where(EnvironmentVariable.id == env_var_id)
    if company_id:
        query = query.where(EnvironmentVariable.company_id == company_id)

    result = await db.execute(query)
    env_var = result.scalar_one_or_none()

    if env_var:
        env_var_dict = env_var.__dict__.copy()
        if env_var.is_secret:
            env_var_dict["masked_value"] = _mask_secret_value(env_var.value)
        await cache_service.set(cache_key, env_var_dict, ttl=300)

    return env_var


async def get_environment_variable_by_key(
    db: AsyncSession,
    key: str,
    company_id: Optional[int] = None,
):
    """Get an environment variable by key, scoped to company."""
    query = select(EnvironmentVariable).where(EnvironmentVariable.key == key)
    if company_id:
        query = query.where(EnvironmentVariable.company_id == company_id)

    result = await db.execute(query)
    return result.scalar_one_or_none()


async def get_environment_variables(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 20,
    search: Optional[str] = None,
    company_id: Optional[int] = None,
) -> Tuple[List[EnvironmentVariable], int]:
    """Get environment variables with pagination, scoped to company."""
    cache_key = f"env_vars:list:{skip}:{limit}:{search}:{company_id}"
    cached = await cache_service.get(cache_key)
    if cached:
        return cached

    query = select(EnvironmentVariable)
    count_query = select(func.count(EnvironmentVariable.id))

    # Apply company scope
    if company_id:
        query = query.where(EnvironmentVariable.company_id == company_id)
        count_query = count_query.where(EnvironmentVariable.company_id == company_id)

    # Apply search filter
    if search:
        search_filter = or_(
            EnvironmentVariable.key.ilike(f"%{search}%"),
            EnvironmentVariable.description.ilike(f"%{search}%"),
        )
        query = query.where(search_filter)
        count_query = count_query.where(search_filter)

    # Get total count
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Apply pagination
    query = query.offset(skip).limit(limit).order_by(EnvironmentVariable.key.asc())
    result = await db.execute(query)
    env_vars = result.scalars().all()

    # Mask secret values
    for env_var in env_vars:
        if env_var.is_secret:
            env_var.masked_value = _mask_secret_value(env_var.value)

    result_data = (env_vars, total)
    await cache_service.set(cache_key, result_data, ttl=300)

    return result_data


async def update_environment_variable(
    db: AsyncSession,
    env_var_id: int,
    payload,
    company_id: Optional[int] = None,
):
    """Update an environment variable, scoped to company."""
    query = select(EnvironmentVariable).where(EnvironmentVariable.id == env_var_id)
    if company_id:
        query = query.where(EnvironmentVariable.company_id == company_id)

    result = await db.execute(query)
    env_var = result.scalar_one_or_none()
    if not env_var:
        return None

    update_data = payload.model_dump(exclude_unset=True, exclude_none=True)
    for field, value in update_data.items():
        setattr(env_var, field, value)

    await db.commit()
    await db.refresh(env_var)

    # Invalidate caches
    await cache_service.delete(f"env_var:{env_var_id}")
    await cache_service.delete_pattern("env_vars:list:*")
    await cache_service.delete("tenant:global_stats")

    return env_var


async def delete_environment_variable(
    db: AsyncSession,
    env_var_id: int,
    company_id: Optional[int] = None,
) -> bool:
    """Delete an environment variable, scoped to company."""
    query = select(EnvironmentVariable).where(EnvironmentVariable.id == env_var_id)
    if company_id:
        query = query.where(EnvironmentVariable.company_id == company_id)

    result = await db.execute(query)
    env_var = result.scalar_one_or_none()
    if not env_var:
        return False

    await db.delete(env_var)
    await db.commit()

    # Invalidate caches
    await cache_service.delete(f"env_var:{env_var_id}")
    await cache_service.delete_pattern("env_vars:list:*")
    await cache_service.delete("tenant:global_stats")

    return True


async def get_all_environment_variables_dict(
    db: AsyncSession,
    company_id: Optional[int] = None,
) -> Dict[str, str]:
    """Export all environment variables as a dictionary, scoped to company."""
    query = select(EnvironmentVariable)
    if company_id:
        query = query.where(EnvironmentVariable.company_id == company_id)

    result = await db.execute(query)
    env_vars = result.scalars().all()
    return {env_var.key: env_var.value for env_var in env_vars}
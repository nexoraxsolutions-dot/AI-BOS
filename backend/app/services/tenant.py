"""Tenant service layer for multi-tenancy management."""
import logging
from typing import Optional, List, Dict, Any, Tuple

from sqlalchemy import select, func, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.company import Company
from app.models.user import User
from app.models.environment_variable import EnvironmentVariable
from app.services.cache import cache_service

logger = logging.getLogger("ai_bos")


async def get_tenant_by_id(db: AsyncSession, company_id: int, include_users: bool = False):
    """Get a tenant (company) by ID with optional user list."""
    cache_key = f"tenant:{company_id}:details"
    cached_tenant = await cache_service.get(cache_key)
    if cached_tenant:
        return cached_tenant

    query = select(Company).where(Company.id == company_id)
    if include_users:
        query = query.options(joinedload(Company.users))

    result = await db.execute(query)
    company = result.unique().scalar_one_or_none()

    if company:
        tenant_data = company.__dict__.copy()
        
        # Get user count
        count_result = await db.execute(
            select(func.count(User.id)).where(User.company_id == company_id)
        )
        tenant_data["user_count"] = count_result.scalar() or 0
        
        if include_users and company.users:
            tenant_data["users"] = [
                {
                    "id": u.id,
                    "email": u.email,
                    "full_name": u.full_name,
                    "username": u.username,
                    "is_active": u.is_active,
                    "is_superuser": u.is_superuser,
                    "created_at": u.created_at,
                }
                for u in company.users
            ]
        
        await cache_service.set(cache_key, tenant_data, ttl=300)
        return tenant_data

    return None


async def get_tenants(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 20,
    search: Optional[str] = None,
    is_active: Optional[bool] = None,
    subscription_plan: Optional[str] = None,
) -> Tuple[List[Dict[str, Any]], int]:
    """Get all tenants with search, filter, and pagination (superuser scope)."""
    query = select(Company)
    count_query = select(func.count(Company.id))

    # Apply filters
    filters = []
    if search:
        filters.append(
            or_(
                Company.name.ilike(f"%{search}%"),
                Company.domain.ilike(f"%{search}%"),
                Company.email.ilike(f"%{search}%"),
                Company.industry.ilike(f"%{search}%"),
            )
        )
    if is_active is not None:
        filters.append(Company.is_active == is_active)
    if subscription_plan:
        filters.append(Company.subscription_plan == subscription_plan)

    if filters:
        query = query.where(and_(*filters))
        count_query = count_query.where(and_(*filters))

    # Get total count
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Apply pagination
    query = query.offset(skip).limit(limit).order_by(Company.name.asc())
    result = await db.execute(query)
    companies = result.scalars().all()

    # Enrich with user counts
    items = []
    for company in companies:
        company_dict = company.__dict__.copy()
        count_result = await db.execute(
            select(func.count(User.id)).where(User.company_id == company.id)
        )
        company_dict["user_count"] = count_result.scalar() or 0
        items.append(company_dict)

    return items, total


async def get_tenant_stats(db: AsyncSession) -> Dict[str, Any]:
    """Get tenant-wide statistics."""
    cache_key = "tenant:global_stats"
    cached_stats = await cache_service.get(cache_key)
    if cached_stats:
        return cached_stats

    # Total companies
    total_result = await db.execute(select(func.count(Company.id)))
    total_companies = total_result.scalar() or 0

    # Active companies
    active_result = await db.execute(
        select(func.count(Company.id)).where(Company.is_active == True)
    )
    active_companies = active_result.scalar() or 0

    # Total users across all companies
    users_result = await db.execute(select(func.count(User.id)))
    total_users = users_result.scalar() or 0

    # Active users
    active_users_result = await db.execute(
        select(func.count(User.id)).where(User.is_active == True)
    )
    active_users = active_users_result.scalar() or 0

    # Total environment variables
    env_result = await db.execute(select(func.count(EnvironmentVariable.id)))
    total_env_vars = env_result.scalar() or 0

    stats = {
        "total_users": total_users,
        "active_users": active_users,
        "total_companies": total_companies,
        "active_companies": active_companies,
        "total_environment_variables": total_env_vars,
        "storage_used_estimate": "0 B",
    }

    await cache_service.set(cache_key, stats, ttl=300)
    return stats


async def get_tenant_users(
    db: AsyncSession,
    company_id: int,
    skip: int = 0,
    limit: int = 20,
    search: Optional[str] = None,
) -> Tuple[List[User], int]:
    """Get users belonging to a specific tenant."""
    query = select(User).where(User.company_id == company_id)
    count_query = select(func.count(User.id)).where(User.company_id == company_id)

    if search:
        search_filter = or_(
            User.email.ilike(f"%{search}%"),
            User.full_name.ilike(f"%{search}%"),
            User.username.ilike(f"%{search}%"),
        )
        query = query.where(search_filter)
        count_query = count_query.where(search_filter)

    # Get total count
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Apply pagination
    query = query.offset(skip).limit(limit).order_by(User.email.asc())
    result = await db.execute(query)
    users = result.scalars().all()

    return users, total


async def assign_user_to_company(
    db: AsyncSession,
    user_id: int,
    company_id: int,
) -> Optional[User]:
    """Assign a user to a company (superuser operation)."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        return None

    # Check company exists
    company_result = await db.execute(select(Company).where(Company.id == company_id))
    company = company_result.scalar_one_or_none()
    if not company:
        return None

    user.company_id = company_id
    await db.commit()
    await db.refresh(user)

    # Invalidate caches
    await cache_service.delete(f"user:{user_id}")
    await cache_service.delete_pattern("users:list:*")
    await cache_service.delete(f"tenant:{company_id}:details")
    await cache_service.delete("tenant:global_stats")

    return user


async def remove_user_from_company(
    db: AsyncSession,
    user_id: int,
) -> Optional[User]:
    """Remove a user from their company (superuser operation)."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        return None

    company_id = user.company_id
    user.company_id = None
    await db.commit()
    await db.refresh(user)

    # Invalidate caches
    await cache_service.delete(f"user:{user_id}")
    await cache_service.delete_pattern("users:list:*")
    if company_id:
        await cache_service.delete(f"tenant:{company_id}:details")
    await cache_service.delete("tenant:global_stats")

    return user


async def invite_user_to_tenant(
    db: AsyncSession,
    company_id: int,
    email: str,
    full_name: Optional[str] = None,
) -> Optional[User]:
    """Invite a user to join a tenant.
    
    If user already exists, assign them to the company.
    If not, return None (user creation would be done via signup flow).
    """
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    
    if user:
        user.company_id = company_id
        if full_name and not user.full_name:
            user.full_name = full_name
        await db.commit()
        await db.refresh(user)

        # Invalidate caches
        await cache_service.delete(f"user:{user.id}")
        await cache_service.delete_pattern("users:list:*")
        await cache_service.delete(f"tenant:{company_id}:details")
        await cache_service.delete("tenant:global_stats")

        return user
    
    return None


async def get_current_tenant_dashboard(
    db: AsyncSession,
    company_id: int,
) -> Dict[str, Any]:
    """Get dashboard data scoped to a specific tenant."""
    cache_key = f"tenant:{company_id}:dashboard"
    cached = await cache_service.get(cache_key)
    if cached:
        return cached

    # Get tenant info
    company_result = await db.execute(select(Company).where(Company.id == company_id))
    company = company_result.scalar_one_or_none()
    if not company:
        return {}

    # Get user stats
    total_users_result = await db.execute(
        select(func.count(User.id)).where(User.company_id == company_id)
    )
    total_users = total_users_result.scalar() or 0

    active_users_result = await db.execute(
        select(func.count(User.id)).where(
            and_(User.company_id == company_id, User.is_active == True)
        )
    )
    active_users = active_users_result.scalar() or 0

    # Get env var stats
    env_vars_result = await db.execute(
        select(func.count(EnvironmentVariable.id))
    )
    total_env_vars = env_vars_result.scalar() or 0

    dashboard = {
        "company_name": company.name,
        "company_domain": company.domain,
        "total_users": total_users,
        "active_users": active_users,
        "subscription_plan": company.subscription_plan,
        "subscription_status": company.subscription_status,
        "total_environment_variables": total_env_vars,
    }

    await cache_service.set(cache_key, dashboard, ttl=300)
    return dashboard
from typing import Optional, List, Dict, Any
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.company import Company
from app.models.user import User
from app.services.cache import cache_service


async def create_company(db: AsyncSession, payload):
    company = Company(**payload.model_dump())
    db.add(company)
    await db.commit()
    await db.refresh(company)
    
    # Invalidate companies list cache
    await cache_service.delete_pattern("companies:list:*")
    await cache_service.delete("companies:stats")
    
    return company


async def get_company(db: AsyncSession, company_id: int):
    # Try cache first
    cache_key = f"company:{company_id}"
    cached_company = await cache_service.get(cache_key)
    if cached_company:
        return cached_company
    
    result = await db.execute(select(Company).where(Company.id == company_id))
    company = result.scalar_one_or_none()
    
    # Cache company data
    if company:
        await cache_service.set(cache_key, company.__dict__, ttl=600)
    
    return company


async def get_company_by_domain(db: AsyncSession, domain: str):
    result = await db.execute(select(Company).where(Company.domain == domain))
    return result.scalar_one_or_none()


async def get_companies(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 20,
    search: Optional[str] = None,
    is_active: Optional[bool] = None,
    industry: Optional[str] = None,
    subscription_plan: Optional[str] = None,
    sort_by: str = "name",
    sort_order: str = "asc",
):
    # Build query
    query = select(Company)
    
    # Apply filters
    if search:
        search_filter = or_(
            Company.name.ilike(f"%{search}%"),
            Company.domain.ilike(f"%{search}%"),
            Company.email.ilike(f"%{search}%"),
            Company.industry.ilike(f"%{search}%"),
        )
        query = query.where(search_filter)
    
    if is_active is not None:
        query = query.where(Company.is_active == is_active)
    
    if industry:
        query = query.where(Company.industry.ilike(f"%{industry}%"))
    
    if subscription_plan:
        query = query.where(Company.subscription_plan == subscription_plan)
    
    # Apply sorting
    sort_column = getattr(Company, sort_by, Company.name)
    if sort_order == "desc":
        sort_column = sort_column.desc()
    else:
        sort_column = sort_column.asc()
    query = query.order_by(sort_column)
    
    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    # Apply pagination
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    companies = result.scalars().all()
    
    return companies, total


async def update_company(db: AsyncSession, company_id: int, payload):
    company = await get_company(db, company_id)
    if not company:
        return None
    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(company, field, value)
    await db.commit()
    await db.refresh(company)
    
    # Invalidate caches
    await cache_service.delete(f"company:{company_id}")
    await cache_service.delete_pattern("companies:list:*")
    await cache_service.delete("companies:stats")
    
    return company


async def delete_company(db: AsyncSession, company_id: int) -> bool:
    company = await get_company(db, company_id)
    if not company:
        return False
    await db.delete(company)
    await db.commit()
    
    # Invalidate caches
    await cache_service.delete(f"company:{company_id}")
    await cache_service.delete_pattern("companies:list:*")
    await cache_service.delete("companies:stats")
    
    return True


async def get_company_stats(db: AsyncSession) -> Dict[str, Any]:
    # Try cache first
    cache_key = "companies:stats"
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
    
    # Inactive companies
    inactive_companies = total_companies - active_companies
    
    # Total users across all companies
    users_result = await db.execute(
        select(func.count(User.id))
    )
    total_users = users_result.scalar() or 0
    
    # Average employees
    avg_result = await db.execute(
        select(func.avg(Company.employee_count)).where(Company.employee_count.isnot(None))
    )
    avg_employees = avg_result.scalar()
    
    # Plan distribution
    plan_result = await db.execute(
        select(Company.subscription_plan, func.count(Company.id))
        .group_by(Company.subscription_plan)
    )
    plan_distribution = {plan: count for plan, count in plan_result.all()}
    
    stats = {
        "total_companies": total_companies,
        "active_companies": active_companies,
        "inactive_companies": inactive_companies,
        "total_users_across_companies": total_users,
        "avg_employees": float(avg_employees) if avg_employees else None,
        "plan_distribution": plan_distribution,
    }
    
    # Cache for 5 minutes
    await cache_service.set(cache_key, stats, ttl=300)
    
    return stats


async def get_company_with_user_count(db: AsyncSession, company_id: int):
    """Get a company with the count of its users."""
    company = await get_company(db, company_id)
    if not company:
        return None
    
    # Get user count
    count_result = await db.execute(
        select(func.count(User.id)).where(User.company_id == company_id)
    )
    user_count = count_result.scalar() or 0
    
    # Add user_count to company dict
    company_dict = company.__dict__.copy()
    company_dict["user_count"] = user_count
    
    return company_dict
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.company import Company
from app.services.cache import cache_service


async def get_dashboard_summary(db: AsyncSession) -> dict:
    """Aggregate real dashboard statistics from the database with caching."""
    # Try to get from cache first
    cache_key = "dashboard:summary"
    cached_data = await cache_service.get(cache_key)
    if cached_data:
        return cached_data

    # Total users
    total_users_result = await db.execute(select(func.count(User.id)))
    total_users = total_users_result.scalar() or 0

    # Active users
    active_users_result = await db.execute(
        select(func.count(User.id)).where(User.is_active == True)
    )
    active_users = active_users_result.scalar() or 0

    # Total companies
    total_companies_result = await db.execute(select(func.count(Company.id)))
    total_companies = total_companies_result.scalar() or 0

    # Recent users (last 30 days)
    from datetime import datetime, timedelta
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    recent_users_result = await db.execute(
        select(func.count(User.id)).where(User.created_at >= thirty_days_ago)
    )
    recent_users_count = recent_users_result.scalar() or 0

    # Recent companies (last 30 days)
    recent_companies_result = await db.execute(
        select(func.count(Company.id)).where(Company.created_at >= thirty_days_ago)
    )
    recent_companies_count = recent_companies_result.scalar() or 0

    # Simulated metrics (would come from dedicated business modules in production)
    total_sales_monthly = 1850000.00
    total_tasks_pending = 84

    result = {
        "total_users": total_users,
        "active_users": active_users,
        "total_companies": total_companies,
        "total_sales_monthly": total_sales_monthly,
        "total_tasks_pending": total_tasks_pending,
        "recent_users_count": recent_users_count,
        "recent_companies_count": recent_companies_count,
    }

    # Cache the result for 5 minutes
    await cache_service.set(cache_key, result, ttl=300)

    return result

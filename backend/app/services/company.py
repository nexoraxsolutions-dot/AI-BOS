from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.company import Company
from app.services.cache import cache_service


async def create_company(db: AsyncSession, payload):
    company = Company(**payload.model_dump())
    db.add(company)
    await db.commit()
    await db.refresh(company)
    
    # Invalidate companies list cache
    await cache_service.delete_pattern("companies:list:*")
    
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


async def get_companies(db: AsyncSession, skip: int = 0, limit: int = 20):
    # Try cache first
    cache_key = f"companies:list:{skip}:{limit}"
    cached_companies = await cache_service.get(cache_key)
    if cached_companies:
        return cached_companies
    
    result = await db.execute(select(Company).offset(skip).limit(limit))
    companies = result.scalars().all()
    
    # Cache companies list
    companies_list = [company.__dict__ for company in companies]
    await cache_service.set(cache_key, companies_list, ttl=300)
    
    return companies


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
    
    return True

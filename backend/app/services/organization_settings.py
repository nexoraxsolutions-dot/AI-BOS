from typing import Optional, Dict, Any
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.organization_settings import OrganizationSettings
from app.services.cache import cache_service


async def get_organization_settings(db: AsyncSession, company_id: int) -> Optional[OrganizationSettings]:
    """Get organization settings for a company."""
    # Try cache first
    cache_key = f"org_settings:{company_id}"
    cached_settings = await cache_service.get(cache_key)
    if cached_settings:
        return cached_settings
    
    # Query database
    result = await db.execute(
        select(OrganizationSettings).where(OrganizationSettings.company_id == company_id)
    )
    settings = result.scalar_one_or_none()
    
    # Cache settings
    if settings:
        await cache_service.set(cache_key, settings.__dict__, ttl=600)
    
    return settings


async def create_organization_settings(db: AsyncSession, company_id: int, settings_data: Dict[str, Any]) -> OrganizationSettings:
    """Create organization settings for a company."""
    # Check if settings already exist
    existing = await get_organization_settings(db, company_id)
    if existing:
        raise ValueError(f"Organization settings already exist for company {company_id}")
    
    # Create new settings
    settings = OrganizationSettings(company_id=company_id, **settings_data)
    db.add(settings)
    await db.commit()
    await db.refresh(settings)
    
    # Invalidate cache
    await cache_service.delete(f"org_settings:{company_id}")
    
    return settings


async def update_organization_settings(db: AsyncSession, company_id: int, settings_data: Dict[str, Any]) -> Optional[OrganizationSettings]:
    """Update organization settings for a company."""
    # Get existing settings
    settings = await get_organization_settings(db, company_id)
    if not settings:
        # Create if doesn't exist
        return await create_organization_settings(db, company_id, settings_data)
    
    # Update fields
    update_data = {k: v for k, v in settings_data.items() if v is not None}
    for field, value in update_data.items():
        if hasattr(settings, field):
            setattr(settings, field, value)
    
    await db.commit()
    await db.refresh(settings)
    
    # Invalidate cache
    await cache_service.delete(f"org_settings:{company_id}")
    
    return settings


async def delete_organization_settings(db: AsyncSession, company_id: int) -> bool:
    """Delete organization settings for a company."""
    settings = await get_organization_settings(db, company_id)
    if not settings:
        return False
    
    await db.delete(settings)
    await db.commit()
    
    # Invalidate cache
    await cache_service.delete(f"org_settings:{company_id}")
    
    return True


async def get_or_create_default_settings(db: AsyncSession, company_id: int) -> OrganizationSettings:
    """Get existing settings or create default settings for a company."""
    settings = await get_organization_settings(db, company_id)
    if settings:
        return settings
    
    # Create default settings
    default_settings = OrganizationSettings(company_id=company_id)
    db.add(default_settings)
    await db.commit()
    await db.refresh(default_settings)
    
    return default_settings
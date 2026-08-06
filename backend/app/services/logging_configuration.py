"""Logging Configuration Service.

Provides CRUD operations for logging configuration settings.
"""
from typing import Optional, Dict, Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.logging_configuration import LoggingConfiguration
from app.services.cache import cache_service


async def get_logging_configuration(db: AsyncSession, company_id: int) -> Optional[LoggingConfiguration]:
    """Get logging configuration for a company.

    Args:
        db: Database session
        company_id: Company ID

    Returns:
        LoggingConfiguration instance or None
    """
    # Try cache first
    cache_key = f"logging_config:{company_id}"
    cached_config = await cache_service.get(cache_key)
    if cached_config:
        return cached_config

    # Query database
    result = await db.execute(
        select(LoggingConfiguration).where(LoggingConfiguration.company_id == company_id)
    )
    config = result.scalar_one_or_none()

    # Cache config
    if config:
        await cache_service.set(cache_key, config.__dict__, ttl=600)

    return config


async def create_logging_configuration(
    db: AsyncSession, company_id: int, config_data: Dict[str, Any]
) -> LoggingConfiguration:
    """Create logging configuration for a company.

    Args:
        db: Database session
        company_id: Company ID
        config_data: Configuration data dictionary

    Returns:
        Created LoggingConfiguration instance

    Raises:
        ValueError: If configuration already exists for the company
    """
    # Check if config already exists
    existing = await get_logging_configuration(db, company_id)
    if existing:
        raise ValueError(f"Logging configuration already exists for company {company_id}")

    # Create new config
    config = LoggingConfiguration(company_id=company_id, **config_data)
    db.add(config)
    await db.commit()
    await db.refresh(config)

    # Invalidate cache
    await cache_service.delete(f"logging_config:{company_id}")

    return config


async def update_logging_configuration(
    db: AsyncSession, company_id: int, config_data: Dict[str, Any]
) -> Optional[LoggingConfiguration]:
    """Update logging configuration for a company.

    Args:
        db: Database session
        company_id: Company ID
        config_data: Configuration data dictionary (only non-None values will be updated)

    Returns:
        Updated LoggingConfiguration instance or None if not found
    """
    # Get existing config
    config = await get_logging_configuration(db, company_id)
    if not config:
        # Create if doesn't exist
        return await create_logging_configuration(db, company_id, config_data)

    # Update fields
    update_data = {k: v for k, v in config_data.items() if v is not None}
    for field, value in update_data.items():
        if hasattr(config, field):
            setattr(config, field, value)

    await db.commit()
    await db.refresh(config)

    # Invalidate cache
    await cache_service.delete(f"logging_config:{company_id}")

    return config


async def delete_logging_configuration(db: AsyncSession, company_id: int) -> bool:
    """Delete logging configuration for a company.

    Args:
        db: Database session
        company_id: Company ID

    Returns:
        True if deleted, False if not found
    """
    config = await get_logging_configuration(db, company_id)
    if not config:
        return False

    await db.delete(config)
    await db.commit()

    # Invalidate cache
    await cache_service.delete(f"logging_config:{company_id}")

    return True


async def get_or_create_default_config(db: AsyncSession, company_id: int) -> LoggingConfiguration:
    """Get existing config or create default configuration for a company.

    Args:
        db: Database session
        company_id: Company ID

    Returns:
        LoggingConfiguration instance
    """
    config = await get_logging_configuration(db, company_id)
    if config:
        return config

    # Create default config
    default_config = LoggingConfiguration(company_id=company_id)
    db.add(default_config)
    await db.commit()
    await db.refresh(default_config)

    return default_config

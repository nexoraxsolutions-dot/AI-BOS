"""Logging Configuration API Endpoints.

Provides:
- GET /logging-config/ - Get logging configuration for current company
- POST /logging-config/ - Create logging configuration (superuser only)
- PUT /logging-config/ - Update logging configuration (superuser only)
- DELETE /logging-config/ - Delete logging configuration (superuser only)
"""
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.request import get_client_ip, get_user_agent
from app.db.dependencies import get_async_session
from app.schemas import logging_configuration as logging_config_schema
from app.services import logging_configuration as logging_config_service
from app.services.audit_log import create_audit_log
from app.core.security import get_current_active_user, require_superuser

router = APIRouter()


@router.get("/", response_model=logging_config_schema.LoggingConfigurationOut)
async def get_logging_configuration(
    request: Request,
    db: AsyncSession = Depends(get_async_session),
    current_user=Depends(get_current_active_user),
):
    """Get logging configuration for the current user's company.

    Creates default configuration if none exists.
    """
    company_id = current_user.company_id
    if not company_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User is not associated with any company"
        )

    config = await logging_config_service.get_or_create_default_config(db, company_id)
    return config


@router.post(
    "/",
    response_model=logging_config_schema.LoggingConfigurationOut,
    status_code=status.HTTP_201_CREATED
)
async def create_logging_configuration(
    request: Request,
    payload: logging_config_schema.LoggingConfigurationCreate,
    db: AsyncSession = Depends(get_async_session),
    current_user=Depends(require_superuser),
):
    """Create logging configuration for a company (superuser only)."""
    try:
        config = await logging_config_service.create_logging_configuration(
            db, payload.company_id, payload.model_dump(exclude={"company_id"})
        )
        # Log configuration creation
        await create_audit_log(
            db,
            action="create",
            resource_type="logging_configuration",
            resource_id=config.id,
            user_id=current_user.id,
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request),
            details={"company_id": payload.company_id, "created_by": current_user.email},
        )
        return config
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.put("/", response_model=logging_config_schema.LoggingConfigurationOut)
async def update_logging_configuration(
    request: Request,
    payload: logging_config_schema.LoggingConfigurationUpdate,
    db: AsyncSession = Depends(get_async_session),
    current_user=Depends(require_superuser),
):
    """Update logging configuration for the current user's company (superuser only)."""
    company_id = current_user.company_id
    if not company_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User is not associated with any company"
        )

    config = await logging_config_service.update_logging_configuration(
        db, company_id, payload.model_dump(exclude_none=True)
    )

    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Logging configuration not found"
        )

    # Log configuration update
    await create_audit_log(
        db,
        action="update",
        resource_type="logging_configuration",
        resource_id=config.id,
        user_id=current_user.id,
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request),
        details={
            "company_id": company_id,
            "updated_by": current_user.email,
            "updated_fields": payload.model_dump(exclude_none=True)
        },
    )

    return config


@router.delete("/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_logging_configuration(
    request: Request,
    db: AsyncSession = Depends(get_async_session),
    current_user=Depends(require_superuser),
):
    """Delete logging configuration for the current user's company (superuser only)."""
    company_id = current_user.company_id
    if not company_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User is not associated with any company"
        )

    deleted = await logging_config_service.delete_logging_configuration(db, company_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Logging configuration not found"
        )

    # Log configuration deletion
    await create_audit_log(
        db,
        action="delete",
        resource_type="logging_configuration",
        resource_id=company_id,
        user_id=current_user.id,
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request),
        details={"company_id": company_id, "deleted_by": current_user.email},
    )

    return None

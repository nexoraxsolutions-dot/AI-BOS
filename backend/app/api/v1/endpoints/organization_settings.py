from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.core.request import get_client_ip, get_user_agent
from app.db.dependencies import get_async_session
from app.schemas import organization_settings as org_settings_schema
from app.services import organization_settings as org_settings_service
from app.services.audit_log import create_audit_log
from app.core.security import get_current_active_user, require_superuser

router = APIRouter()


@router.get("/", response_model=org_settings_schema.OrganizationSettingsOut)
async def get_organization_settings(
    request: Request,
    db: AsyncSession = Depends(get_async_session),
    current_user=Depends(get_current_active_user),
):
    """Get organization settings for the current user's company."""
    company_id = current_user.company_id
    if not company_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User is not associated with any company"
        )
    
    settings = await org_settings_service.get_or_create_default_settings(db, company_id)
    return settings


@router.post("/", response_model=org_settings_schema.OrganizationSettingsOut, status_code=status.HTTP_201_CREATED)
async def create_organization_settings(
    request: Request,
    payload: org_settings_schema.OrganizationSettingsCreate,
    db: AsyncSession = Depends(get_async_session),
    current_user=Depends(require_superuser),
):
    """Create organization settings for a company (superuser only)."""
    try:
        settings = await org_settings_service.create_organization_settings(
            db, payload.company_id, payload.model_dump(exclude={'company_id'})
        )
        # Log settings creation
        await create_audit_log(
            db,
            action="create",
            resource_type="organization_settings",
            resource_id=settings.id,
            user_id=current_user.id,
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request),
            details={"company_id": payload.company_id, "created_by": current_user.email},
        )
        return settings
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.put("/", response_model=org_settings_schema.OrganizationSettingsOut)
async def update_organization_settings(
    request: Request,
    payload: org_settings_schema.OrganizationSettingsUpdate,
    db: AsyncSession = Depends(get_async_session),
    current_user=Depends(get_current_active_user),
):
    """Update organization settings for the current user's company."""
    company_id = current_user.company_id
    if not company_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User is not associated with any company"
        )
    
    # Non-superusers can only update certain fields
    if not current_user.is_superuser:
        # Allow users to update their own company settings, but restrict sensitive fields
        allowed_fields = {
            'timezone', 'date_format', 'time_format', 'language', 'currency',
            'primary_color', 'logo_url', 'custom_css'
        }
        update_data = payload.model_dump(exclude_none=True)
        restricted_fields = set(update_data.keys()) - allowed_fields
        if restricted_fields:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"You don't have permission to update these fields: {', '.join(restricted_fields)}"
            )
    
    settings = await org_settings_service.update_organization_settings(
        db, company_id, payload.model_dump(exclude_none=True)
    )
    
    if not settings:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization settings not found"
        )
    
    # Log settings update
    await create_audit_log(
        db,
        action="update",
        resource_type="organization_settings",
        resource_id=settings.id,
        user_id=current_user.id,
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request),
        details={
            "company_id": company_id,
            "updated_by": current_user.email,
            "updated_fields": payload.model_dump(exclude_none=True)
        },
    )
    
    return settings


@router.put("/{company_id}", response_model=org_settings_schema.OrganizationSettingsOut)
async def update_company_organization_settings(
    request: Request,
    company_id: int,
    payload: org_settings_schema.OrganizationSettingsUpdate,
    db: AsyncSession = Depends(get_async_session),
    current_user=Depends(require_superuser),
):
    """Update organization settings for a specific company (superuser only)."""
    settings = await org_settings_service.update_organization_settings(
        db, company_id, payload.model_dump(exclude_none=True)
    )
    
    if not settings:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization settings not found"
        )
    
    # Log settings update
    await create_audit_log(
        db,
        action="update",
        resource_type="organization_settings",
        resource_id=settings.id,
        user_id=current_user.id,
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request),
        details={
            "company_id": company_id,
            "updated_by": current_user.email,
            "updated_fields": payload.model_dump(exclude_none=True)
        },
    )
    
    return settings


@router.delete("/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_organization_settings(
    request: Request,
    db: AsyncSession = Depends(get_async_session),
    current_user=Depends(require_superuser),
):
    """Delete organization settings for the current user's company (superuser only)."""
    company_id = current_user.company_id
    if not company_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User is not associated with any company"
        )
    
    deleted = await org_settings_service.delete_organization_settings(db, company_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization settings not found"
        )
    
    # Log settings deletion
    await create_audit_log(
        db,
        action="delete",
        resource_type="organization_settings",
        resource_id=company_id,
        user_id=current_user.id,
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request),
        details={"company_id": company_id, "deleted_by": current_user.email},
    )
    
    return None


@router.get("/defaults", response_model=org_settings_schema.OrganizationSettingsOut)
async def get_default_organization_settings(
    db: AsyncSession = Depends(get_async_session),
    current_user=Depends(get_current_active_user),
):
    """Get default organization settings template."""
    # Return default settings without company association
    return org_settings_schema.OrganizationSettingsOut(
        id=0,
        company_id=0,
        timezone="UTC",
        date_format="YYYY-MM-DD",
        time_format="24h",
        language="en",
        currency="USD",
        password_min_length=8,
        password_require_uppercase=True,
        password_require_lowercase=True,
        password_require_numbers=True,
        password_require_special_chars=True,
        password_expiry_days=90,
        session_timeout_minutes=60,
        enforce_2fa=False,
        max_login_attempts=5,
        email_notifications_enabled=True,
        notify_on_user_creation=True,
        notify_on_user_deletion=True,
        notify_on_password_reset=True,
        notify_on_security_alerts=True,
        notify_on_subscription_changes=True,
        primary_color="#06b6d4",
        logo_url=None,
        custom_css=None,
        enable_user_registration=True,
        enable_api_access=True,
        enable_audit_logs=True,
        enable_data_export=True,
        custom_settings={},
        created_at=None,
        updated_at=None,
    )
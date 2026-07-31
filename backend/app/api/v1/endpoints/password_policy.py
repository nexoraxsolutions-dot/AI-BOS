from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.request import get_client_ip, get_user_agent
from app.db.dependencies import get_async_session
from app.schemas import password_policy as password_policy_schema
from app.services import password_policy as password_policy_service
from app.services.audit_log import create_audit_log
from app.core.security import get_current_active_user, require_superuser

router = APIRouter()


@router.get("/", response_model=password_policy_schema.PasswordPolicyResponse)
async def get_password_policy(
    request: Request,
    db: AsyncSession = Depends(get_async_session),
    current_user=Depends(get_current_active_user),
):
    """Get password policy for the current user's company."""
    company_id = current_user.company_id
    if not company_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User is not associated with any company"
        )
    
    # Get organization settings
    from app.services.organization_settings import get_organization_settings
    settings = await get_organization_settings(db, company_id)
    
    if not settings:
        # Return default policy
        policy = password_policy_service.PasswordPolicyService.get_default_policy()
    else:
        policy = {
            "min_length": settings.password_min_length,
            "require_uppercase": settings.password_require_uppercase,
            "require_lowercase": settings.password_require_lowercase,
            "require_numbers": settings.password_require_numbers,
            "require_special_chars": settings.password_require_special_chars,
            "expiry_days": settings.password_expiry_days,
        }
    
    # Get requirements for display
    requirements = password_policy_service.PasswordPolicyService.get_password_requirements_display(
        company_id, policy
    )
    
    return password_policy_schema.PasswordPolicyResponse(
        min_length=policy["min_length"],
        require_uppercase=policy["require_uppercase"],
        require_lowercase=policy["require_lowercase"],
        require_numbers=policy["require_numbers"],
        require_special_chars=policy["require_special_chars"],
        expiry_days=policy["expiry_days"],
        requirements=requirements,
    )


@router.post("/validate", response_model=password_policy_schema.PasswordValidationResponse)
async def validate_password(
    request: Request,
    payload: password_policy_schema.PasswordValidationRequest,
    db: AsyncSession = Depends(get_async_session),
    current_user=Depends(get_current_active_user),
):
    """Validate a password against the current organization's policy."""
    company_id = current_user.company_id
    if not company_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User is not associated with any company"
        )
    
    # Get policy
    from app.services.organization_settings import get_organization_settings
    settings = await get_organization_settings(db, company_id)
    
    if not settings:
        policy = password_policy_service.PasswordPolicyService.get_default_policy()
    else:
        policy = {
            "min_length": settings.password_min_length,
            "require_uppercase": settings.password_require_uppercase,
            "require_lowercase": settings.password_require_lowercase,
            "require_numbers": settings.password_require_numbers,
            "require_special_chars": settings.password_require_special_chars,
        }
    
    # Get requirements
    requirements = password_policy_service.PasswordPolicyService.get_password_requirements_display(
        company_id, policy
    )
    
    # Check password against requirements
    requirement_status = password_policy_service.PasswordPolicyService.check_password_against_requirements(
        payload.password, requirements
    )

    # Update requirements with status
    updated_requirements = []
    for req in requirements:
        req_copy = req.copy()
        req_copy["met"] = requirement_status.get(req["id"], False)
        updated_requirements.append(req_copy)
    
    # Validate password
    try:
        password_policy_service.PasswordPolicyService.validate_password_against_policy(
            payload.password, policy
        )
        
        # Check if it's a common password
        from app.core.password_policy import is_common_password
        if is_common_password(payload.password):
            return password_policy_schema.PasswordValidationResponse(
                valid=False,
                errors=["Password is too common. Please choose a more unique password"],
                requirements=updated_requirements,
            )
        
        return password_policy_schema.PasswordValidationResponse(
            valid=True,
            requirements=updated_requirements,
        )
    except Exception as e:
        # Handle PasswordValidationError
        from app.core.password_policy import PasswordValidationError
        if isinstance(e, PasswordValidationError):
            return password_policy_schema.PasswordValidationResponse(
                valid=False,
                errors=e.errors,
                requirements=updated_requirements,
            )
        raise


@router.get("/defaults", response_model=password_policy_schema.PasswordPolicyResponse)
async def get_default_password_policy(
    current_user=Depends(get_current_active_user),
):
    """Get default password policy template."""
    policy = password_policy_service.PasswordPolicyService.get_default_policy()
    requirements = password_policy_service.PasswordPolicyService.get_password_requirements_display(
        current_user.company_id or 0, policy
    )
    
    return password_policy_schema.PasswordPolicyResponse(
        min_length=policy["min_length"],
        require_uppercase=policy["require_uppercase"],
        require_lowercase=policy["require_lowercase"],
        require_numbers=policy["require_numbers"],
        require_special_chars=policy["require_special_chars"],
        expiry_days=policy["expiry_days"],
        requirements=requirements,
    )


@router.put("/", response_model=password_policy_schema.PasswordPolicyOut)
async def update_password_policy(
    request: Request,
    payload: password_policy_schema.PasswordPolicyUpdate,
    db: AsyncSession = Depends(get_async_session),
    current_user=Depends(require_superuser),
):
    """Update password policy for the current user's company (superuser only)."""
    company_id = current_user.company_id
    if not company_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User is not associated with any company"
        )
    
    # Get current settings
    from app.services.organization_settings import get_organization_settings, update_organization_settings
    
    settings = await get_organization_settings(db, company_id)
    if not settings:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization settings not found"
        )
    
    # Map password policy fields to organization settings fields
    update_data = payload.model_dump(exclude_none=True)
    field_mapping = {
        "min_length": "password_min_length",
        "require_uppercase": "password_require_uppercase",
        "require_lowercase": "password_require_lowercase",
        "require_numbers": "password_require_numbers",
        "require_special_chars": "password_require_special_chars",
        "expiry_days": "password_expiry_days",
    }
    
    mapped_update = {}
    for key, value in update_data.items():
        if key in field_mapping:
            mapped_update[field_mapping[key]] = value
    
    updated_settings = await update_organization_settings(db, company_id, mapped_update)
    
    # Log policy update
    await create_audit_log(
        db,
        action="update",
        resource_type="password_policy",
        resource_id=company_id,
        user_id=current_user.id,
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request),
        details={
            "company_id": company_id,
            "updated_by": current_user.email,
            "updated_fields": update_data,
        },
    )
    
    return password_policy_schema.PasswordPolicyOut(
        company_id=company_id,
        min_length=updated_settings.password_min_length,
        require_uppercase=updated_settings.password_require_uppercase,
        require_lowercase=updated_settings.password_require_lowercase,
        require_numbers=updated_settings.password_require_numbers,
        require_special_chars=updated_settings.password_require_special_chars,
        expiry_days=updated_settings.password_expiry_days,
    )


@router.put("/{company_id}", response_model=password_policy_schema.PasswordPolicyOut)
async def update_company_password_policy(
    request: Request,
    company_id: int,
    payload: password_policy_schema.PasswordPolicyUpdate,
    db: AsyncSession = Depends(get_async_session),
    current_user=Depends(require_superuser),
):
    """Update password policy for a specific company (superuser only)."""
    # Get current settings
    from app.services.organization_settings import get_organization_settings, update_organization_settings
    
    settings = await get_organization_settings(db, company_id)
    if not settings:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization settings not found"
        )
    
    # Map password policy fields to organization settings fields
    update_data = payload.model_dump(exclude_none=True)
    field_mapping = {
        "min_length": "password_min_length",
        "require_uppercase": "password_require_uppercase",
        "require_lowercase": "password_require_lowercase",
        "require_numbers": "password_require_numbers",
        "require_special_chars": "password_require_special_chars",
        "expiry_days": "password_expiry_days",
    }
    
    mapped_update = {}
    for key, value in update_data.items():
        if key in field_mapping:
            mapped_update[field_mapping[key]] = value
    
    updated_settings = await update_organization_settings(db, company_id, mapped_update)
    
    # Log policy update
    await create_audit_log(
        db,
        action="update",
        resource_type="password_policy",
        resource_id=company_id,
        user_id=current_user.id,
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request),
        details={
            "company_id": company_id,
            "updated_by": current_user.email,
            "updated_fields": update_data,
        },
    )
    
    return password_policy_schema.PasswordPolicyOut(
        company_id=company_id,
        min_length=updated_settings.password_min_length,
        require_uppercase=updated_settings.password_require_uppercase,
        require_lowercase=updated_settings.password_require_lowercase,
        require_numbers=updated_settings.password_require_numbers,
        require_special_chars=updated_settings.password_require_special_chars,
        expiry_days=updated_settings.password_expiry_days,
    )
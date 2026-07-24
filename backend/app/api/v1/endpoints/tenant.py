"""Tenant management REST API endpoints.

Provides multi-tenancy management capabilities:
- Tenant listing and details (superuser)
- Tenant user management
- Tenant dashboard (scoped to current user's company)
- User assignment to tenants
"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app.db.dependencies import get_async_session
from app.schemas import tenant as tenant_schema
from app.services import tenant as tenant_service
from app.core.security import get_current_active_user, require_superuser, get_current_user
from app.core.tenant import (
    TenantContext,
    get_tenant_context,
    require_tenant_membership,
)

router = APIRouter()


@router.get("/stats", response_model=tenant_schema.TenantStats)
async def get_tenant_stats(
    db: AsyncSession = Depends(get_async_session),
    current_user=Depends(require_superuser),
):
    """Get global tenant statistics (superuser only)."""
    return await tenant_service.get_tenant_stats(db)


@router.get("/my-tenant", response_model=tenant_schema.TenantDetail)
async def get_my_tenant(
    db: AsyncSession = Depends(get_async_session),
    tenant: TenantContext = Depends(require_tenant_membership),
):
    """Get the current user's tenant details with user list."""
    if tenant.is_superuser and not tenant.company_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Superuser has no company assigned. Use /api/v1/tenants/ to list all tenants.",
        )
    
    company_data = await tenant_service.get_tenant_by_id(
        db, tenant.company_id, include_users=True
    )
    if not company_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found",
        )
    return company_data


@router.get("/my-tenant/dashboard")
async def get_my_tenant_dashboard(
    db: AsyncSession = Depends(get_async_session),
    tenant: TenantContext = Depends(require_tenant_membership),
):
    """Get dashboard data scoped to current user's tenant."""
    if not tenant.company_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No company assigned to your account",
        )
    return await tenant_service.get_current_tenant_dashboard(db, tenant.company_id)


@router.get("/", response_model=tenant_schema.TenantListResponse)
async def list_tenants(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=100, description="Number of records to return"),
    search: Optional[str] = Query(None, description="Search by name, domain, email, or industry"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    subscription_plan: Optional[str] = Query(None, description="Filter by subscription plan"),
    db: AsyncSession = Depends(get_async_session),
    current_user=Depends(require_superuser),
):
    """List all tenants with search and filtering (superuser only)."""
    items, total = await tenant_service.get_tenants(
        db,
        skip=skip,
        limit=limit,
        search=search,
        is_active=is_active,
        subscription_plan=subscription_plan,
    )
    return tenant_schema.TenantListResponse(
        items=items,
        total=total,
        page=(skip // limit) + 1,
        page_size=limit,
    )


@router.post("/assign", status_code=status.HTTP_200_OK)
async def assign_user_to_company(
    payload: tenant_schema.UserCompanyAssignment,
    db: AsyncSession = Depends(get_async_session),
    current_user=Depends(require_superuser),
):
    """Assign a user to a company (superuser only)."""
    user = await tenant_service.assign_user_to_company(
        db, payload.user_id, payload.company_id
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User or company not found",
        )
    return {
        "message": f"User {user.email} assigned to company ID {payload.company_id}",
        "user_id": user.id,
        "company_id": payload.company_id,
    }


@router.post("/remove", status_code=status.HTTP_200_OK)
async def remove_user_from_company(
    user_id: int = Query(..., description="User ID to remove from their company"),
    db: AsyncSession = Depends(get_async_session),
    current_user=Depends(require_superuser),
):
    """Remove a user from their company assignment (superuser only)."""
    user = await tenant_service.remove_user_from_company(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return {
        "message": f"User {user.email} removed from their company",
        "user_id": user.id,
    }


@router.post("/invite", response_model=tenant_schema.TenantInviteResponse)
async def invite_user_to_tenant(
    payload: tenant_schema.TenantInviteRequest,
    db: AsyncSession = Depends(get_async_session),
    current_user=Depends(require_superuser),
):
    """Invite a user to join a tenant (superuser only)."""
    # Find a company to assign (requires company_id in payload or default)
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Direct invite flow not yet implemented. Use POST /api/v1/tenants/assign instead.",
    )


@router.get("/my-tenant/users", response_model=List[tenant_schema.TenantUserSummary])
async def get_my_tenant_users(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=100, description="Number of records to return"),
    search: Optional[str] = Query(None, description="Search by email, name, or username"),
    db: AsyncSession = Depends(get_async_session),
    tenant: TenantContext = Depends(require_tenant_membership),
):
    """Get users within the current user's tenant."""
    if not tenant.company_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No company assigned",
        )
    users, total = await tenant_service.get_tenant_users(
        db, tenant.company_id, skip=skip, limit=limit, search=search
    )
    return users  # Return only the users list, not the tuple


@router.get("/{company_id}", response_model=tenant_schema.TenantDetail)
async def get_tenant_detail(
    company_id: int,
    include_users: bool = Query(True, description="Include user list"),
    db: AsyncSession = Depends(get_async_session),
    current_user=Depends(require_superuser),
):
    """Get detailed tenant information (superuser only)."""
    company_data = await tenant_service.get_tenant_by_id(
        db, company_id, include_users=include_users
    )
    if not company_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found",
        )
    return company_data


@router.get("/{company_id}/users", response_model=List[tenant_schema.TenantUserSummary])
async def list_tenant_users(
    company_id: int,
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=100, description="Number of records to return"),
    search: Optional[str] = Query(None, description="Search by email, name, or username"),
    db: AsyncSession = Depends(get_async_session),
    current_user=Depends(require_superuser),
):
    """Get users belonging to a tenant (superuser only)."""
    users, total = await tenant_service.get_tenant_users(
        db, company_id, skip=skip, limit=limit, search=search
    )
    return users  # Return only the users list, not the tuple

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app.core.request import get_client_ip, get_user_agent
from app.db.dependencies import get_async_session
from app.schemas import company as company_schema
from app.services import company as company_service
from app.services.audit_log import create_audit_log
from app.core.security import get_current_active_user, require_superuser

router = APIRouter()


@router.post("/", response_model=company_schema.CompanyOut, status_code=status.HTTP_201_CREATED)
async def create_company(
    request: Request,
    payload: company_schema.CompanyCreate,
    db: AsyncSession = Depends(get_async_session),
    current_user=Depends(require_superuser),
):
    company = await company_service.create_company(db, payload)
    # Log company creation
    await create_audit_log(
        db,
        action="create",
        resource_type="company",
        resource_id=company.id,
        user_id=current_user.id,
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request),
        details={"company_name": company.name, "domain": company.domain, "created_by": current_user.email},
    )
    return company


@router.get("/", response_model=company_schema.CompanyListResponse)
async def list_companies(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=100, description="Number of records to return"),
    search: Optional[str] = Query(None, description="Search by name, domain, email, or industry"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    industry: Optional[str] = Query(None, description="Filter by industry"),
    subscription_plan: Optional[str] = Query(None, description="Filter by subscription plan"),
    sort_by: str = Query("name", description="Sort field (name, domain, created_at, employee_count)"),
    sort_order: str = Query("asc", description="Sort order (asc or desc)"),
    db: AsyncSession = Depends(get_async_session),
    current_user=Depends(get_current_active_user),
):
    companies, total = await company_service.get_companies(
        db,
        skip=skip,
        limit=limit,
        search=search,
        is_active=is_active,
        industry=industry,
        subscription_plan=subscription_plan,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    return company_schema.CompanyListResponse(
        items=companies,
        total=total,
        page=(skip // limit) + 1,
        page_size=limit,
    )


@router.get("/stats", response_model=company_schema.CompanyStats)
async def get_company_stats(
    db: AsyncSession = Depends(get_async_session),
    current_user=Depends(get_current_active_user),
):
    """Get company statistics including counts and plan distribution."""
    return await company_service.get_company_stats(db)


@router.get("/by-domain/{domain}", response_model=company_schema.CompanyOut)
async def get_company_by_domain(
    domain: str,
    db: AsyncSession = Depends(get_async_session),
    current_user=Depends(get_current_active_user),
):
    company = await company_service.get_company_by_domain(db, domain)
    if not company:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
    return company


@router.get("/{company_id}", response_model=company_schema.CompanyOut)
async def get_company(
    company_id: int,
    db: AsyncSession = Depends(get_async_session),
    current_user=Depends(get_current_active_user),
):
    company = await company_service.get_company_with_user_count(db, company_id)
    if not company:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
    return company


@router.put("/{company_id}", response_model=company_schema.CompanyOut)
async def update_company(
    request: Request,
    company_id: int,
    payload: company_schema.CompanyUpdate,
    db: AsyncSession = Depends(get_async_session),
    current_user=Depends(require_superuser),
):
    company = await company_service.update_company(db, company_id, payload)
    if not company:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
    # Log company update
    await create_audit_log(
        db,
        action="update",
        resource_type="company",
        resource_id=company_id,
        user_id=current_user.id,
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request),
        details={"company_name": company.name, "updated_by": current_user.email, "updated_fields": payload.model_dump(exclude_none=True)},
    )
    return company


@router.delete("/{company_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_company(
    request: Request,
    company_id: int,
    db: AsyncSession = Depends(get_async_session),
    current_user=Depends(require_superuser),
):
    # Fetch company before deletion for audit log
    company_to_delete = await company_service.get_company(db, company_id)
    deleted = await company_service.delete_company(db, company_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
    # Log company deletion
    await create_audit_log(
        db,
        action="delete",
        resource_type="company",
        resource_id=company_id,
        user_id=current_user.id,
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request),
        details={"company_name": company_to_delete.name if company_to_delete else "unknown", "deleted_by": current_user.email},
    )
    return None

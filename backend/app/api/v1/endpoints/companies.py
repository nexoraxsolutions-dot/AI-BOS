from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app.core.request import get_client_ip, get_user_agent
from app.db.dependencies import get_async_session
from app.schemas import company as company_schema
from app.services import company as company_service
from app.services import onboarding as onboarding_service
from app.services import invitation as invitation_service
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


@router.post(
    "/onboard",
    response_model=company_schema.CompanyOnboardResponse,
    status_code=status.HTTP_201_CREATED,
)
async def onboard_company(
    request: Request,
    payload: company_schema.CompanyOnboardRequest,
    db: AsyncSession = Depends(get_async_session),
    current_user=Depends(get_current_active_user),
):
    """Self-service onboarding: create a company for a user with no company.

    Creates the company, assigns the user as owner, creates a default
    department, creates organization settings, and associates the user.
    """
    if current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Superusers must use the admin company endpoints.",
        )
    if current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You already belong to a company.",
        )
    try:
        company, department, org_settings = await onboarding_service.onboard_company(
            db, current_user, payload
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    await create_audit_log(
        db,
        action="company_onboard",
        resource_type="company",
        resource_id=company.id,
        user_id=current_user.id,
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request),
        details={"company_name": company.name, "domain": company.domain, "owner": current_user.email},
    )

    base = company_schema.CompanyOut.model_validate(company).model_dump()
    return company_schema.CompanyOnboardResponse(
        **base,
        membership_role="owner",
        default_department={"id": department.id, "name": department.name, "company_id": department.company_id},
        organization_settings={"id": org_settings.id, "company_id": org_settings.company_id, "timezone": org_settings.timezone},
    )


@router.get("/my", response_model=company_schema.UserCompaniesResponse)
async def list_my_companies(
    db: AsyncSession = Depends(get_async_session),
    current_user=Depends(get_current_active_user),
):
    """List all companies the current user belongs to (multi-company support)."""
    items, active_company_id = await onboarding_service.list_user_companies(db, current_user)
    return company_schema.UserCompaniesResponse(
        items=items,
        total=len(items),
        active_company_id=active_company_id,
    )


@router.post("/switch", response_model=company_schema.SwitchCompanyResponse)
async def switch_company(
    request: Request,
    payload: company_schema.SwitchCompanyRequest,
    db: AsyncSession = Depends(get_async_session),
    current_user=Depends(get_current_active_user),
):
    """Switch the current user's active company."""
    try:
        company_id = await onboarding_service.switch_active_company(
            db, current_user, payload.company_id
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    await create_audit_log(
        db,
        action="company_switch",
        resource_type="company",
        resource_id=company_id,
        user_id=current_user.id,
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request),
        details={"active_company_id": company_id, "email": current_user.email},
    )
    return company_schema.SwitchCompanyResponse(
        message="Active company switched successfully",
        active_company_id=company_id,
    )


@router.post("/invite", response_model=company_schema.CompanyInviteResponse, status_code=status.HTTP_201_CREATED)
async def invite_user(
    request: Request,
    payload: company_schema.CompanyInviteRequest,
    db: AsyncSession = Depends(get_async_session),
    current_user=Depends(get_current_active_user),
):
    """Invite a user to join a company (generates a secure invitation token)."""
    try:
        invitation, token = await invitation_service.invite_user_to_company(
            db,
            payload.company_id,
            current_user,
            payload.email,
            payload.role,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    company = await company_service.get_company(db, payload.company_id)
    company_name = company.name if company else payload.company_id

    # Deliver the invitation email (non-blocking / logged in dev)
    from app.services.email import send_invitation_email
    inviter_name = current_user.full_name or current_user.email
    await send_invitation_email(payload.email, token, company_name, inviter_name, payload.role)

    await create_audit_log(
        db,
        action="invite_sent",
        resource_type="company",
        resource_id=payload.company_id,
        user_id=current_user.id,
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request),
        details={"email": payload.email, "role": payload.role, "company_id": payload.company_id},
    )

    return company_schema.CompanyInviteResponse(
        invitation_id=invitation.id,
        company_id=invitation.company_id,
        company_name=company_name,
        email=invitation.email,
        token=token,
        expires_at=invitation.expires_at,
    )


async def _invitation_detail(db: AsyncSession, invitation):
    """Build a safe invitation detail payload."""
    company = await company_service.get_company(db, invitation.company_id)
    return company_schema.CompanyInvitationDetail(
        id=invitation.id,
        company_id=invitation.company_id,
        company_name=company.name if company else "Unknown company",
        email=invitation.email,
        role=invitation.role,
        status=invitation.status,
        expires_at=invitation.expires_at,
        created_at=invitation.created_at,
    )


@router.get("/invitations/{token}", response_model=company_schema.CompanyInvitationDetail)
async def get_invitation(
    token: str,
    db: AsyncSession = Depends(get_async_session),
    current_user=Depends(get_current_active_user),
):
    """Get details of a pending invitation by token."""
    invitation = await invitation_service.get_invitation_by_token(db, token)
    if not invitation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invitation not found or no longer pending")
    return await _invitation_detail(db, invitation)


@router.post("/invitations/{token}/accept", response_model=company_schema.InvitationActionResponse)
async def accept_invitation(
    request: Request,
    token: str,
    db: AsyncSession = Depends(get_async_session),
    current_user=Depends(get_current_active_user),
):
    """Accept an invitation and join the company."""
    invitation = await invitation_service.get_invitation_by_token(db, token)
    if not invitation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invitation not found or no longer pending")
    try:
        invitation = await invitation_service.accept_invitation(db, current_user, invitation)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    company = await company_service.get_company(db, invitation.company_id)
    await create_audit_log(
        db,
        action="invitation_accepted",
        resource_type="company",
        resource_id=invitation.company_id,
        user_id=current_user.id,
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request),
        details={"email": current_user.email, "company_id": invitation.company_id},
    )
    return company_schema.InvitationActionResponse(
        message="Invitation accepted successfully",
        invitation_id=invitation.id,
        company_id=invitation.company_id,
        company_name=company.name if company else None,
        joined=True,
    )


@router.post("/invitations/{token}/reject", response_model=company_schema.InvitationActionResponse)
async def reject_invitation(
    token: str,
    db: AsyncSession = Depends(get_async_session),
    current_user=Depends(get_current_active_user),
):
    """Reject a pending invitation."""
    invitation = await invitation_service.get_invitation_by_token(db, token)
    if not invitation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invitation not found or no longer pending")
    try:
        invitation = await invitation_service.reject_invitation(db, current_user, invitation)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return company_schema.InvitationActionResponse(
        message="Invitation rejected",
        invitation_id=invitation.id,
        company_id=invitation.company_id,
        joined=False,
    )




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

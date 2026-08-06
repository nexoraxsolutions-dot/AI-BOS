"""Company onboarding and company-switching service.

Implements:
- ``onboard_company`` — creates a company for a user with no company, along with
  a default department, organization settings, owner membership, and assigns the
  user as primary/active company.
- ``list_user_companies`` / ``switch_active_company`` — support a user belonging
  to multiple companies and switching the active one.
- ``is_company_member`` — membership check used by invitation and switching.
"""
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.company import Company
from app.models.department import Department
from app.models.membership import CompanyMembership
from app.models.organization_settings import OrganizationSettings
from app.models.user import User
from app.services.cache import cache_service


async def get_membership(
    db: AsyncSession,
    user_id: int,
    company_id: int,
) -> Optional[CompanyMembership]:
    """Fetch an active membership for a user+company, if any."""
    result = await db.execute(
        select(CompanyMembership).where(
            CompanyMembership.user_id == user_id,
            CompanyMembership.company_id == company_id,
            CompanyMembership.is_active == True,  # noqa: E712
        )
    )
    return result.scalar_one_or_none()


async def is_company_member(db: AsyncSession, user: User, company_id: int) -> bool:
    """Return True if the user is a member of the given company."""
    if user.company_id == company_id:
        return True
    return await get_membership(db, user.id, company_id) is not None


async def onboard_company(db: AsyncSession, user: User, payload):
    """Create a company for onboarding a user with no company.

    Returns (company, department, organization_settings). Performs all
    creation in a single transaction so that a failure rolls everything back.
    """
    if user.company_id:
        raise ValueError("You already belong to a company")

    company = Company(**payload.model_dump(exclude_unset=True, exclude={"settings"}))
    company.is_active = True
    if payload.settings:
        company.settings = payload.settings
    db.add(company)

    try:
        await db.flush()

        # Default department
        department = Department(
            company_id=company.id,
            name="General",
            description="Default department",
            manager_id=user.id,
            is_active=True,
        )
        db.add(department)

        # Organization settings
        org_settings = OrganizationSettings(company_id=company.id)
        db.add(org_settings)

        # Owner membership
        membership = CompanyMembership(
            user_id=user.id,
            company_id=company.id,
            role="owner",
            is_active=True,
        )
        db.add(membership)

        # Associate user
        user.company_id = company.id
        user.active_company_id = company.id

        await db.commit()
        await db.refresh(company)
    except Exception:
        await db.rollback()
        raise

    await cache_service.delete_pattern("companies:list:*")
    await cache_service.delete("companies:stats")
    await cache_service.delete(f"user:{user.id}")
    await cache_service.delete_pattern("users:list:*")

    return company, department, org_settings


async def list_user_companies(db: AsyncSession, user: User):
    """List all companies the user belongs to, with membership role."""
    company_ids: set = set()
    role_map: dict = {}

    memberships_result = await db.execute(
        select(CompanyMembership).where(
            CompanyMembership.user_id == user.id,
            CompanyMembership.is_active == True,  # noqa: E712
        )
    )
    for m in memberships_result.scalars().all():
        company_ids.add(m.company_id)
        role_map[m.company_id] = m.role

    if user.company_id:
        company_ids.add(user.company_id)
        role_map.setdefault(user.company_id, "member")

    if not company_ids:
        return [], user.active_company_id

    companies_result = await db.execute(
        select(Company).where(Company.id.in_(company_ids))
    )
    companies = companies_result.scalars().all()

    items = []
    for company in companies:
        items.append(
            {
                "id": company.id,
                "name": company.name,
                "domain": company.domain,
                "role": role_map.get(company.id, "member"),
                "is_active": company.is_active,
                "is_current": user.active_company_id == company.id,
                "created_at": company.created_at,
            }
        )
    # Stable ordering: current company first, then by name
    items.sort(key=lambda c: (not c["is_current"], c["name"].lower()))
    return items, user.active_company_id


async def switch_active_company(db: AsyncSession, user: User, company_id: int) -> int:
    """Set the user's active company, validating membership."""
    if not await is_company_member(db, user, company_id):
        raise ValueError("You are not a member of this company")

    result = await db.execute(select(Company).where(Company.id == company_id))
    company = result.scalar_one_or_none()
    if not company or not company.is_active:
        raise ValueError("Company not found or inactive")

    user.active_company_id = company_id
    await db.commit()
    await db.refresh(user)
    await cache_service.delete(f"user:{user.id}")
    return company_id

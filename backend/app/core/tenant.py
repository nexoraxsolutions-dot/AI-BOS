"""Tenant-aware dependencies for multi-tenancy support.

Uses a shared-database approach where data is isolated by company_id.
This module provides dependencies that scope database queries to the
current user's company.
"""

import logging
from typing import Optional

from fastapi import Depends, HTTPException, status

from app.core.security import get_current_active_user, get_current_user
from app.models.user import User

logger = logging.getLogger("ai_bos")


class TenantContext:
    """Holds the current tenant context during a request."""
    
    def __init__(self, user: User):
        self.user = user
        self.company_id: Optional[int] = user.company_id
        self.is_superuser: bool = user.is_superuser
    
    @property
    def is_tenant_user(self) -> bool:
        """Check if user belongs to a tenant (company)."""
        return self.company_id is not None or self.is_superuser


async def get_tenant_context(
    current_user: User = Depends(get_current_active_user),
) -> TenantContext:
    """Get the tenant context for the current request.
    
    Superusers can access all tenants. Regular users are scoped to their company.
    """
    return TenantContext(current_user)


async def require_tenant_membership(
    tenant: TenantContext = Depends(get_tenant_context),
) -> TenantContext:
    """Require the user to belong to a tenant (company).
    
    Superusers can pass through, regular users must have a company assigned.
    """
    if tenant.is_superuser:
        return tenant
    
    if not tenant.company_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You must belong to a company to access this resource",
        )
    
    return tenant


def scoped_company_id(tenant: TenantContext) -> Optional[int]:
    """Get the company_id to scope queries.
    
    Returns None for superusers (no scope), and the tenant's company_id
    for regular users.
    """
    if tenant.is_superuser:
        return None
    return tenant.company_id


def require_same_company_or_superuser(company_id: int):
    """Create a dependency that ensures the user belongs to the specified company or is superuser."""
    async def _dependency(
        tenant: TenantContext = Depends(get_tenant_context),
    ):
        if tenant.is_superuser:
            return tenant
        
        if tenant.company_id != company_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have access to this company's resources",
            )
        return tenant
    
    return _dependency
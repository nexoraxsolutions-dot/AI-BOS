"""Pydantic schemas for tenant management."""
from pydantic import BaseModel, ConfigDict
from typing import Optional, Any, Dict, List
from datetime import datetime


class TenantStats(BaseModel):
    """Tenant statistics for dashboard."""
    total_users: int
    active_users: int
    total_companies: int
    active_companies: int
    total_environment_variables: int
    storage_used_estimate: str = "0 B"


class TenantUserSummary(BaseModel):
    """Summary of a user within a tenant."""
    id: int
    email: str
    full_name: Optional[str] = None
    username: Optional[str] = None
    is_active: bool
    is_superuser: bool
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class TenantDetail(BaseModel):
    """Detailed tenant information including users."""
    id: int
    name: str
    domain: str
    description: Optional[str] = None
    industry: Optional[str] = None
    employee_count: Optional[int] = None
    subscription_plan: str = "free"
    subscription_status: str = "active"
    is_active: bool
    user_count: int = 0
    users: List[TenantUserSummary] = []
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class TenantListResponse(BaseModel):
    """Paginated tenant list response."""
    items: List[TenantDetail]
    total: int
    page: int
    page_size: int


class TenantInviteRequest(BaseModel):
    """Request to invite a user to a tenant."""
    email: str
    company_id: Optional[int] = None
    full_name: Optional[str] = None
    role: Optional[str] = "member"


class TenantInviteResponse(BaseModel):
    """Response after inviting a user."""
    message: str
    user_id: Optional[int] = None
    email: str


class TenantTransferRequest(BaseModel):
    """Request to transfer ownership to another user."""
    user_id: int


class TenantSettingsUpdate(BaseModel):
    """Update tenant-level settings."""
    settings: Dict[str, Any]


class UserCompanyAssignment(BaseModel):
    """Assign a user to a company (for superuser)."""
    user_id: int
    company_id: int
"""
RBAC schemas for role-based access control.

Includes schemas for:
- Role CRUD
- Permission CRUD
- User role assignment
- Permission checks
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel


# ---------- Permission Schemas ----------

class PermissionBase(BaseModel):
    name: str
    description: Optional[str] = None
    resource: str
    action: str


class PermissionCreate(PermissionBase):
    pass


class PermissionUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class PermissionResponse(PermissionBase):
    id: int
    created_at: datetime

    model_config = {"from_attributes": True}


# ---------- Role Schemas ----------

class RoleBase(BaseModel):
    name: str
    description: Optional[str] = None


class RoleCreate(RoleBase):
    permission_ids: Optional[List[int]] = None


class RoleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    permission_ids: Optional[List[int]] = None


class RoleResponse(RoleBase):
    id: int
    is_system_role: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    permissions: List[PermissionResponse] = []

    model_config = {"from_attributes": True}


class RoleListResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    is_system_role: bool
    permission_count: int = 0
    user_count: int = 0
    created_at: datetime

    model_config = {"from_attributes": True}


# ---------- User Role Assignment Schemas ----------

class UserRoleAssignment(BaseModel):
    user_id: int
    role_id: int


class UserRoleResponse(BaseModel):
    id: int
    user_id: int
    role_id: int
    assigned_at: datetime
    role: RoleResponse

    model_config = {"from_attributes": True}


class UserWithRolesResponse(BaseModel):
    id: int
    email: str
    full_name: Optional[str] = None
    username: Optional[str] = None
    is_active: bool
    is_superuser: bool
    roles: List[RoleResponse] = []

    model_config = {"from_attributes": True}


# ---------- Permission Check Schemas ----------

class PermissionCheck(BaseModel):
    resource: str
    action: str


class PermissionCheckResponse(BaseModel):
    has_permission: bool
    resource: str
    action: str


class UserPermissionsResponse(BaseModel):
    user_id: int
    email: str
    permissions: List[str]  # e.g., ["users:read", "users:write"]
    roles: List[str]  # e.g., ["admin", "manager"]
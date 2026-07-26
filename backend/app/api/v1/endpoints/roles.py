"""
RBAC API endpoints for role-based access control.

Provides CRUD operations for:
- Roles
- Permissions
- User role assignments
- Permission checking
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_active_user, require_superuser
from app.db.dependencies import get_async_session
from app.models.user import User
from app.schemas import role as role_schema
from app.services import role as role_service

router = APIRouter()


# ========== Permission Endpoints ==========

@router.get(
    "/permissions",
    response_model=list[role_schema.PermissionResponse],
)
async def list_permissions(
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_active_user),
):
    """List all permissions. Requires authenticated user."""
    permissions = await role_service.get_all_permissions(db)
    return permissions


@router.post(
    "/permissions",
    response_model=role_schema.PermissionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_permission(
    payload: role_schema.PermissionCreate,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(require_superuser),
):
    """Create a new permission. Superuser only."""
    try:
        permission = await role_service.create_permission(
            db,
            name=payload.name,
            resource=payload.resource,
            action=payload.action,
            description=payload.description,
        )
        return permission
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.delete(
    "/permissions/{permission_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_permission(
    permission_id: int,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(require_superuser),
):
    """Delete a permission. Superuser only."""
    try:
        await role_service.delete_permission(db, permission_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


# ========== Role Endpoints ==========

@router.get(
    "/roles",
    response_model=list[role_schema.RoleListResponse],
)
async def list_roles(
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_active_user),
):
    """List all roles. Requires authenticated user."""
    from sqlalchemy import func
    from app.models.role import UserRole as UserRoleModel
    
    roles = await role_service.get_all_roles(db)
    result = []
    for role in roles:
        # Count users assigned to this role
        user_count_result = await db.execute(
            select(func.count()).select_from(UserRoleModel).where(UserRoleModel.role_id == role.id)
        )
        user_count = user_count_result.scalar() or 0
        result.append(role_schema.RoleListResponse(
            id=role.id,
            name=role.name,
            description=role.description,
            is_system_role=role.is_system_role,
            permission_count=len(role.permissions),
            user_count=user_count,
            created_at=role.created_at,
        ))
    return result


@router.get(
    "/roles/{role_id}",
    response_model=role_schema.RoleResponse,
)
async def get_role(
    role_id: int,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_active_user),
):
    """Get role details. Requires authenticated user."""
    role = await role_service.get_role_by_id(db, role_id)
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found",
        )
    return role


@router.post(
    "/roles",
    response_model=role_schema.RoleResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_role(
    payload: role_schema.RoleCreate,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(require_superuser),
):
    """Create a new role. Superuser only."""
    try:
        role = await role_service.create_role(
            db,
            name=payload.name,
            description=payload.description,
            permission_ids=payload.permission_ids,
        )
        return role
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.put(
    "/roles/{role_id}",
    response_model=role_schema.RoleResponse,
)
async def update_role(
    role_id: int,
    payload: role_schema.RoleUpdate,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(require_superuser),
):
    """Update a role. Superuser only. System roles cannot be modified."""
    try:
        role = await role_service.update_role(
            db,
            role_id=role_id,
            name=payload.name,
            description=payload.description,
            permission_ids=payload.permission_ids,
        )
        return role
    except ValueError as exc:
        status_code = status.HTTP_400_BAD_REQUEST
        if "not found" in str(exc).lower():
            status_code = status.HTTP_404_NOT_FOUND
        raise HTTPException(
            status_code=status_code,
            detail=str(exc),
        ) from exc


@router.delete(
    "/roles/{role_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_role(
    role_id: int,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(require_superuser),
):
    """Delete a role. Superuser only. System roles cannot be deleted."""
    try:
        await role_service.delete_role(db, role_id)
    except ValueError as exc:
        status_code = status.HTTP_400_BAD_REQUEST
        if "not found" in str(exc).lower():
            status_code = status.HTTP_404_NOT_FOUND
        raise HTTPException(
            status_code=status_code,
            detail=str(exc),
        ) from exc


# ========== User Role Assignment ==========

@router.get(
    "/users/{user_id}/roles",
    response_model=list[role_schema.RoleResponse],
)
async def get_user_roles(
    user_id: int,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_active_user),
):
    """Get all roles for a user."""
    roles = await role_service.get_user_roles(db, user_id)
    return roles


@router.post(
    "/users/{user_id}/roles",
    response_model=role_schema.UserRoleResponse,
    status_code=status.HTTP_201_CREATED,
)
async def assign_user_role(
    user_id: int,
    payload: role_schema.UserRoleAssignment,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(require_superuser),
):
    """Assign a role to a user. Superuser only."""
    try:
        user_role = await role_service.assign_role_to_user(
            db,
            user_id=user_id,
            role_id=payload.role_id,
            assigned_by=current_user.id,
        )
        return user_role
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.delete(
    "/users/{user_id}/roles/{role_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def remove_user_role(
    user_id: int,
    role_id: int,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(require_superuser),
):
    """Remove a role from a user. Superuser only."""
    try:
        await role_service.remove_role_from_user(db, user_id, role_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.get(
    "/roles/{role_id}/users",
    response_model=list[role_schema.UserWithRolesResponse],
)
async def get_role_users(
    role_id: int,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_active_user),
):
    """Get all users with a specific role."""
    users = await role_service.get_role_users(db, role_id)
    result = []
    for user in users:
        roles = await role_service.get_user_roles(db, user.id)
        result.append(role_schema.UserWithRolesResponse(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            username=user.username,
            is_active=user.is_active,
            is_superuser=user.is_superuser,
            roles=list(roles),
        ))
    return result


# ========== Permission Checking ==========

@router.get(
    "/users/{user_id}/permissions",
    response_model=role_schema.UserPermissionsResponse,
)
async def get_user_permissions(
    user_id: int,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_active_user),
):
    """Get all permissions for a user."""
    permissions = await role_service.get_user_permissions(db, user_id)
    roles = await role_service.get_user_roles(db, user_id)
    user_result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = user_result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return role_schema.UserPermissionsResponse(
        user_id=user.id,
        email=user.email,
        permissions=list(permissions),
        roles=[r.name for r in roles],
    )


@router.post(
    "/check-permission",
    response_model=role_schema.PermissionCheckResponse,
)
async def check_permission(
    payload: role_schema.PermissionCheck,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_active_user),
):
    """Check if the current user has a specific permission."""
    has_permission = await role_service.user_has_permission(
        db,
        user_id=current_user.id,
        resource=payload.resource,
        action=payload.action,
    )
    return role_schema.PermissionCheckResponse(
        has_permission=has_permission,
        resource=payload.resource,
        action=payload.action,
    )
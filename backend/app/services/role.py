"""
RBAC service layer for role-based access control.

Provides:
- Role CRUD operations
- Permission CRUD operations
- User-role assignment
- Permission checking
- Default role seeding
"""
import logging
from typing import List, Optional, Sequence
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.role import Role, Permission, UserRole, role_permission_association
from app.models.user import User

logger = logging.getLogger("ai_bos")

# ========== Seed Data ==========

DEFAULT_PERMISSIONS = {
    "users:read": {"resource": "users", "action": "read", "description": "View user list and details"},
    "users:write": {"resource": "users", "action": "write", "description": "Create and edit users"},
    "users:delete": {"resource": "users", "action": "delete", "description": "Delete users"},
    "users:admin": {"resource": "users", "action": "admin", "description": "Full user administration"},
    "companies:read": {"resource": "companies", "action": "read", "description": "View company list and details"},
    "companies:write": {"resource": "companies", "action": "write", "description": "Create and edit companies"},
    "companies:delete": {"resource": "companies", "action": "delete", "description": "Delete companies"},
    "companies:admin": {"resource": "companies", "action": "admin", "description": "Full company administration"},
    "audit_logs:read": {"resource": "audit_logs", "action": "read", "description": "View audit logs"},
    "audit_logs:export": {"resource": "audit_logs", "action": "export", "description": "Export audit logs"},
    "tokens:read": {"resource": "tokens", "action": "read", "description": "View token list and details"},
    "tokens:revoke": {"resource": "tokens", "action": "revoke", "description": "Revoke tokens"},
    "environment_variables:read": {"resource": "environment_variables", "action": "read", "description": "View environment variables"},
    "environment_variables:write": {"resource": "environment_variables", "action": "write", "description": "Create and edit environment variables"},
    "environment_variables:delete": {"resource": "environment_variables", "action": "delete", "description": "Delete environment variables"},
    "roles:read": {"resource": "roles", "action": "read", "description": "View roles and permissions"},
    "roles:write": {"resource": "roles", "action": "write", "description": "Create and edit roles"},
    "roles:delete": {"resource": "roles", "action": "delete", "description": "Delete roles"},
    "roles:assign": {"resource": "roles", "action": "assign", "description": "Assign roles to users"},
    "dashboard:read": {"resource": "dashboard", "action": "read", "description": "View dashboard statistics"},
    "redis:read": {"resource": "redis", "action": "read", "description": "View Redis cache status"},
    "redis:flush": {"resource": "redis", "action": "flush", "description": "Flush Redis cache"},
    "tenants:read": {"resource": "tenants", "action": "read", "description": "View tenant information"},
    "tenants:admin": {"resource": "tenants", "action": "admin", "description": "Full tenant administration"},
}

DEFAULT_ROLES = {
    "admin": {
        "description": "Full system access with all permissions",
        "is_system_role": True,
        "permissions": list(DEFAULT_PERMISSIONS.keys()),
    },
    "manager": {
        "description": "Management access with read/write on most resources",
        "is_system_role": True,
        "permissions": [
            "users:read", "users:write",
            "companies:read", "companies:write",
            "audit_logs:read",
            "tokens:read", "tokens:revoke",
            "environment_variables:read", "environment_variables:write",
            "roles:read",
            "dashboard:read",
            "redis:read",
            "tenants:read",
        ],
    },
    "user": {
        "description": "Standard user access with read-only on most resources",
        "is_system_role": True,
        "permissions": [
            "users:read",
            "companies:read",
            "audit_logs:read",
            "environment_variables:read",
            "dashboard:read",
            "redis:read",
        ],
    },
    "viewer": {
        "description": "Read-only access to basic resources",
        "is_system_role": True,
        "permissions": [
            "dashboard:read",
            "users:read",
            "companies:read",
        ],
    },
}


async def seed_default_roles_and_permissions(db: AsyncSession) -> None:
    """Seed default roles and permissions if they don't exist."""
    from sqlalchemy import func

    # Check if already seeded
    result = await db.execute(select(func.count()).select_from(Permission))
    count = result.scalar()
    if count and count > 0:
        return  # Already seeded

    # Create permissions
    permission_map = {}
    for perm_name, perm_data in DEFAULT_PERMISSIONS.items():
        permission = Permission(
            name=perm_name,
            resource=perm_data["resource"],
            action=perm_data["action"],
            description=perm_data["description"],
        )
        db.add(permission)
        await db.flush()
        permission_map[perm_name] = permission

    # Create roles with permissions
    for role_name, role_data in DEFAULT_ROLES.items():
        role = Role(
            name=role_name,
            description=role_data["description"],
            is_system_role=role_data["is_system_role"],
        )
        db.add(role)
        await db.flush()

        # Assign permissions to role
        for perm_name in role_data["permissions"]:
            if perm_name in permission_map:
                stmt = role_permission_association.insert().values(
                    role_id=role.id,
                    permission_id=permission_map[perm_name].id,
                )
                await db.execute(stmt)

    await db.commit()
    logger.info("Default roles and permissions seeded successfully")


# ========== Permission Service ==========

async def get_all_permissions(db: AsyncSession) -> Sequence[Permission]:
    """Get all permissions."""
    result = await db.execute(select(Permission).order_by(Permission.resource, Permission.action))
    return result.scalars().all()


async def get_permission_by_id(db: AsyncSession, permission_id: int) -> Optional[Permission]:
    """Get permission by ID."""
    result = await db.execute(select(Permission).where(Permission.id == permission_id))
    return result.scalar_one_or_none()


async def get_permission_by_name(db: AsyncSession, name: str) -> Optional[Permission]:
    """Get permission by name."""
    result = await db.execute(select(Permission).where(Permission.name == name))
    return result.scalar_one_or_none()


async def create_permission(db: AsyncSession, name: str, resource: str, action: str, description: Optional[str] = None) -> Permission:
    """Create a new permission."""
    existing = await get_permission_by_name(db, name)
    if existing:
        raise ValueError(f"Permission '{name}' already exists")
    
    permission = Permission(
        name=name,
        resource=resource,
        action=action,
        description=description,
    )
    db.add(permission)
    await db.commit()
    await db.refresh(permission)
    return permission


async def delete_permission(db: AsyncSession, permission_id: int) -> None:
    """Delete a permission."""
    permission = await get_permission_by_id(db, permission_id)
    if not permission:
        raise ValueError("Permission not found")
    await db.delete(permission)
    await db.commit()


# ========== Role Service ==========

async def get_all_roles(db: AsyncSession) -> Sequence[Role]:
    """Get all roles with permission and user counts."""
    result = await db.execute(
        select(Role)
        .options(selectinload(Role.permissions))
        .order_by(Role.name)
    )
    return result.scalars().all()


async def get_role_by_id(db: AsyncSession, role_id: int) -> Optional[Role]:
    """Get role by ID with permissions loaded."""
    result = await db.execute(
        select(Role)
        .options(selectinload(Role.permissions))
        .where(Role.id == role_id)
    )
    return result.scalar_one_or_none()


async def get_role_by_name(db: AsyncSession, name: str) -> Optional[Role]:
    """Get role by name."""
    result = await db.execute(
        select(Role)
        .options(selectinload(Role.permissions))
        .where(Role.name == name)
    )
    return result.scalar_one_or_none()


async def create_role(db: AsyncSession, name: str, description: Optional[str] = None, permission_ids: Optional[List[int]] = None) -> Role:
    """Create a new role."""
    existing = await get_role_by_name(db, name)
    if existing:
        raise ValueError(f"Role '{name}' already exists")

    role = Role(name=name, description=description)
    db.add(role)
    await db.flush()

    if permission_ids:
        permissions = await db.execute(
            select(Permission).where(Permission.id.in_(permission_ids))
        )
        for perm in permissions.scalars().all():
            stmt = role_permission_association.insert().values(
                role_id=role.id,
                permission_id=perm.id,
            )
            await db.execute(stmt)

    await db.commit()
    await db.refresh(role)
    return role


async def update_role(
    db: AsyncSession,
    role_id: int,
    name: Optional[str] = None,
    description: Optional[str] = None,
    permission_ids: Optional[List[int]] = None,
) -> Role:
    """Update a role."""
    role = await get_role_by_id(db, role_id)
    if not role:
        raise ValueError("Role not found")
    if role.is_system_role:
        raise ValueError("System roles cannot be modified")

    if name is not None:
        role.name = name
    if description is not None:
        role.description = description

    if permission_ids is not None:
        # Remove existing permissions
        await db.execute(
            delete(role_permission_association).where(
                role_permission_association.c.role_id == role_id
            )
        )
        # Add new permissions
        permissions = await db.execute(
            select(Permission).where(Permission.id.in_(permission_ids))
        )
        for perm in permissions.scalars().all():
            stmt = role_permission_association.insert().values(
                role_id=role.id,
                permission_id=perm.id,
            )
            await db.execute(stmt)

    await db.commit()
    await db.refresh(role)
    return role


async def delete_role(db: AsyncSession, role_id: int) -> None:
    """Delete a role."""
    role = await get_role_by_id(db, role_id)
    if not role:
        raise ValueError("Role not found")
    if role.is_system_role:
        raise ValueError("System roles cannot be deleted")

    await db.delete(role)
    await db.commit()


# ========== User Role Assignment ==========

async def assign_role_to_user(
    db: AsyncSession,
    user_id: int,
    role_id: int,
    assigned_by: Optional[int] = None,
) -> UserRole:
    """Assign a role to a user."""
    # Verify role exists
    role = await get_role_by_id(db, role_id)
    if not role:
        raise ValueError("Role not found")

    # Verify user exists
    user_result = await db.execute(select(User).where(User.id == user_id))
    user = user_result.scalar_one_or_none()
    if not user:
        raise ValueError("User not found")

    # Check if already assigned
    existing = await db.execute(
        select(UserRole).where(
            UserRole.user_id == user_id,
            UserRole.role_id == role_id,
        )
    )
    if existing.scalar_one_or_none():
        raise ValueError("User already has this role")

    user_role = UserRole(
        user_id=user_id,
        role_id=role_id,
        assigned_by=assigned_by,
    )
    db.add(user_role)
    await db.commit()
    await db.refresh(user_role)
    return user_role


async def remove_role_from_user(db: AsyncSession, user_id: int, role_id: int) -> None:
    """Remove a role from a user."""
    result = await db.execute(
        select(UserRole).where(
            UserRole.user_id == user_id,
            UserRole.role_id == role_id,
        )
    )
    user_role = result.scalar_one_or_none()
    if not user_role:
        raise ValueError("User does not have this role")

    await db.delete(user_role)
    await db.commit()


async def get_user_roles(db: AsyncSession, user_id: int) -> Sequence[Role]:
    """Get all roles for a user."""
    result = await db.execute(
        select(Role)
        .options(selectinload(Role.permissions))
        .join(UserRole, UserRole.role_id == Role.id)
        .where(UserRole.user_id == user_id)
    )
    return result.scalars().all()


async def get_role_users(db: AsyncSession, role_id: int) -> Sequence[User]:
    """Get all users with a specific role."""
    result = await db.execute(
        select(User)
        .join(UserRole, UserRole.user_id == User.id)
        .where(UserRole.role_id == role_id)
    )
    return result.scalars().all()


# ========== Permission Checking ==========

async def user_has_permission(
    db: AsyncSession,
    user_id: int,
    resource: str,
    action: str,
) -> bool:
    """Check if a user has a specific permission via their roles."""
    # Superusers have all permissions
    user_result = await db.execute(select(User).where(User.id == user_id))
    user = user_result.scalar_one_or_none()
    if user and user.is_superuser:
        return True

    # Check via roles
    result = await db.execute(
        select(Permission)
        .select_from(Permission)
        .join(role_permission_association)
        .join(Role)
        .join(UserRole)
        .where(
            UserRole.user_id == user_id,
            Permission.resource == resource,
            Permission.action == action,
        )
    )
    return result.scalar_one_or_none() is not None


async def get_user_permissions(db: AsyncSession, user_id: int) -> List[str]:
    """Get all permission strings for a user."""
    # Superusers have all permissions
    user_result = await db.execute(select(User).where(User.id == user_id))
    user = user_result.scalar_one_or_none()
    if user and user.is_superuser:
        return list(DEFAULT_PERMISSIONS.keys())

    result = await db.execute(
        select(Permission.name)
        .select_from(Permission)
        .join(role_permission_association)
        .join(Role)
        .join(UserRole)
        .where(UserRole.user_id == user_id)
        .distinct()
    )
    return list(result.scalars().all())
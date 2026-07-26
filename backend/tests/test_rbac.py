"""
Tests for Role-Based Access Control (RBAC) functionality.

Tests:
- Permission CRUD
- Role CRUD
- User role assignment
- Permission checking
- Default role seeding
"""
import pytest
from fastapi import status
from sqlalchemy import select

from app.models.role import Role, Permission, UserRole
from app.services import role as role_service
from app.core.security import get_password_hash


class TestDefaultSeeding:
    """Tests for default role and permission seeding."""

    @pytest.mark.asyncio
    async def test_seed_roles_and_permissions(self, db_session):
        """Test that seeding creates default roles and permissions."""
        # Seed should create data
        await role_service.seed_default_roles_and_permissions(db_session)

        # Verify permissions were created
        permissions = await role_service.get_all_permissions(db_session)
        assert len(permissions) >= 23  # All default permissions

        # Verify roles were created
        roles = await role_service.get_all_roles(db_session)
        assert len(roles) >= 4  # admin, manager, user, viewer

        # Verify admin role has all permissions
        admin_role = await role_service.get_role_by_name(db_session, "admin")
        assert admin_role is not None
        assert len(admin_role.permissions) >= 23

        # Verify viewer role has limited permissions
        viewer_role = await role_service.get_role_by_name(db_session, "viewer")
        assert viewer_role is not None
        assert len(viewer_role.permissions) == 3  # dashboard:read, users:read, companies:read

    @pytest.mark.asyncio
    async def test_seed_is_idempotent(self, db_session):
        """Test that seeding multiple times doesn't duplicate data."""
        await role_service.seed_default_roles_and_permissions(db_session)
        await role_service.seed_default_roles_and_permissions(db_session)
        await role_service.seed_default_roles_and_permissions(db_session)

        # Verify counts remain the same
        permissions = await role_service.get_all_permissions(db_session)
        assert len(permissions) >= 23

        roles = await role_service.get_all_roles(db_session)
        assert len(roles) >= 4


class TestPermissionService:
    """Tests for permission CRUD operations."""

    @pytest.mark.asyncio
    async def test_create_permission(self, db_session):
        """Test creating a new permission."""
        permission = await role_service.create_permission(
            db_session,
            name="test:read",
            resource="test",
            action="read",
            description="Test permission",
        )
        assert permission.id is not None
        assert permission.name == "test:read"
        assert permission.resource == "test"
        assert permission.action == "read"

    @pytest.mark.asyncio
    async def test_create_duplicate_permission(self, db_session):
        """Test that duplicate permission raises ValueError."""
        await role_service.create_permission(
            db_session,
            name="test:write",
            resource="test",
            action="write",
        )
        with pytest.raises(ValueError) as exc_info:
            await role_service.create_permission(
                db_session,
                name="test:write",
                resource="test",
                action="write",
            )
        assert "already exists" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_permission_by_name(self, db_session):
        """Test getting permission by name."""
        await role_service.seed_default_roles_and_permissions(db_session)
        permission = await role_service.get_permission_by_name(db_session, "users:read")
        assert permission is not None
        assert permission.resource == "users"
        assert permission.action == "read"


class TestRoleService:
    """Tests for role CRUD operations."""

    @pytest.mark.asyncio
    async def test_create_role(self, db_session):
        """Test creating a new role."""
        role = await role_service.create_role(
            db_session,
            name="custom_role",
            description="A custom role",
        )
        assert role.id is not None
        assert role.name == "custom_role"
        assert role.description == "A custom role"
        assert role.is_system_role is False

    @pytest.mark.asyncio
    async def test_create_role_with_permissions(self, db_session):
        """Test creating a role with permissions."""
        await role_service.seed_default_roles_and_permissions(db_session)

        perm1 = await role_service.get_permission_by_name(db_session, "users:read")
        perm2 = await role_service.get_permission_by_name(db_session, "dashboard:read")

        role = await role_service.create_role(
            db_session,
            name="test_role_with_perms",
            permission_ids=[perm1.id, perm2.id],
        )
        assert len(role.permissions) == 2
        perm_names = [p.name for p in role.permissions]
        assert "users:read" in perm_names
        assert "dashboard:read" in perm_names

    @pytest.mark.asyncio
    async def test_create_duplicate_role(self, db_session):
        """Test that duplicate role raises ValueError."""
        await role_service.create_role(db_session, name="unique_role")
        with pytest.raises(ValueError) as exc_info:
            await role_service.create_role(db_session, name="unique_role")
        assert "already exists" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_delete_system_role_fails(self, db_session):
        """Test that system roles cannot be deleted."""
        await role_service.seed_default_roles_and_permissions(db_session)
        admin_role = await role_service.get_role_by_name(db_session, "admin")
        with pytest.raises(ValueError) as exc_info:
            await role_service.delete_role(db_session, admin_role.id)
        assert "cannot be deleted" in str(exc_info.value)


class TestUserRoleAssignment:
    """Tests for user-role assignment."""

    @pytest.mark.asyncio
    async def test_assign_role_to_user(self, db_session, test_user):
        """Test assigning a role to a user."""
        await role_service.seed_default_roles_and_permissions(db_session)
        user_role = await role_service.get_role_by_name(db_session, "user")

        user_role_assignment = await role_service.assign_role_to_user(
            db_session,
            user_id=test_user.id,
            role_id=user_role.id,
            assigned_by=test_user.id,
        )
        assert user_role_assignment.id is not None
        assert user_role_assignment.user_id == test_user.id
        assert user_role_assignment.role_id == user_role.id

    @pytest.mark.asyncio
    async def test_get_user_roles(self, db_session, test_user):
        """Test getting all roles for a user."""
        await role_service.seed_default_roles_and_permissions(db_session)
        user_role = await role_service.get_role_by_name(db_session, "user")
        viewer_role = await role_service.get_role_by_name(db_session, "viewer")

        await role_service.assign_role_to_user(
            db_session, user_id=test_user.id, role_id=user_role.id,
        )
        await role_service.assign_role_to_user(
            db_session, user_id=test_user.id, role_id=viewer_role.id,
        )

        roles = await role_service.get_user_roles(db_session, test_user.id)
        assert len(roles) == 2
        role_names = [r.name for r in roles]
        assert "user" in role_names
        assert "viewer" in role_names

    @pytest.mark.asyncio
    async def test_remove_role_from_user(self, db_session, test_user):
        """Test removing a role from a user."""
        await role_service.seed_default_roles_and_permissions(db_session)
        user_role = await role_service.get_role_by_name(db_session, "user")

        await role_service.assign_role_to_user(
            db_session, user_id=test_user.id, role_id=user_role.id,
        )

        # Remove role
        await role_service.remove_role_from_user(
            db_session, user_id=test_user.id, role_id=user_role.id,
        )

        # Verify role is removed
        roles = await role_service.get_user_roles(db_session, test_user.id)
        assert len(roles) == 0

    @pytest.mark.asyncio
    async def test_duplicate_role_assignment_fails(self, db_session, test_user):
        """Test that assigning same role twice raises ValueError."""
        await role_service.seed_default_roles_and_permissions(db_session)
        user_role = await role_service.get_role_by_name(db_session, "user")

        await role_service.assign_role_to_user(
            db_session, user_id=test_user.id, role_id=user_role.id,
        )
        with pytest.raises(ValueError) as exc_info:
            await role_service.assign_role_to_user(
                db_session, user_id=test_user.id, role_id=user_role.id,
            )
        assert "already has this role" in str(exc_info.value)


class TestPermissionChecking:
    """Tests for permission checking."""

    @pytest.mark.asyncio
    async def test_superuser_has_all_permissions(self, db_session, admin_user):
        """Test that superusers have all permissions."""
        has_perm = await role_service.user_has_permission(
            db_session,
            user_id=admin_user.id,
            resource="users",
            action="admin",
        )
        assert has_perm is True

    @pytest.mark.asyncio
    async def test_user_with_role_has_permission(self, db_session, test_user):
        """Test that a user with a role has the role's permissions."""
        await role_service.seed_default_roles_and_permissions(db_session)

        # Assign admin role to user
        admin_role = await role_service.get_role_by_name(db_session, "admin")
        await role_service.assign_role_to_user(
            db_session, user_id=test_user.id, role_id=admin_role.id,
        )

        has_perm = await role_service.user_has_permission(
            db_session,
            user_id=test_user.id,
            resource="users",
            action="read",
        )
        assert has_perm is True

    @pytest.mark.asyncio
    async def test_user_without_role_has_no_permission(self, db_session, test_user):
        """Test that a user without role has no permissions."""
        await role_service.seed_default_roles_and_permissions(db_session)

        has_perm = await role_service.user_has_permission(
            db_session,
            user_id=test_user.id,
            resource="users",
            action="delete",
        )
        assert has_perm is False

    @pytest.mark.asyncio
    async def test_get_user_permissions(self, db_session, test_user):
        """Test getting all permissions for a user."""
        await role_service.seed_default_roles_and_permissions(db_session)

        # Assign user role
        user_role = await role_service.get_role_by_name(db_session, "user")
        await role_service.assign_role_to_user(
            db_session, user_id=test_user.id, role_id=user_role.id,
        )

        permissions = await role_service.get_user_permissions(db_session, test_user.id)
        assert len(permissions) >= 6  # user role has 6 permissions
        assert "users:read" in permissions
        assert "companies:read" in permissions


class TestRBACEndpoints:
    """Tests for RBAC API endpoints."""

    @pytest.mark.asyncio
    async def test_list_permissions(self, client, db_session, admin_token_headers):
        """Test listing all permissions."""
        await role_service.seed_default_roles_and_permissions(db_session)

        response = await client.get(
            "/api/v1/roles/permissions",
            headers=admin_token_headers,
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) >= 23
        assert data[0]["name"] is not None
        assert data[0]["resource"] is not None

    @pytest.mark.asyncio
    async def test_list_roles(self, client, db_session, admin_token_headers):
        """Test listing all roles."""
        await role_service.seed_default_roles_and_permissions(db_session)

        response = await client.get(
            "/api/v1/roles/roles",
            headers=admin_token_headers,
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) >= 4
        role_names = [r["name"] for r in data]
        assert "admin" in role_names
        assert "viewer" in role_names

    @pytest.mark.asyncio
    async def test_assign_role_endpoint(self, client, db_session, admin_token_headers, test_user):
        """Test assigning a role via API."""
        await role_service.seed_default_roles_and_permissions(db_session)
        user_role = await role_service.get_role_by_name(db_session, "user")

        response = await client.post(
            f"/api/v1/roles/users/{test_user.id}/roles",
            headers=admin_token_headers,
            json={"user_id": test_user.id, "role_id": user_role.id},
        )
        assert response.status_code == status.HTTP_201_CREATED

    @pytest.mark.asyncio
    async def test_check_permission_endpoint(self, client, db_session, admin_token_headers):
        """Test checking a permission via API."""
        response = await client.post(
            "/api/v1/roles/check-permission",
            headers=admin_token_headers,
            json={"resource": "users", "action": "admin"},
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["has_permission"] is True  # superuser

    @pytest.mark.asyncio
    async def test_unauthorized_access(self, client, db_session):
        """Test that unauthenticated access is rejected."""
        response = await client.get("/api/v1/roles/permissions")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
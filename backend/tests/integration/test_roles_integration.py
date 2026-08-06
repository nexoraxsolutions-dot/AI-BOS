"""Integration tests for roles and permissions API endpoints."""
import pytest
from fastapi import status
from httpx import AsyncClient

from app.schemas.role import PermissionCreate, RoleCreate, UserRoleAssignment

pytestmark = pytest.mark.asyncio


class TestPermissionsEndpoints:
    """Integration tests for permissions endpoints."""

    async def test_list_permissions_success(self, client: AsyncClient, user_token_headers):
        """Test listing all permissions."""
        # Act
        response = await client.get("/api/v1/roles/permissions", headers=user_token_headers)
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)

    async def test_list_permissions_unauthorized(self, client: AsyncClient):
        """Test listing permissions without authentication."""
        # Act
        response = await client.get("/api/v1/roles/permissions")
        
        # Assert
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_create_permission_success(self, client: AsyncClient, admin_token_headers, db_session):
        """Test successful permission creation."""
        # Arrange
        permission_data = {
            "name": "test_permission",
            "resource": "test_resource",
            "action": "test_action",
            "description": "A test permission"
        }
        
        # Act
        response = await client.post(
            "/api/v1/roles/permissions",
            json=permission_data,
            headers=admin_token_headers
        )
        
        # Assert
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["name"] == "test_permission"
        assert data["resource"] == "test_resource"
        assert data["action"] == "test_action"
        assert "id" in data
        
        # Verify permission was persisted in database
        from app.services.role import get_permission_by_name
        permission = await get_permission_by_name(db_session, "test_permission")
        assert permission is not None
        assert permission.resource == "test_resource"

    async def test_create_permission_duplicate(self, client: AsyncClient, admin_token_headers, db_session):
        """Test creating duplicate permission."""
        # Arrange - Create first permission
        permission_data = {
            "name": "duplicate_permission",
            "resource": "test_resource",
            "action": "test_action",
            "description": "First permission"
        }
        response1 = await client.post(
            "/api/v1/roles/permissions",
            json=permission_data,
            headers=admin_token_headers
        )
        assert response1.status_code == status.HTTP_201_CREATED
        
        # Try to create duplicate
        response2 = await client.post(
            "/api/v1/roles/permissions",
            json=permission_data,
            headers=admin_token_headers
        )
        
        # Assert
        assert response2.status_code == status.HTTP_400_BAD_REQUEST
        data = response2.json()
        assert "detail" in data

    async def test_create_permission_unauthorized(self, client: AsyncClient):
        """Test creating permission without authentication."""
        # Arrange
        permission_data = {
            "name": "test_permission",
            "resource": "test_resource",
            "action": "test_action"
        }
        
        # Act
        response = await client.post(
            "/api/v1/roles/permissions",
            json=permission_data
        )
        
        # Assert
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_create_permission_validation_errors(self, client: AsyncClient, admin_token_headers):
        """Test permission creation with validation errors."""
        # Test missing required fields
        response = await client.post(
            "/api/v1/roles/permissions",
            json={},
            headers=admin_token_headers
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        
        # Test missing name
        response = await client.post(
            "/api/v1/roles/permissions",
            json={"resource": "test", "action": "test"},
            headers=admin_token_headers
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    async def test_delete_permission_success(self, client: AsyncClient, admin_token_headers, db_session):
        """Test successful permission deletion."""
        # Arrange - Create a permission to delete
        from app.services.role import create_permission
        permission = await create_permission(
            db_session,
            name="to_delete_permission",
            resource="test_resource",
            action="delete_action",
            description="Will be deleted"
        )
        permission_id = permission.id
        
        # Act
        response = await client.delete(
            f"/api/v1/roles/permissions/{permission_id}",
            headers=admin_token_headers
        )
        
        # Assert
        assert response.status_code == status.HTTP_204_NO_CONTENT
        
        # Verify permission was deleted
        from app.services.role import get_permission_by_name
        deleted_permission = await get_permission_by_name(db_session, "to_delete_permission")
        assert deleted_permission is None

    async def test_delete_permission_not_found(self, client: AsyncClient, admin_token_headers):
        """Test deleting non-existent permission."""
        # Act
        response = await client.delete(
            "/api/v1/roles/permissions/99999",
            headers=admin_token_headers
        )
        
        # Assert
        assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_delete_permission_unauthorized(self, client: AsyncClient):
        """Test deleting permission without authentication."""
        # Act
        response = await client.delete("/api/v1/roles/permissions/1")
        
        # Assert
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestRolesEndpoints:
    """Integration tests for roles endpoints."""

    async def test_list_roles_success(self, client: AsyncClient, user_token_headers):
        """Test listing all roles."""
        # Act
        response = await client.get("/api/v1/roles/roles", headers=user_token_headers)
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)

    async def test_list_roles_unauthorized(self, client: AsyncClient):
        """Test listing roles without authentication."""
        # Act
        response = await client.get("/api/v1/roles/roles")
        
        # Assert
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_get_role_success(self, client: AsyncClient, user_token_headers, test_role):
        """Test getting a specific role."""
        # Act
        response = await client.get(
            f"/api/v1/roles/roles/{test_role.id}",
            headers=user_token_headers
        )
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == test_role.id
        assert data["name"] == test_role.name

    async def test_get_role_not_found(self, client: AsyncClient, user_token_headers):
        """Test getting non-existent role."""
        # Act
        response = await client.get(
            "/api/v1/roles/roles/99999",
            headers=user_token_headers
        )
        
        # Assert
        assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_create_role_success(self, client: AsyncClient, admin_token_headers, db_session):
        """Test successful role creation."""
        # Arrange - Create a permission first
        from app.services.role import create_permission
        permission = await create_permission(
            db_session,
            name="role_test_permission",
            resource="test",
            action="test",
            description="Test permission for role"
        )
        
        role_data = {
            "name": "Test Role",
            "description": "A test role",
            "permission_ids": [permission.id]
        }
        
        # Act
        response = await client.post(
            "/api/v1/roles/roles",
            json=role_data,
            headers=admin_token_headers
        )
        
        # Assert
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["name"] == "Test Role"
        assert data["description"] == "A test role"
        assert "id" in data
        
        # Verify role was persisted in database
        from app.services.role import get_role_by_name
        role = await get_role_by_name(db_session, "Test Role")
        assert role is not None
        assert len(role.permissions) == 1

    async def test_create_role_duplicate_name(self, client: AsyncClient, admin_token_headers, test_role):
        """Test creating role with duplicate name."""
        # Arrange
        role_data = {
            "name": test_role.name,  # Already exists
            "description": "Duplicate role"
        }
        
        # Act
        response = await client.post(
            "/api/v1/roles/roles",
            json=role_data,
            headers=admin_token_headers
        )
        
        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert "detail" in data

    async def test_create_role_unauthorized(self, client: AsyncClient):
        """Test creating role without authentication."""
        # Arrange
        role_data = {
            "name": "Test Role",
            "description": "A test role"
        }
        
        # Act
        response = await client.post(
            "/api/v1/roles/roles",
            json=role_data
        )
        
        # Assert
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_create_role_validation_errors(self, client: AsyncClient, admin_token_headers):
        """Test role creation with validation errors."""
        # Test missing required fields
        response = await client.post(
            "/api/v1/roles/roles",
            json={},
            headers=admin_token_headers
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        
        # Test missing name
        response = await client.post(
            "/api/v1/roles/roles",
            json={"description": "Test role"},
            headers=admin_token_headers
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    async def test_update_role_success(self, client: AsyncClient, admin_token_headers, test_role, db_session):
        """Test successful role update."""
        # Arrange - Create a new permission
        from app.services.role import create_permission
        new_permission = await create_permission(
            db_session,
            name="update_test_permission",
            resource="update_test",
            action="update_test",
            description="Test permission for role update"
        )
        
        update_data = {
            "name": "Updated Test Role",
            "description": "Updated description",
            "permission_ids": [new_permission.id]
        }
        
        # Act
        response = await client.put(
            f"/api/v1/roles/roles/{test_role.id}",
            json=update_data,
            headers=admin_token_headers
        )
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["name"] == "Updated Test Role"
        assert data["description"] == "Updated description"
        
        # Verify in database
        from app.services.role import get_role_by_name
        updated_role = await get_role_by_name(db_session, "Updated Test Role")
        assert updated_role is not None
        assert updated_role.description == "Updated description"

    async def test_update_role_not_found(self, client: AsyncClient, admin_token_headers):
        """Test updating non-existent role."""
        # Arrange
        update_data = {"name": "Updated Role"}
        
        # Act
        response = await client.put(
            "/api/v1/roles/roles/99999",
            json=update_data,
            headers=admin_token_headers
        )
        
        # Assert
        assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_update_role_unauthorized(self, client: AsyncClient, test_role, user_token_headers):
        """Test that regular users cannot update roles."""
        # Arrange
        update_data = {"name": "Hacked Role"}
        
        # Act
        response = await client.put(
            f"/api/v1/roles/roles/{test_role.id}",
            json=update_data,
            headers=user_token_headers
        )
        
        # Assert - Should be forbidden (requires superuser)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    async def test_delete_role_success(self, client: AsyncClient, admin_token_headers, db_session):
        """Test successful role deletion."""
        # Arrange - Create a role to delete
        from app.services.role import create_role
        role_to_delete = await create_role(
            db_session,
            name="To Delete Role",
            description="Will be deleted",
            permission_ids=[]
        )
        role_id = role_to_delete.id
        
        # Act
        response = await client.delete(
            f"/api/v1/roles/roles/{role_id}",
            headers=admin_token_headers
        )
        
        # Assert
        assert response.status_code == status.HTTP_204_NO_CONTENT
        
        # Verify role was deleted from database
        from app.services.role import get_role_by_name
        deleted_role = await get_role_by_name(db_session, "To Delete Role")
        assert deleted_role is None

    async def test_delete_role_not_found(self, client: AsyncClient, admin_token_headers):
        """Test deleting non-existent role."""
        # Act
        response = await client.delete(
            "/api/v1/roles/roles/99999",
            headers=admin_token_headers
        )
        
        # Assert
        assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_delete_role_unauthorized(self, client: AsyncClient, test_role, user_token_headers):
        """Test that regular users cannot delete roles."""
        # Act
        response = await client.delete(
            f"/api/v1/roles/roles/{test_role.id}",
            headers=user_token_headers
        )
        
        # Assert - Should be forbidden (requires superuser)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    async def test_delete_system_role(self, client: AsyncClient, admin_token_headers, db_session):
        """Test that system roles cannot be deleted."""
        # Arrange - Create a system role
        from app.models.role import Role
        
        system_role = Role(
            name="System Role",
            description="A system role",
            is_system_role=True,
            permissions=[]
        )
        db_session.add(system_role)
        await db_session.commit()
        await db_session.refresh(system_role)
        
        # Act
        response = await client.delete(
            f"/api/v1/roles/roles/{system_role.id}",
            headers=admin_token_headers
        )
        
        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestUserRoleAssignments:
    """Integration tests for user role assignment endpoints."""

    async def test_get_user_roles_success(self, client: AsyncClient, user_token_headers, test_user, test_role, db_session):
        """Test getting roles for a user."""
        # Arrange - Assign role to user
        from app.services.role import assign_role_to_user
        await assign_role_to_user(db_session, test_user.id, test_role.id, assigned_by=test_user.id)
        
        # Act
        response = await client.get(
            f"/api/v1/roles/users/{test_user.id}/roles",
            headers=user_token_headers
        )
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        role_names = [r["name"] for r in data]
        assert test_role.name in role_names

    async def test_get_user_roles_not_found(self, client: AsyncClient, user_token_headers):
        """Test getting roles for non-existent user."""
        # Act - API returns 200 with empty list for non-existent users
        response = await client.get(
            "/api/v1/roles/users/99999/roles",
            headers=user_token_headers
        )
        
        # Assert - API returns empty list instead of 404
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)

    async def test_assign_role_to_user_success(self, client: AsyncClient, admin_token_headers, test_user, test_role, db_session):
        """Test successfully assigning a role to a user."""
        # Arrange - Remove any existing roles first
        from app.services.role import get_user_roles, remove_role_from_user
        existing_roles = await get_user_roles(db_session, test_user.id)
        for role in existing_roles:
            await remove_role_from_user(db_session, test_user.id, role.id)
        
        # Note: API expects user_id in both URL and body
        assignment_data = {
            "user_id": test_user.id,
            "role_id": test_role.id
        }
        
        # Act
        response = await client.post(
            f"/api/v1/roles/users/{test_user.id}/roles",
            json=assignment_data,
            headers=admin_token_headers
        )
        
        # Assert
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["user_id"] == test_user.id
        assert data["role_id"] == test_role.id
        
        # Verify in database
        from app.services.role import get_user_roles
        user_roles = await get_user_roles(db_session, test_user.id)
        role_ids = [r.id for r in user_roles]
        assert test_role.id in role_ids

    async def test_assign_role_to_user_not_found(self, client: AsyncClient, admin_token_headers):
        """Test assigning role to non-existent user."""
        # Arrange - API returns 400 for non-existent users
        assignment_data = {
            "user_id": 99999,
            "role_id": 1
        }
        
        # Act
        response = await client.post(
            "/api/v1/roles/users/99999/roles",
            json=assignment_data,
            headers=admin_token_headers
        )
        
        # Assert - API returns 400 for non-existent user
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    async def test_assign_role_unauthorized(self, client: AsyncClient, test_user, test_role, user_token_headers):
        """Test that regular users cannot assign roles."""
        # Arrange
        assignment_data = {"role_id": test_role.id}
        
        # Act
        response = await client.post(
            f"/api/v1/roles/users/{test_user.id}/roles",
            json=assignment_data,
            headers=user_token_headers
        )
        
        # Assert - Should be forbidden (requires superuser)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    async def test_remove_role_from_user_success(self, client: AsyncClient, admin_token_headers, test_user, test_role, db_session):
        """Test successfully removing a role from a user."""
        # Arrange - Assign role first
        from app.services.role import assign_role_to_user
        await assign_role_to_user(db_session, test_user.id, test_role.id, assigned_by=test_user.id)
        
        # Act
        response = await client.delete(
            f"/api/v1/roles/users/{test_user.id}/roles/{test_role.id}",
            headers=admin_token_headers
        )
        
        # Assert
        assert response.status_code == status.HTTP_204_NO_CONTENT
        
        # Verify role was removed
        from app.services.role import get_user_roles
        user_roles = await get_user_roles(db_session, test_user.id)
        role_ids = [r.id for r in user_roles]
        assert test_role.id not in role_ids

    async def test_remove_role_from_user_not_found(self, client: AsyncClient, admin_token_headers):
        """Test removing role from non-existent user."""
        # Act - API returns 400 for non-existent user
        response = await client.delete(
            "/api/v1/roles/users/99999/roles/1",
            headers=admin_token_headers
        )
        
        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    async def test_remove_role_unauthorized(self, client: AsyncClient, test_user, test_role, user_token_headers):
        """Test that regular users cannot remove roles."""
        # Act
        response = await client.delete(
            f"/api/v1/roles/users/{test_user.id}/roles/{test_role.id}",
            headers=user_token_headers
        )
        
        # Assert - Should be forbidden (requires superuser)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    async def test_get_role_users_success(self, client: AsyncClient, user_token_headers, test_role, test_user, db_session):
        """Test getting all users with a specific role."""
        # Arrange - Assign role to user
        from app.services.role import assign_role_to_user
        await assign_role_to_user(db_session, test_user.id, test_role.id, assigned_by=test_user.id)
        
        # Act
        response = await client.get(
            f"/api/v1/roles/roles/{test_role.id}/users",
            headers=user_token_headers
        )
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        user_ids = [u["id"] for u in data]
        assert test_user.id in user_ids

    async def test_get_role_users_not_found(self, client: AsyncClient, user_token_headers):
        """Test getting users for non-existent role."""
        # Act - API returns 200 with empty list for non-existent roles
        response = await client.get(
            "/api/v1/roles/roles/99999/users",
            headers=user_token_headers
        )
        
        # Assert - API returns empty list instead of 404
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)


class TestPermissionChecking:
    """Integration tests for permission checking endpoints."""

    async def test_get_user_permissions_success(self, client: AsyncClient, user_token_headers, test_user, test_role, db_session):
        """Test getting all permissions for a user."""
        # Arrange - Assign role with permissions to user
        from app.services.role import assign_role_to_user
        await assign_role_to_user(db_session, test_user.id, test_role.id, assigned_by=test_user.id)
        
        # Act
        response = await client.get(
            f"/api/v1/roles/users/{test_user.id}/permissions",
            headers=user_token_headers
        )
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["user_id"] == test_user.id
        assert data["email"] == test_user.email
        assert "permissions" in data
        assert "roles" in data
        assert isinstance(data["permissions"], list)
        assert isinstance(data["roles"], list)

    async def test_get_user_permissions_not_found(self, client: AsyncClient, user_token_headers):
        """Test getting permissions for non-existent user."""
        # Act
        response = await client.get(
            "/api/v1/roles/users/99999/permissions",
            headers=user_token_headers
        )
        
        # Assert
        assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_check_permission_success(self, client: AsyncClient, user_token_headers, test_user, test_role, db_session):
        """Test checking if user has specific permission."""
        # Arrange - Assign role to user
        from app.services.role import assign_role_to_user, get_role_by_id
        await assign_role_to_user(db_session, test_user.id, test_role.id, assigned_by=test_user.id)
        
        # Get a permission from the role
        role = await get_role_by_id(db_session, test_role.id)
        if role.permissions:
            permission = role.permissions[0]
            check_data = {
                "resource": permission.resource,
                "action": permission.action
            }
            
            # Act
            response = await client.post(
                "/api/v1/roles/check-permission",
                json=check_data,
                headers=user_token_headers
            )
            
            # Assert
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert "has_permission" in data
            assert data["resource"] == permission.resource
            assert data["action"] == permission.action

    async def test_check_permission_denied(self, client: AsyncClient, user_token_headers):
        """Test checking permission that user doesn't have."""
        # Arrange
        check_data = {
            "resource": "nonexistent_resource",
            "action": "nonexistent_action"
        }
        
        # Act
        response = await client.post(
            "/api/v1/roles/check-permission",
            json=check_data,
            headers=user_token_headers
        )
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["has_permission"] is False

    async def test_rbac_crud_workflow(self, client: AsyncClient, admin_token_headers, test_user, db_session):
        """Test complete RBAC workflow: permission -> role -> assignment."""
        # Create permission
        permission_data = {
            "name": "workflow_permission",
            "resource": "workflow_resource",
            "action": "workflow_action",
            "description": "Permission for workflow test"
        }
        permission_response = await client.post(
            "/api/v1/roles/permissions",
            json=permission_data,
            headers=admin_token_headers
        )
        assert permission_response.status_code == status.HTTP_201_CREATED
        permission_id = permission_response.json()["id"]
        
        # Create role with permission
        role_data = {
            "name": "Workflow Role",
            "description": "Role for workflow test",
            "permission_ids": [permission_id]
        }
        role_response = await client.post(
            "/api/v1/roles/roles",
            json=role_data,
            headers=admin_token_headers
        )
        assert role_response.status_code == status.HTTP_201_CREATED
        role_id = role_response.json()["id"]
        
        # Assign role to user
        assignment_data = {
            "user_id": test_user.id,
            "role_id": role_id
        }
        assignment_response = await client.post(
            f"/api/v1/roles/users/{test_user.id}/roles",
            json=assignment_data,
            headers=admin_token_headers
        )
        assert assignment_response.status_code == status.HTTP_201_CREATED
        
        # Verify user has role
        roles_response = await client.get(
            f"/api/v1/roles/users/{test_user.id}/roles",
            headers=admin_token_headers
        )
        assert roles_response.status_code == status.HTTP_200_OK
        role_names = [r["name"] for r in roles_response.json()]
        assert "Workflow Role" in role_names
        
        # Remove role from user
        remove_response = await client.delete(
            f"/api/v1/roles/users/{test_user.id}/roles/{role_id}",
            headers=admin_token_headers
        )
        assert remove_response.status_code == status.HTTP_204_NO_CONTENT
        
        # Delete role
        delete_role_response = await client.delete(
            f"/api/v1/roles/roles/{role_id}",
            headers=admin_token_headers
        )
        assert delete_role_response.status_code == status.HTTP_204_NO_CONTENT
        
        # Delete permission
        delete_permission_response = await client.delete(
            f"/api/v1/roles/permissions/{permission_id}",
            headers=admin_token_headers
        )
        assert delete_permission_response.status_code == status.HTTP_204_NO_CONTENT
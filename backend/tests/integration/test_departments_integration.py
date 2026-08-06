"""Integration tests for departments API endpoints."""
import pytest
from fastapi import status
from httpx import AsyncClient

from app.schemas.department import DepartmentCreate, DepartmentUpdate

pytestmark = pytest.mark.asyncio


class TestDepartmentsEndpoints:
    """Integration tests for departments endpoints."""

    async def test_create_department_success(self, client: AsyncClient, admin_token_headers, test_company, db_session):
        """Test successful department creation via API."""
        # Arrange
        department_data = {
            "name": "Engineering",
            "description": "Software engineering department",
            "company_id": test_company.id,
            "budget": "$100,000",
            "location": "Building A",
            "is_active": True
        }
        
        # Act
        response = await client.post(
            "/api/v1/departments/",
            json=department_data,
            headers=admin_token_headers
        )
        
        # Assert
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["name"] == "Engineering"
        assert data["description"] == "Software engineering department"
        assert data["company_id"] == test_company.id
        assert data["budget"] == "$100,000"
        assert data["location"] == "Building A"
        assert "id" in data
        
        # Verify department was persisted in database
        from app.services.department import get_department
        department = await get_department(db_session, data["id"])
        assert department is not None
        assert department.name == "Engineering"
        assert department.company_id == test_company.id

    async def test_create_department_unauthorized(self, client: AsyncClient, test_company):
        """Test department creation without authentication."""
        # Arrange
        department_data = {
            "name": "Test Department",
            "company_id": test_company.id
        }
        
        # Act
        response = await client.post("/api/v1/departments/", json=department_data)
        
        # Assert
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_create_department_validation_errors(self, client: AsyncClient, admin_token_headers, test_company):
        """Test department creation with validation errors."""
        # Test missing required fields
        response = await client.post(
            "/api/v1/departments/",
            json={},
            headers=admin_token_headers
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        
        # Test missing name
        response = await client.post(
            "/api/v1/departments/",
            json={"company_id": test_company.id},
            headers=admin_token_headers
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        
        # Test missing company_id
        response = await client.post(
            "/api/v1/departments/",
            json={"name": "Test Department"},
            headers=admin_token_headers
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    async def test_get_department_success(self, client: AsyncClient, user_token_headers, test_department):
        """Test getting a department by ID."""
        # Act
        response = await client.get(
            f"/api/v1/departments/{test_department.id}",
            headers=user_token_headers
        )
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == test_department.id
        assert data["name"] == test_department.name
        assert data["company_id"] == test_department.company_id

    async def test_get_department_not_found(self, client: AsyncClient, user_token_headers):
        """Test getting non-existent department."""
        # Act
        response = await client.get(
            "/api/v1/departments/99999",
            headers=user_token_headers
        )
        
        # Assert
        assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_list_departments_success(self, client: AsyncClient, user_token_headers, test_department):
        """Test getting list of departments."""
        # Act
        response = await client.get("/api/v1/departments/", headers=user_token_headers)
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert isinstance(data["items"], list)
        assert data["total"] >= 1
        # Check that test_department is in the list
        department_names = [d["name"] for d in data["items"]]
        assert test_department.name in department_names

    async def test_list_departments_with_pagination(self, client: AsyncClient, user_token_headers):
        """Test getting departments with pagination."""
        # Act
        response = await client.get(
            "/api/v1/departments/?skip=0&limit=10",
            headers=user_token_headers
        )
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data
        assert len(data["items"]) <= 10
        assert data["page_size"] == 10

    async def test_list_departments_with_search(self, client: AsyncClient, user_token_headers, test_department):
        """Test searching departments."""
        # Act
        response = await client.get(
            f"/api/v1/departments/?search={test_department.name}",
            headers=user_token_headers
        )
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total"] >= 1
        # Check that test_department is in results
        department_names = [d["name"] for d in data["items"]]
        assert test_department.name in department_names

    async def test_list_departments_with_filters(self, client: AsyncClient, user_token_headers, test_department):
        """Test filtering departments."""
        # Act - filter by company_id
        response = await client.get(
            f"/api/v1/departments/?company_id={test_department.company_id}",
            headers=user_token_headers
        )
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        # All returned departments should belong to the test company
        for dept in data["items"]:
            assert dept["company_id"] == test_department.company_id

    async def test_list_departments_with_sorting(self, client: AsyncClient, user_token_headers, test_company, db_session):
        """Test sorting departments."""
        # Arrange - Create multiple departments
        from app.services.department import create_department
        from app.schemas.department import DepartmentCreate
        
        dept1 = await create_department(db_session, DepartmentCreate(
            name="Alpha Department",
            description="First department",
            company_id=test_company.id
        ))
        dept2 = await create_department(db_session, DepartmentCreate(
            name="Beta Department",
            description="Second department",
            company_id=test_company.id
        ))
        
        # Act - sort by name ascending
        response = await client.get(
            "/api/v1/departments/?sort_by=name&sort_order=asc",
            headers=user_token_headers
        )
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        if len(data["items"]) > 1:
            # Check that departments are sorted by name
            names = [d["name"] for d in data["items"]]
            assert names == sorted(names)

    async def test_get_department_stats(self, client: AsyncClient, user_token_headers, test_department):
        """Test getting department statistics."""
        # Act
        response = await client.get(
            "/api/v1/departments/stats",
            headers=user_token_headers
        )
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "total_departments" in data
        assert "active_departments" in data
        assert "inactive_departments" in data
        assert "total_companies_with_departments" in data
        assert isinstance(data["total_departments"], int)
        assert data["total_departments"] >= 1

    async def test_update_department_success(self, client: AsyncClient, admin_token_headers, test_department, db_session):
        """Test successful department update."""
        # Arrange
        update_data = {
            "name": "Updated Department",
            "description": "Updated description",
            "budget": "$150,000"
        }
        
        # Act
        response = await client.put(
            f"/api/v1/departments/{test_department.id}",
            json=update_data,
            headers=admin_token_headers
        )
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["name"] == "Updated Department"
        assert data["description"] == "Updated description"
        assert data["budget"] == "$150,000"
        
        # Verify in database
        await db_session.refresh(test_department)
        assert test_department.name == "Updated Department"
        assert test_department.description == "Updated description"

    async def test_update_department_not_found(self, client: AsyncClient, admin_token_headers):
        """Test updating non-existent department."""
        # Arrange
        update_data = {"name": "Updated Name"}
        
        # Act
        response = await client.put(
            "/api/v1/departments/99999",
            json=update_data,
            headers=admin_token_headers
        )
        
        # Assert
        assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_update_department_unauthorized(self, client: AsyncClient, test_department, user_token_headers):
        """Test that regular users cannot update departments."""
        # Arrange
        update_data = {"name": "Hacked Name"}
        
        # Act - Try to update with regular user token
        response = await client.put(
            f"/api/v1/departments/{test_department.id}",
            json=update_data,
            headers=user_token_headers
        )
        
        # Assert - Should be forbidden (requires superuser)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    async def test_delete_department_success(self, client: AsyncClient, admin_token_headers, test_company, db_session):
        """Test successful department deletion."""
        # Arrange - Create a department to delete
        from app.services.department import create_department
        from app.schemas.department import DepartmentCreate
        dept_to_delete = await create_department(db_session, DepartmentCreate(
            name="To Delete",
            description="Will be deleted",
            company_id=test_company.id
        ))
        dept_id = dept_to_delete.id
        
        # Act
        response = await client.delete(
            f"/api/v1/departments/{dept_id}",
            headers=admin_token_headers
        )
        
        # Assert
        assert response.status_code == status.HTTP_204_NO_CONTENT
        
        # Verify department was deleted from database
        from app.services.department import get_department
        deleted_dept = await get_department(db_session, dept_id)
        assert deleted_dept is None

    async def test_delete_department_not_found(self, client: AsyncClient, admin_token_headers):
        """Test deleting non-existent department."""
        # Act
        response = await client.delete(
            "/api/v1/departments/99999",
            headers=admin_token_headers
        )
        
        # Assert
        assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_delete_department_unauthorized(self, client: AsyncClient, test_department, user_token_headers):
        """Test that regular users cannot delete departments."""
        # Act - Try to delete with regular user token
        response = await client.delete(
            f"/api/v1/departments/{test_department.id}",
            headers=user_token_headers
        )
        
        # Assert - Should be forbidden (requires superuser)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    async def test_department_crud_workflow(self, client: AsyncClient, admin_token_headers, test_company, db_session):
        """Test complete CRUD workflow for departments."""
        # Create
        create_data = {
            "name": "Workflow Department",
            "description": "Testing CRUD workflow",
            "company_id": test_company.id,
            "budget": "$75,000",
            "location": "Building C"
        }
        create_response = await client.post(
            "/api/v1/departments/",
            json=create_data,
            headers=admin_token_headers
        )
        assert create_response.status_code == status.HTTP_201_CREATED
        dept_id = create_response.json()["id"]
        
        # Read
        read_response = await client.get(
            f"/api/v1/departments/{dept_id}",
            headers=admin_token_headers
        )
        assert read_response.status_code == status.HTTP_200_OK
        assert read_response.json()["name"] == "Workflow Department"
        
        # Update
        update_data = {"name": "Updated Workflow Department", "budget": "$80,000"}
        update_response = await client.put(
            f"/api/v1/departments/{dept_id}",
            json=update_data,
            headers=admin_token_headers
        )
        assert update_response.status_code == status.HTTP_200_OK
        assert update_response.json()["name"] == "Updated Workflow Department"
        
        # Delete
        delete_response = await client.delete(
            f"/api/v1/departments/{dept_id}",
            headers=admin_token_headers
        )
        assert delete_response.status_code == status.HTTP_204_NO_CONTENT
        
        # Verify deletion
        verify_response = await client.get(
            f"/api/v1/departments/{dept_id}",
            headers=admin_token_headers
        )
        assert verify_response.status_code == status.HTTP_404_NOT_FOUND
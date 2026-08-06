"""Integration tests for company API endpoints."""
import pytest
from fastapi import status
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


class TestCompanyEndpoints:
    """Integration tests for company endpoints."""

    async def test_create_company_success(self, client: AsyncClient, admin_token_headers, db_session):
        """Test successful company creation via API."""
        # Arrange
        company_data = {
            "name": "New Test Company",
            "domain": "newtestcompany.com",
            "email": "info@newtestcompany.com",
            "industry": "Technology",
            "subscription_plan": "premium",
            "employee_count": 100
        }
        
        # Act
        response = await client.post(
            "/api/v1/companies/",
            json=company_data,
            headers=admin_token_headers
        )
        
        # Assert
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["name"] == "New Test Company"
        assert data["domain"] == "newtestcompany.com"
        assert data["email"] == "info@newtestcompany.com"
        assert "id" in data
        
        # Verify company was persisted in database
        from app.services.company import get_company_by_domain
        company = await get_company_by_domain(db_session, "newtestcompany.com")
        assert company is not None
        assert company.name == "New Test Company"

    async def test_create_company_unauthorized(self, client: AsyncClient):
        """Test company creation without authentication."""
        # Arrange
        company_data = {
            "name": "Test Company",
            "domain": "testcompany.com"
        }
        
        # Act
        response = await client.post("/api/v1/companies/", json=company_data)
        
        # Assert
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_get_company_success(self, client: AsyncClient, test_company, admin_token_headers):
        """Test getting a company by ID."""
        # Act
        response = await client.get(
            f"/api/v1/companies/{test_company.id}",
            headers=admin_token_headers
        )
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == test_company.id
        assert data["name"] == test_company.name
        assert data["domain"] == test_company.domain

    async def test_get_company_not_found(self, client: AsyncClient, admin_token_headers):
        """Test getting non-existent company."""
        # Act
        response = await client.get(
            "/api/v1/companies/99999",
            headers=admin_token_headers
        )
        
        # Assert
        assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_get_company_by_domain_success(self, client: AsyncClient, test_company, admin_token_headers):
        """Test getting a company by domain."""
        # Act
        response = await client.get(
            f"/api/v1/companies/domain/{test_company.domain}",
            headers=admin_token_headers
        )
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["domain"] == test_company.domain
        assert data["name"] == test_company.name

    async def test_get_company_by_domain_not_found(self, client: AsyncClient, admin_token_headers):
        """Test getting non-existent company by domain."""
        # Act
        response = await client.get(
            "/api/v1/companies/domain/nonexistent.com",
            headers=admin_token_headers
        )
        
        # Assert
        assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_get_companies_list(self, client: AsyncClient, admin_token_headers, test_company):
        """Test getting list of companies."""
        # Act
        response = await client.get("/api/v1/companies/", headers=admin_token_headers)
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert isinstance(data["items"], list)
        assert data["total"] >= 1

    async def test_get_companies_with_pagination(self, client: AsyncClient, admin_token_headers):
        """Test getting companies with pagination."""
        # Act
        response = await client.get(
            "/api/v1/companies/?skip=0&limit=10",
            headers=admin_token_headers
        )
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert len(data["items"]) <= 10

    async def test_get_companies_with_search(self, client: AsyncClient, admin_token_headers, test_company):
        """Test searching companies."""
        # Act
        response = await client.get(
            f"/api/v1/companies/?search={test_company.name}",
            headers=admin_token_headers
        )
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total"] >= 1
        # Check that the test company is in results
        company_names = [c["name"] for c in data["items"]]
        assert test_company.name in company_names

    async def test_get_companies_with_filters(self, client: AsyncClient, admin_token_headers, test_company):
        """Test filtering companies."""
        # Act - filter by active status
        response = await client.get(
            "/api/v1/companies/?is_active=true",
            headers=admin_token_headers
        )
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        # All returned companies should be active
        for company in data["items"]:
            assert company["is_active"] is True

    async def test_get_companies_with_sorting(self, client: AsyncClient, admin_token_headers):
        """Test sorting companies."""
        # Act - sort by name ascending
        response = await client.get(
            "/api/v1/companies/?sort_by=name&sort_order=asc",
            headers=admin_token_headers
        )
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        if len(data["items"]) > 1:
            # Check that companies are sorted by name
            names = [c["name"] for c in data["items"]]
            assert names == sorted(names)

    async def test_update_company_success(self, client: AsyncClient, test_company, admin_token_headers, db_session):
        """Test successful company update."""
        # Arrange
        update_data = {
            "name": "Updated Company Name",
            "industry": "Finance"
        }
        
        # Act
        response = await client.put(
            f"/api/v1/companies/{test_company.id}",
            json=update_data,
            headers=admin_token_headers
        )
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["name"] == "Updated Company Name"
        assert data["industry"] == "Finance"
        
        # Verify in database
        await db_session.refresh(test_company)
        assert test_company.name == "Updated Company Name"

    async def test_update_company_not_found(self, client: AsyncClient, admin_token_headers):
        """Test updating non-existent company."""
        # Arrange
        update_data = {"name": "Updated Name"}
        
        # Act
        response = await client.put(
            "/api/v1/companies/99999",
            json=update_data,
            headers=admin_token_headers
        )
        
        # Assert
        assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_delete_company_success(self, client: AsyncClient, test_company, admin_token_headers, db_session):
        """Test successful company deletion."""
        # Act
        response = await client.delete(
            f"/api/v1/companies/{test_company.id}",
            headers=admin_token_headers
        )
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "message" in data
        
        # Verify company was deleted from database
        from app.services.company import get_company
        deleted_company = await get_company(db_session, test_company.id)
        assert deleted_company is None

    async def test_delete_company_not_found(self, client: AsyncClient, admin_token_headers):
        """Test deleting non-existent company."""
        # Act
        response = await client.delete(
            "/api/v1/companies/99999",
            headers=admin_token_headers
        )
        
        # Assert
        assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_get_company_stats(self, client: AsyncClient, admin_token_headers):
        """Test getting company statistics."""
        # Act
        response = await client.get(
            "/api/v1/companies/stats",
            headers=admin_token_headers
        )
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "total_companies" in data
        assert "active_companies" in data
        assert "inactive_companies" in data
        assert "total_users_across_companies" in data
        assert isinstance(data["total_companies"], int)

    async def test_get_company_with_user_count(self, client: AsyncClient, test_company, admin_token_headers):
        """Test getting company with user count."""
        # Act
        response = await client.get(
            f"/api/v1/companies/{test_company.id}/with-user-count",
            headers=admin_token_headers
        )
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == test_company.id
        assert "user_count" in data
        assert isinstance(data["user_count"], int)

    async def test_company_validation_errors(self, client: AsyncClient, admin_token_headers):
        """Test company creation with validation errors."""
        # Test missing required fields
        response = await client.post(
            "/api/v1/companies/",
            json={},
            headers=admin_token_headers
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        
        # Test invalid domain
        response = await client.post(
            "/api/v1/companies/",
            json={
                "name": "Test Company",
                "domain": "invalid domain with spaces"
            },
            headers=admin_token_headers
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        
        # Test missing name
        response = await client.post(
            "/api/v1/companies/",
            json={"domain": "test.com"},
            headers=admin_token_headers
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    async def test_company_crud_workflow(self, client: AsyncClient, admin_token_headers, db_session):
        """Test complete CRUD workflow for companies."""
        # Create
        create_data = {
            "name": "Workflow Test Company",
            "domain": "workflow-test.com",
            "email": "info@workflow-test.com",
            "industry": "Technology"
        }
        create_response = await client.post(
            "/api/v1/companies/",
            json=create_data,
            headers=admin_token_headers
        )
        assert create_response.status_code == status.HTTP_201_CREATED
        company_id = create_response.json()["id"]
        
        # Read
        read_response = await client.get(
            f"/api/v1/companies/{company_id}",
            headers=admin_token_headers
        )
        assert read_response.status_code == status.HTTP_200_OK
        assert read_response.json()["name"] == "Workflow Test Company"
        
        # Update
        update_data = {"name": "Updated Workflow Company"}
        update_response = await client.put(
            f"/api/v1/companies/{company_id}",
            json=update_data,
            headers=admin_token_headers
        )
        assert update_response.status_code == status.HTTP_200_OK
        assert update_response.json()["name"] == "Updated Workflow Company"
        
        # Delete
        delete_response = await client.delete(
            f"/api/v1/companies/{company_id}",
            headers=admin_token_headers
        )
        assert delete_response.status_code == status.HTTP_200_OK
        
        # Verify deletion
        verify_response = await client.get(
            f"/api/v1/companies/{company_id}",
            headers=admin_token_headers
        )
        assert verify_response.status_code == status.HTTP_404_NOT_FOUND

    async def test_company_list_with_multiple_filters(self, client: AsyncClient, admin_token_headers, test_company):
        """Test company listing with multiple filters applied."""
        # Act
        response = await client.get(
            "/api/v1/companies/?skip=0&limit=10&sort_by=name&sort_order=asc&is_active=true",
            headers=admin_token_headers
        )
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert data["total"] >= 1
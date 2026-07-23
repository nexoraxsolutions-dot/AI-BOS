import os
import sys
import pytest
from fastapi import status

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


def test_company_service():
    """Test company service functions exist."""
    from app.services.company import create_company, get_company, get_companies, update_company, delete_company
    assert callable(create_company)
    assert callable(get_company)
    assert callable(get_companies)
    assert callable(update_company)
    assert callable(delete_company)


def test_company_model():
    """Test company model fields."""
    from app.models.company import Company
    
    company = Company(
        name="Test Company",
        domain="testcompany.com",
    )
    assert company.name == "Test Company"
    assert company.domain == "testcompany.com"
    # is_active has a server_default in the database, not a Python default
    # So we just verify the model can be instantiated
    assert hasattr(company, 'is_active')


@pytest.mark.asyncio
async def test_company_update_schema():
    """Test company update schema validation."""
    from app.schemas.company import CompanyUpdate
    
    # Valid partial update
    update = CompanyUpdate(name="New Name")
    assert update.name == "New Name"
    assert update.domain is None
    
    # Valid full update
    update = CompanyUpdate(name="New Name", domain="newdomain.com")
    assert update.domain == "newdomain.com"
    
    # Invalid short name
    with pytest.raises(Exception):
        CompanyUpdate(name="X")
    
    # Invalid domain
    with pytest.raises(Exception):
        CompanyUpdate(domain="invalid domain!")


@pytest.mark.asyncio
async def test_list_companies_endpoint(client, admin_token_headers, test_company):
    """Test listing companies as admin."""
    response = await client.get("/api/v1/companies/", headers=admin_token_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) >= 1
    assert any(c["name"] == "Test Company" for c in data)


@pytest.mark.asyncio
async def test_get_company_endpoint(client, admin_token_headers, test_company):
    """Test getting a specific company by ID as admin."""
    response = await client.get(f"/api/v1/companies/{test_company.id}", headers=admin_token_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["name"] == "Test Company"
    assert data["domain"] == "test-company.com"


@pytest.mark.asyncio
async def test_get_company_nonexistent(client, admin_token_headers):
    """Test getting a non-existent company returns 404."""
    response = await client.get("/api/v1/companies/99999", headers=admin_token_headers)
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_create_company_endpoint(client, admin_token_headers):
    """Test creating a new company as admin."""
    response = await client.post(
        "/api/v1/companies/",
        json={"name": "New Company", "domain": "new-company.com"},
        headers=admin_token_headers,
    )
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["name"] == "New Company"
    assert data["domain"] == "new-company.com"
    assert data["is_active"] == True


@pytest.mark.asyncio
async def test_create_company_unauthorized(client, user_token_headers):
    """Test that non-admin users cannot create companies."""
    response = await client.post(
        "/api/v1/companies/",
        json={"name": "New Company", "domain": "new-company.com"},
        headers=user_token_headers,
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.asyncio
async def test_update_company_endpoint(client, admin_token_headers, test_company):
    """Test updating a company as admin."""
    response = await client.put(
        f"/api/v1/companies/{test_company.id}",
        json={"name": "Updated Company", "is_active": False},
        headers=admin_token_headers,
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["name"] == "Updated Company"
    assert data["domain"] == "test-company.com"
    assert data["is_active"] == False


@pytest.mark.asyncio
async def test_delete_company_endpoint(client, admin_token_headers, test_company):
    """Test deleting a company as admin."""
    response = await client.delete(f"/api/v1/companies/{test_company.id}", headers=admin_token_headers)
    assert response.status_code == status.HTTP_204_NO_CONTENT


@pytest.mark.asyncio
async def test_delete_company_nonexistent(client, admin_token_headers):
    """Test deleting a non-existent company returns 404."""
    response = await client.delete("/api/v1/companies/99999", headers=admin_token_headers)
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_users_linked_to_company(client, admin_token_headers, test_company, test_user):
    """Test that users are linked to a company via company_id."""
    response = await client.get(f"/api/v1/users/{test_user.id}", headers=admin_token_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["company_id"] == test_company.id
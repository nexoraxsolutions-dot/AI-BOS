import os
import sys
import pytest
from datetime import datetime, timedelta
from fastapi import status

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


def test_company_service():
    """Test company service functions exist."""
    from app.services.company import (
        create_company, get_company, get_companies,
        update_company, delete_company, get_company_stats,
        get_company_by_domain, get_company_with_user_count
    )
    assert callable(create_company)
    assert callable(get_company)
    assert callable(get_companies)
    assert callable(update_company)
    assert callable(delete_company)
    assert callable(get_company_stats)
    assert callable(get_company_by_domain)
    assert callable(get_company_with_user_count)


def test_company_model():
    """Test company model fields."""
    from app.models.company import Company
    
    company = Company(
        name="Test Company",
        domain="testcompany.com",
    )
    assert company.name == "Test Company"
    assert company.domain == "testcompany.com"
    assert hasattr(company, 'is_active')
    assert hasattr(company, 'description')
    assert hasattr(company, 'address')
    assert hasattr(company, 'phone')
    assert hasattr(company, 'email')
    assert hasattr(company, 'website')
    assert hasattr(company, 'tax_id')
    assert hasattr(company, 'industry')
    assert hasattr(company, 'employee_count')
    assert hasattr(company, 'subscription_plan')
    assert hasattr(company, 'subscription_status')
    assert hasattr(company, 'subscription_expires_at')
    assert hasattr(company, 'settings')


@pytest.mark.asyncio
async def test_company_create_schema():
    """Test company create schema validation."""
    from app.schemas.company import CompanyCreate
    
    # Valid create with all fields
    company = CompanyCreate(
        name="Test Company",
        domain="testcompany.com",
        description="A test company",
        email="info@testcompany.com",
        phone="+1-555-123-4567",
        website="https://testcompany.com",
        industry="Technology",
        employee_count=50,
        subscription_plan="professional",
        subscription_status="active",
    )
    assert company.name == "Test Company"
    assert company.domain == "testcompany.com"
    assert company.description == "A test company"
    assert company.email == "info@testcompany.com"
    assert company.industry == "Technology"
    assert company.employee_count == 50
    assert company.subscription_plan == "professional"

    # Invalid phone
    with pytest.raises(Exception):
        CompanyCreate(name="Test", domain="test.com", phone="abc")

    # Invalid website
    with pytest.raises(Exception):
        CompanyCreate(name="Test", domain="test.com", website="not-a-url")

    # Invalid subscription plan
    with pytest.raises(Exception):
        CompanyCreate(name="Test", domain="test.com", subscription_plan="invalid-plan")

    # Invalid email
    with pytest.raises(Exception):
        CompanyCreate(name="Test", domain="test.com", email="not-an-email")


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
    
    # Valid update with all fields
    update = CompanyUpdate(
        name="Updated",
        domain="updated.com",
        description="Updated description",
        industry="Healthcare",
        employee_count=100,
        is_active=False,
        subscription_plan="enterprise",
    )
    assert update.name == "Updated"
    assert update.industry == "Healthcare"
    assert update.employee_count == 100
    assert update.is_active == False
    assert update.subscription_plan == "enterprise"


@pytest.mark.asyncio
async def test_company_stats_schema():
    """Test company stats schema validation."""
    from app.schemas.company import CompanyStats
    
    stats = CompanyStats(
        total_companies=10,
        active_companies=8,
        inactive_companies=2,
        total_users_across_companies=100,
        avg_employees=25.5,
        plan_distribution={"free": 5, "professional": 3, "enterprise": 2},
    )
    assert stats.total_companies == 10
    assert stats.active_companies == 8
    assert stats.plan_distribution["free"] == 5


@pytest.mark.asyncio
async def test_company_list_response_schema():
    """Test company list response schema validation."""
    from app.schemas.company import CompanyListResponse, CompanyOut
    from datetime import datetime
    
    company = CompanyOut(
        id=1,
        name="Test",
        domain="test.com",
        is_active=True,
        created_at=datetime.utcnow(),
        user_count=5,
    )
    
    response = CompanyListResponse(
        items=[company],
        total=1,
        page=1,
        page_size=20,
    )
    assert response.total == 1
    assert response.items[0].name == "Test"
    assert response.items[0].user_count == 5


# --- Integration Tests ---


@pytest.mark.asyncio
async def test_list_companies_endpoint(client, admin_token_headers, test_company):
    """Test listing companies as admin."""
    response = await client.get("/api/v1/companies/", headers=admin_token_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert len(data["items"]) >= 1
    assert any(c["name"] == "Test Company" for c in data["items"])


@pytest.mark.asyncio
async def test_get_company_endpoint(client, admin_token_headers, test_company):
    """Test getting a specific company by ID as admin."""
    response = await client.get(f"/api/v1/companies/{test_company.id}", headers=admin_token_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["name"] == "Test Company"
    assert data["domain"] == "test-company.com"
    assert data["is_active"] == True


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
        json={
            "name": "New Company",
            "domain": "new-company.com",
            "description": "A brand new company",
            "industry": "Finance",
            "employee_count": 25,
            "subscription_plan": "starter",
            "email": "contact@new-company.com",
        },
        headers=admin_token_headers,
    )
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["name"] == "New Company"
    assert data["domain"] == "new-company.com"
    assert data["is_active"] == True
    assert data["description"] == "A brand new company"
    assert data["industry"] == "Finance"
    assert data["employee_count"] == 25
    assert data["subscription_plan"] == "starter"
    assert data["email"] == "contact@new-company.com"


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
        json={
            "name": "Updated Company",
            "is_active": False,
            "industry": "Healthcare",
            "employee_count": 100,
            "subscription_plan": "enterprise",
        },
        headers=admin_token_headers,
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["name"] == "Updated Company"
    assert data["domain"] == "test-company.com"
    assert data["is_active"] == False
    assert data["industry"] == "Healthcare"
    assert data["employee_count"] == 100
    assert data["subscription_plan"] == "enterprise"


@pytest.mark.asyncio
async def test_update_company_missing_fields(client, admin_token_headers, test_company):
    """Test partial update only changes specified fields."""
    response = await client.put(
        f"/api/v1/companies/{test_company.id}",
        json={"name": "Only Name Changed"},
        headers=admin_token_headers,
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["name"] == "Only Name Changed"
    assert data["domain"] == "test-company.com"
    assert data["is_active"] == True


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
async def test_search_companies(client, admin_token_headers, test_company):
    """Test searching companies by name."""
    response = await client.get(
        "/api/v1/companies/?search=Test",
        headers=admin_token_headers,
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["total"] >= 1
    assert any(c["name"] == "Test Company" for c in data["items"])


@pytest.mark.asyncio
async def test_filter_companies_by_status(client, admin_token_headers, test_company):
    """Test filtering companies by active status."""
    response = await client.get(
        "/api/v1/companies/?is_active=true",
        headers=admin_token_headers,
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert all(c["is_active"] == True for c in data["items"])


@pytest.mark.asyncio
async def test_get_company_by_domain(client, admin_token_headers, test_company):
    """Test getting a company by domain."""
    response = await client.get(
        f"/api/v1/companies/by-domain/{test_company.domain}",
        headers=admin_token_headers,
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["name"] == "Test Company"
    assert data["domain"] == "test-company.com"


@pytest.mark.asyncio
async def test_get_company_by_domain_not_found(client, admin_token_headers):
    """Test getting a company by non-existent domain returns 404."""
    response = await client.get(
        "/api/v1/companies/by-domain/nonexistent.com",
        headers=admin_token_headers,
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_get_company_stats_endpoint(client, admin_token_headers, test_company):
    """Test getting company statistics."""
    response = await client.get(
        "/api/v1/companies/stats",
        headers=admin_token_headers,
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "total_companies" in data
    assert "active_companies" in data
    assert "inactive_companies" in data
    assert "total_users_across_companies" in data
    assert "avg_employees" in data
    assert "plan_distribution" in data
    assert data["total_companies"] >= 1


@pytest.mark.asyncio
async def test_company_pagination(client, admin_token_headers, test_company):
    """Test company list pagination."""
    response = await client.get(
        "/api/v1/companies/?skip=0&limit=5",
        headers=admin_token_headers,
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["page"] == 1
    assert data["page_size"] == 5
    assert len(data["items"]) <= 5


@pytest.mark.asyncio
async def test_company_sorting(client, admin_token_headers, test_company):
    """Test company list sorting."""
    # Create another company for sorting test
    await client.post(
        "/api/v1/companies/",
        json={"name": "Alpha Company", "domain": "alpha.com"},
        headers=admin_token_headers,
    )
    
    # Sort by name desc
    response = await client.get(
        "/api/v1/companies/?sort_by=name&sort_order=desc",
        headers=admin_token_headers,
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    if len(data["items"]) >= 2:
        assert data["items"][0]["name"] >= data["items"][1]["name"]


@pytest.mark.asyncio
async def test_users_linked_to_company(client, admin_token_headers, test_company, test_user):
    """Test that users are linked to a company via company_id."""
    response = await client.get(f"/api/v1/users/{test_user.id}", headers=admin_token_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["company_id"] == test_company.id


@pytest.mark.asyncio
async def test_company_requires_auth(client):
    """Test that unauthenticated requests are rejected."""
    response = await client.get("/api/v1/companies/")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.asyncio
async def test_update_company_unauthorized(client, user_token_headers, test_company):
    """Test that non-admin users cannot update companies."""
    response = await client.put(
        f"/api/v1/companies/{test_company.id}",
        json={"name": "Hacked"},
        headers=user_token_headers,
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.asyncio
async def test_delete_company_unauthorized(client, user_token_headers, test_company):
    """Test that non-admin users cannot delete companies."""
    response = await client.delete(
        f"/api/v1/companies/{test_company.id}",
        headers=user_token_headers,
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
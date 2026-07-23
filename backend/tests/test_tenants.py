"""Tests for tenant management (multi-tenancy)."""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_password_hash, create_access_token
from app.models.user import User
from app.models.company import Company
from app.models.environment_variable import EnvironmentVariable


@pytest.mark.asyncio
async def test_tenant_context_fixture(client: AsyncClient, user_token_headers: dict):
    """Test that tenant context is properly set for authenticated users."""
    response = await client.get("/api/v1/tenants/my-tenant", headers=user_token_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test Company"
    assert data["domain"] == "test-company.com"


@pytest.mark.asyncio
async def test_my_tenant_dashboard(client: AsyncClient, user_token_headers: dict):
    """Test getting tenant-specific dashboard data."""
    response = await client.get("/api/v1/tenants/my-tenant/dashboard", headers=user_token_headers)
    assert response.status_code == 200
    data = response.json()
    assert "company_name" in data
    assert "company_domain" in data
    assert "total_users" in data
    assert data["company_name"] == "Test Company"


@pytest.mark.asyncio
async def test_my_tenant_users(client: AsyncClient, db_session: AsyncSession, test_company: Company, test_user: User):
    """Test getting users within the current tenant."""
    # Ensure test_user has company_id set
    test_user.company_id = test_company.id
    await db_session.commit()
    
    # Create a new token with the updated user
    from app.core.security import create_access_token
    token = create_access_token(data={"sub": test_user.email})
    user_token_headers = {"Authorization": f"Bearer {token}"}
    
    response = await client.get("/api/v1/tenants/my-tenant/users", headers=user_token_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    emails = [u["email"] for u in data]
    assert "testuser@example.com" in emails


@pytest.mark.asyncio
async def test_list_tenants_superuser(client: AsyncClient, admin_token_headers: dict):
    """Test listing all tenants (superuser only)."""
    response = await client.get("/api/v1/tenants/", headers=admin_token_headers)
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert len(data["items"]) >= 1


@pytest.mark.asyncio
async def test_list_tenants_unauthorized(client: AsyncClient, user_token_headers: dict):
    """Test that non-superuser cannot list all tenants."""
    response = await client.get("/api/v1/tenants/", headers=user_token_headers)
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_tenant_stats_superuser(client: AsyncClient, admin_token_headers: dict):
    """Test getting global tenant statistics."""
    response = await client.get("/api/v1/tenants/stats", headers=admin_token_headers)
    assert response.status_code == 200
    data = response.json()
    assert "total_companies" in data
    assert "total_users" in data
    assert data["total_companies"] >= 1


@pytest.mark.asyncio
async def test_tenant_stats_unauthorized(client: AsyncClient, user_token_headers: dict):
    """Test that non-superuser cannot get stats."""
    response = await client.get("/api/v1/tenants/stats", headers=user_token_headers)
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_tenant_detail(client: AsyncClient, admin_token_headers: dict, test_company: Company):
    """Test getting detailed tenant information."""
    response = await client.get(f"/api/v1/tenants/{test_company.id}", headers=admin_token_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == test_company.name
    assert data["domain"] == test_company.domain
    assert "users" in data


@pytest.mark.asyncio
async def test_tenant_detail_not_found(client: AsyncClient, admin_token_headers: dict):
    """Test 404 for non-existent tenant."""
    response = await client.get("/api/v1/tenants/99999", headers=admin_token_headers)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_tenant_users_list(client: AsyncClient, admin_token_headers: dict, test_company: Company):
    """Test listing users of a specific tenant."""
    response = await client.get(
        f"/api/v1/tenants/{test_company.id}/users",
        headers=admin_token_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1


@pytest.mark.asyncio
async def test_tenant_users_search(client: AsyncClient, admin_token_headers: dict, test_company: Company, test_user: User):
    """Test searching users within a tenant."""
    response = await client.get(
        f"/api/v1/tenants/{test_company.id}/users?search=test",
        headers=admin_token_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    emails = [u["email"] for u in data]
    assert "testuser@example.com" in emails


@pytest.mark.asyncio
async def test_assign_user_to_company(
    client: AsyncClient,
    admin_token_headers: dict,
    db_session: AsyncSession,
    test_company: Company,
):
    """Test assigning a user to a company."""
    # Create a user without a company
    user = User(
        email="unassigned@example.com",
        hashed_password=get_password_hash("TestPass123!"),
        full_name="Unassigned User",
        is_active=True,
        is_superuser=False,
    )
    db_session.add(user)
    await db_session.commit()
    
    response = await client.post(
        "/api/v1/tenants/assign",
        headers=admin_token_headers,
        json={"user_id": user.id, "company_id": test_company.id},
    )
    assert response.status_code == 200
    data = response.json()
    assert "assigned" in data["message"].lower()


@pytest.mark.asyncio
async def test_assign_user_not_found(client: AsyncClient, admin_token_headers: dict, test_company: Company):
    """Test assigning non-existent user returns 404."""
    response = await client.post(
        "/api/v1/tenants/assign",
        headers=admin_token_headers,
        json={"user_id": 99999, "company_id": test_company.id},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_remove_user_from_company(
    client: AsyncClient,
    admin_token_headers: dict,
    test_user: User,
):
    """Test removing a user from their company."""
    assert test_user.company_id is not None
    
    response = await client.post(
        f"/api/v1/tenants/remove?user_id={test_user.id}",
        headers=admin_token_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert "removed" in data["message"].lower()


@pytest.mark.asyncio
async def test_remove_user_not_found(client: AsyncClient, admin_token_headers: dict):
    """Test removing non-existent user returns 404."""
    response = await client.post(
        "/api/v1/tenants/remove?user_id=99999",
        headers=admin_token_headers,
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_assign_unauthorized(client: AsyncClient, user_token_headers: dict):
    """Test that non-superuser cannot assign users."""
    response = await client.post(
        "/api/v1/tenants/assign",
        headers=user_token_headers,
        json={"user_id": 1, "company_id": 1},
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_tenant_search_filter(
    client: AsyncClient,
    admin_token_headers: dict,
):
    """Test searching tenants."""
    response = await client.get(
        "/api/v1/tenants/?search=Test",
        headers=admin_token_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1


@pytest.mark.asyncio
async def test_tenant_pagination(
    client: AsyncClient,
    admin_token_headers: dict,
):
    """Test tenant list pagination."""
    response = await client.get(
        "/api/v1/tenants/?skip=0&limit=5",
        headers=admin_token_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["page"] == 1
    assert data["page_size"] == 5
    assert data["total"] >= 1


@pytest.mark.asyncio
async def test_env_var_company_isolation(
    client: AsyncClient,
    db_session: AsyncSession,
    test_company: Company,
    test_user: User,
    admin_user: User,
):
    """Test that environment variables are scoped to company."""
    # Create env vars for test_company
    env_var1 = EnvironmentVariable(
        key="TEST_VAR_1",
        value="value1",
        company_id=test_company.id,
    )
    db_session.add(env_var1)
    
    # Create a second company
    company2 = Company(name="Company Two", domain="company-two.com")
    db_session.add(company2)
    await db_session.commit()
    
    env_var2 = EnvironmentVariable(
        key="TEST_VAR_2",
        value="value2",
        company_id=company2.id,
    )
    db_session.add(env_var2)
    await db_session.commit()
    
    # Get token for test_user (belongs to test_company)
    token = create_access_token(data={"sub": test_user.email})
    user_headers = {"Authorization": f"Bearer {token}"}
    
    # Test user should only see their company's env vars
    response = await client.get("/api/v1/environment-variables/", headers=user_headers)
    assert response.status_code == 200
    data = response.json()
    keys = [item["key"] for item in data]
    assert "TEST_VAR_1" in keys
    assert "TEST_VAR_2" not in keys  # Isolated from other company


@pytest.mark.asyncio
async def test_my_tenant_requires_company(client: AsyncClient, db_session: AsyncSession):
    """Test that user without company gets 403 on tenant endpoints."""
    user = User(
        email="nocompany@example.com",
        hashed_password=get_password_hash("TestPass123!"),
        full_name="No Company User",
        is_active=True,
        is_superuser=False,
        company_id=None,
    )
    db_session.add(user)
    await db_session.commit()
    
    token = create_access_token(data={"sub": user.email})
    headers = {"Authorization": f"Bearer {token}"}
    
    response = await client.get("/api/v1/tenants/my-tenant", headers=headers)
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_tenant_schema_validation():
    """Test tenant Pydantic schema validation."""
    from app.schemas.tenant import TenantStats, TenantDetail, TenantUserSummary
    
    # Test TenantStats
    stats = TenantStats(
        total_users=10,
        active_users=8,
        total_companies=5,
        active_companies=4,
        total_environment_variables=20,
        storage_used_estimate="1 MB",
    )
    assert stats.total_users == 10
    assert stats.active_users == 8
    
    # Test TenantUserSummary
    summary = TenantUserSummary(
        id=1,
        email="test@example.com",
        is_active=True,
        is_superuser=False,
    )
    assert summary.email == "test@example.com"
    
    # Test TenantDetail
    detail = TenantDetail(
        id=1,
        name="Test Co",
        domain="test.co",
        is_active=True,
        user_count=5,
    )
    assert detail.name == "Test Co"
    assert detail.subscription_plan == "free"
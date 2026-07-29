import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.organization_settings import OrganizationSettings
from app.models.company import Company
from app.models.user import User
from app.core.security import get_password_hash


@pytest.mark.asyncio
async def test_get_organization_settings_defaults(client: AsyncClient, db_session: AsyncSession, test_user: User, test_company: Company, user_token_headers: dict):
    """Test getting organization settings (auto-creates defaults)."""
    # Ensure user has a company
    test_user.company_id = test_company.id
    await db_session.commit()
    
    response = await client.get("/api/v1/organization-settings/", headers=user_token_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["company_id"] == test_company.id
    assert data["timezone"] == "UTC"
    assert data["language"] == "en"
    assert data["currency"] == "USD"


@pytest.mark.asyncio
async def test_update_organization_settings(client: AsyncClient, db_session: AsyncSession, test_user: User, test_company: Company, user_token_headers: dict):
    """Test updating organization settings."""
    # Ensure user has a company
    test_user.company_id = test_company.id
    await db_session.commit()
    
    # Update settings (regular users can only update localization and branding)
    update_data = {
        "timezone": "America/New_York",
        "language": "es",
        "currency": "EUR",
        "primary_color": "#FF5733"
    }
    
    response = await client.put("/api/v1/organization-settings/", json=update_data, headers=user_token_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["timezone"] == "America/New_York"
    assert data["language"] == "es"
    assert data["currency"] == "EUR"
    assert data["primary_color"] == "#FF5733"


@pytest.mark.asyncio
async def test_get_default_organization_settings(client: AsyncClient, admin_token_headers: dict):
    """Test getting default organization settings template."""
    response = await client.get("/api/v1/organization-settings/defaults", headers=admin_token_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["timezone"] == "UTC"
    assert data["language"] == "en"
    assert data["password_min_length"] == 8
    assert data["company_id"] == 0  # Default template has no company


@pytest.mark.asyncio
async def test_create_organization_settings_as_superuser(client: AsyncClient, db_session: AsyncSession, admin_token_headers: dict, test_company: Company):
    """Test creating organization settings as superuser."""
    # Create a new company for this test
    new_company = Company(
        name="Test Company 2",
        domain="test2.example.com",
    )
    db_session.add(new_company)
    await db_session.commit()
    await db_session.refresh(new_company)
    
    create_data = {
        "company_id": new_company.id,
        "timezone": "Europe/London",
        "language": "fr"
    }
    
    response = await client.post("/api/v1/organization-settings/", json=create_data, headers=admin_token_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["company_id"] == new_company.id
    assert data["timezone"] == "Europe/London"
    assert data["language"] == "fr"


@pytest.mark.asyncio
async def test_create_organization_settings_duplicate(client: AsyncClient, db_session: AsyncSession, admin_token_headers: dict, test_company: Company):
    """Test creating duplicate organization settings fails."""
    # Create settings first
    from app.services.organization_settings import create_organization_settings
    await create_organization_settings(db_session, test_company.id, {"timezone": "UTC"})
    
    # Try to create again
    create_data = {
        "company_id": test_company.id,
        "timezone": "America/New_York"
    }
    
    response = await client.post("/api/v1/organization-settings/", json=create_data, headers=admin_token_headers)
    assert response.status_code == 400
    assert "already exist" in response.json()["detail"]


@pytest.mark.asyncio
async def test_update_organization_settings_as_superuser_for_company(client: AsyncClient, db_session: AsyncSession, admin_token_headers: dict, test_company: Company):
    """Test superuser can update any company's settings."""
    from app.services.organization_settings import create_organization_settings
    await create_organization_settings(db_session, test_company.id, {"timezone": "UTC"})
    
    update_data = {
        "timezone": "Asia/Tokyo",
        "password_min_length": 16
    }
    
    response = await client.put(f"/api/v1/organization-settings/{test_company.id}", json=update_data, headers=admin_token_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["timezone"] == "Asia/Tokyo"
    assert data["password_min_length"] == 16


@pytest.mark.asyncio
async def test_validation_timezone(client: AsyncClient, db_session: AsyncSession, test_user: User, test_company: Company, user_token_headers: dict):
    """Test timezone validation."""
    test_user.company_id = test_company.id
    await db_session.commit()
    
    # Invalid timezone
    response = await client.put("/api/v1/organization-settings/", json={"timezone": "Invalid/Timezone"}, headers=user_token_headers)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_validation_password_min_length(client: AsyncClient, db_session: AsyncSession, test_user: User, test_company: Company, admin_token_headers: dict):
    """Test password minimum length validation."""
    test_user.company_id = test_company.id
    await db_session.commit()
    
    # Too short
    response = await client.put("/api/v1/organization-settings/", json={"password_min_length": 3}, headers=admin_token_headers)
    assert response.status_code == 422
    
    # Too long
    response = await client.put("/api/v1/organization-settings/", json={"password_min_length": 200}, headers=admin_token_headers)
    assert response.status_code == 422
    
    # Valid
    response = await client.put("/api/v1/organization-settings/", json={"password_min_length": 10}, headers=admin_token_headers)
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_validation_currency(client: AsyncClient, db_session: AsyncSession, test_user: User, test_company: Company, user_token_headers: dict):
    """Test currency validation."""
    test_user.company_id = test_company.id
    await db_session.commit()
    
    # Invalid currency
    response = await client.put("/api/v1/organization-settings/", json={"currency": "INVALID"}, headers=user_token_headers)
    assert response.status_code == 422
    
    # Valid currency
    response = await client.put("/api/v1/organization-settings/", json={"currency": "GBP"}, headers=user_token_headers)
    assert response.status_code == 200
    assert response.json()["currency"] == "GBP"


@pytest.mark.asyncio
async def test_validation_primary_color(client: AsyncClient, db_session: AsyncSession, test_user: User, test_company: Company, user_token_headers: dict):
    """Test primary color validation."""
    test_user.company_id = test_company.id
    await db_session.commit()
    
    # Invalid color format
    response = await client.put("/api/v1/organization-settings/", json={"primary_color": "red"}, headers=user_token_headers)
    assert response.status_code == 422
    
    # Valid color
    response = await client.put("/api/v1/organization-settings/", json={"primary_color": "#FF5733"}, headers=user_token_headers)
    assert response.status_code == 200
    assert response.json()["primary_color"] == "#FF5733"


@pytest.mark.asyncio
async def test_unauthorized_access(client: AsyncClient):
    """Test unauthorized access to organization settings."""
    response = await client.get("/api/v1/organization-settings/")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_user_without_company(client: AsyncClient, db_session: AsyncSession, test_user: User, user_token_headers: dict):
    """Test user without company cannot access settings."""
    test_user.company_id = None
    await db_session.commit()
    
    response = await client.get("/api/v1/organization-settings/", headers=user_token_headers)
    assert response.status_code == 404
    assert "not associated with any company" in response.json()["detail"]


@pytest.mark.asyncio
async def test_delete_organization_settings_as_superuser(client: AsyncClient, db_session: AsyncSession, admin_token_headers: dict, test_company: Company):
    """Test deleting organization settings as superuser."""
    from app.services.organization_settings import create_organization_settings
    settings = await create_organization_settings(db_session, test_company.id, {"timezone": "UTC"})
    
    response = await client.delete("/api/v1/organization-settings/", headers=admin_token_headers)
    assert response.status_code == 204
    
    # Verify deletion
    result = await db_session.execute(
        select(OrganizationSettings).where(OrganizationSettings.id == settings.id)
    )
    assert result.scalar_one_or_none() is None


@pytest.mark.asyncio
async def test_regular_user_cannot_update_restricted_fields(client: AsyncClient, db_session: AsyncSession, test_user: User, test_company: Company, user_token_headers: dict):
    """Test regular users cannot update security/notification settings."""
    test_user.company_id = test_company.id
    test_user.is_superuser = False
    await db_session.commit()
    
    # Try to update security settings (should fail)
    response = await client.put("/api/v1/organization-settings/", json={
        "enforce_2fa": True,
        "password_min_length": 12
    }, headers=user_token_headers)
    assert response.status_code == 403
    assert "don't have permission" in response.json()["detail"]
    
    # Try to update allowed fields (should succeed)
    response = await client.put("/api/v1/organization-settings/", json={
        "timezone": "America/New_York",
        "language": "es"
    }, headers=user_token_headers)
    assert response.status_code == 200
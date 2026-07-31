import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.company import Company
from app.core.password_policy import PasswordValidationError
from app.services.password_policy import PasswordPolicyService


@pytest.mark.asyncio
async def test_get_password_policy_defaults(client: AsyncClient, db_session: AsyncSession, test_user: User, test_company: Company, user_token_headers: dict):
    """Test getting password policy (returns defaults when no org settings)."""
    test_user.company_id = test_company.id
    await db_session.commit()
    
    response = await client.get("/api/v1/password-policy/", headers=user_token_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["min_length"] == 12
    assert data["require_uppercase"] is True
    assert data["require_lowercase"] is True
    assert data["require_numbers"] is True
    assert data["require_special_chars"] is True
    assert data["expiry_days"] == 90
    assert len(data["requirements"]) == 5


@pytest.mark.asyncio
async def test_get_password_policy_with_org_settings(client: AsyncClient, db_session: AsyncSession, test_user: User, test_company: Company, user_token_headers: dict):
    """Test getting password policy with organization settings."""
    from app.services.organization_settings import create_organization_settings
    
    test_user.company_id = test_company.id
    await db_session.commit()
    
    # Create org settings with custom password policy
    await create_organization_settings(db_session, test_company.id, {
        "password_min_length": 16,
        "password_require_uppercase": True,
        "password_require_lowercase": True,
        "password_require_numbers": True,
        "password_require_special_chars": False,
        "password_expiry_days": 60,
    })
    
    response = await client.get("/api/v1/password-policy/", headers=user_token_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["min_length"] == 16
    assert data["require_uppercase"] is True
    assert data["require_lowercase"] is True
    assert data["require_numbers"] is True
    assert data["require_special_chars"] is False
    assert data["expiry_days"] == 60


@pytest.mark.asyncio
async def test_validate_password_success(client: AsyncClient, db_session: AsyncSession, test_user: User, test_company: Company, user_token_headers: dict):
    """Test successful password validation."""
    test_user.company_id = test_company.id
    await db_session.commit()
    
    response = await client.post("/api/v1/password-policy/validate", json={
        "password": "SecurePass123!"
    }, headers=user_token_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is True
    assert len(data["errors"]) == 0
    assert all(req["met"] for req in data["requirements"])


@pytest.mark.asyncio
async def test_validate_password_too_short(client: AsyncClient, db_session: AsyncSession, test_user: User, test_company: Company, user_token_headers: dict):
    """Test password validation fails for too short password."""
    test_user.company_id = test_company.id
    await db_session.commit()
    
    response = await client.post("/api/v1/password-policy/validate", json={
        "password": "Short1!"
    }, headers=user_token_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is False
    assert any("12 characters" in error for error in data["errors"])


@pytest.mark.asyncio
async def test_validate_password_missing_uppercase(client: AsyncClient, db_session: AsyncSession, test_user: User, test_company: Company, user_token_headers: dict):
    """Test password validation fails for missing uppercase."""
    test_user.company_id = test_company.id
    await db_session.commit()
    
    response = await client.post("/api/v1/password-policy/validate", json={
        "password": "securepass123!"
    }, headers=user_token_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is False
    assert any("uppercase" in error.lower() for error in data["errors"])


@pytest.mark.asyncio
async def test_validate_password_missing_lowercase(client: AsyncClient, db_session: AsyncSession, test_user: User, test_company: Company, user_token_headers: dict):
    """Test password validation fails for missing lowercase."""
    test_user.company_id = test_company.id
    await db_session.commit()
    
    response = await client.post("/api/v1/password-policy/validate", json={
        "password": "SECUREPASS123!"
    }, headers=user_token_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is False
    assert any("lowercase" in error.lower() for error in data["errors"])


@pytest.mark.asyncio
async def test_validate_password_missing_number(client: AsyncClient, db_session: AsyncSession, test_user: User, test_company: Company, user_token_headers: dict):
    """Test password validation fails for missing number."""
    test_user.company_id = test_company.id
    await db_session.commit()
    
    response = await client.post("/api/v1/password-policy/validate", json={
        "password": "SecurePass!"
    }, headers=user_token_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is False
    assert any("digit" in error.lower() or "number" in error.lower() for error in data["errors"])


@pytest.mark.asyncio
async def test_validate_password_missing_special_char(client: AsyncClient, db_session: AsyncSession, test_user: User, test_company: Company, user_token_headers: dict):
    """Test password validation fails for missing special character."""
    test_user.company_id = test_company.id
    await db_session.commit()
    
    response = await client.post("/api/v1/password-policy/validate", json={
        "password": "SecurePass123"
    }, headers=user_token_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is False
    assert any("special character" in error.lower() for error in data["errors"])


@pytest.mark.asyncio
async def test_validate_password_common_password(client: AsyncClient, db_session: AsyncSession, test_user: User, test_company: Company, user_token_headers: dict):
    """Test password validation fails for common password."""
    test_user.company_id = test_company.id
    await db_session.commit()
    
    response = await client.post("/api/v1/password-policy/validate", json={
        "password": "password123"
    }, headers=user_token_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is False
    assert any("common" in error.lower() for error in data["errors"])


@pytest.mark.asyncio
async def test_get_default_password_policy(client: AsyncClient, user_token_headers: dict):
    """Test getting default password policy template."""
    response = await client.get("/api/v1/password-policy/defaults", headers=user_token_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["min_length"] == 12
    assert data["require_uppercase"] is True
    assert data["require_lowercase"] is True
    assert data["require_numbers"] is True
    assert data["require_special_chars"] is True
    assert data["expiry_days"] == 90


@pytest.mark.asyncio
async def test_update_password_policy_as_superuser(client: AsyncClient, db_session: AsyncSession, admin_token_headers: dict, test_company: Company):
    """Test updating password policy as superuser."""
    from app.services.organization_settings import create_organization_settings
    
    # Create org settings first
    await create_organization_settings(db_session, test_company.id, {"timezone": "UTC"})
    
    update_data = {
        "min_length": 20,
        "require_special_chars": False,
        "expiry_days": 120,
    }
    
    response = await client.put("/api/v1/password-policy/", json=update_data, headers=admin_token_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["min_length"] == 20
    assert data["require_special_chars"] is False
    assert data["expiry_days"] == 120


@pytest.mark.asyncio
async def test_update_password_policy_for_specific_company(client: AsyncClient, db_session: AsyncSession, admin_token_headers: dict, test_company: Company):
    """Test updating password policy for a specific company as superuser."""
    from app.services.organization_settings import create_organization_settings
    
    # Create org settings first
    await create_organization_settings(db_session, test_company.id, {"timezone": "UTC"})
    
    update_data = {
        "min_length": 14,
        "require_numbers": False,
    }
    
    response = await client.put(f"/api/v1/password-policy/{test_company.id}", json=update_data, headers=admin_token_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["min_length"] == 14
    assert data["require_numbers"] is False


@pytest.mark.asyncio
async def test_update_password_policy_validation_error(client: AsyncClient, db_session: AsyncSession, admin_token_headers: dict, test_company: Company):
    """Test password policy update validation."""
    from app.services.organization_settings import create_organization_settings
    
    # Create org settings first
    await create_organization_settings(db_session, test_company.id, {"timezone": "UTC"})
    
    # Invalid min_length (too short)
    response = await client.put("/api/v1/password-policy/", json={"min_length": 3}, headers=admin_token_headers)
    assert response.status_code == 422
    
    # Invalid expiry_days (too high)
    response = await client.put("/api/v1/password-policy/", json={"expiry_days": 400}, headers=admin_token_headers)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_password_policy_unauthorized(client: AsyncClient):
    """Test unauthorized access to password policy endpoints."""
    response = await client.get("/api/v1/password-policy/")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_password_policy_user_without_company(client: AsyncClient, db_session: AsyncSession, test_user: User, user_token_headers: dict):
    """Test user without company cannot access password policy."""
    test_user.company_id = None
    await db_session.commit()
    
    response = await client.get("/api/v1/password-policy/", headers=user_token_headers)
    assert response.status_code == 404
    assert "not associated with any company" in response.json()["detail"]


@pytest.mark.asyncio
async def test_password_policy_service_get_organization_policy(db_session: AsyncSession, test_company: Company):
    """Test PasswordPolicyService.get_organization_policy."""
    from app.services.organization_settings import create_organization_settings
    
    # Create org settings
    await create_organization_settings(db_session, test_company.id, {
        "password_min_length": 18,
        "password_require_uppercase": True,
        "password_require_lowercase": True,
        "password_require_numbers": True,
        "password_require_special_chars": True,
        "password_expiry_days": 60,
    })
    
    policy = await PasswordPolicyService.get_organization_policy(db_session, test_company.id)
    assert policy is not None
    assert policy["min_length"] == 18
    assert policy["require_uppercase"] is True
    assert policy["expiry_days"] == 60


@pytest.mark.asyncio
async def test_password_policy_service_validate_password_against_policy():
    """Test PasswordPolicyService.validate_password_against_policy."""
    policy = {
        "min_length": 12,
        "require_uppercase": True,
        "require_lowercase": True,
        "require_numbers": True,
        "require_special_chars": True,
    }
    
    # Valid password
    PasswordPolicyService.validate_password_against_policy("SecurePass123!", policy)
    
    # Too short
    with pytest.raises(PasswordValidationError) as exc_info:
        PasswordPolicyService.validate_password_against_policy("Short1!", policy)
    assert "12 characters" in str(exc_info.value)
    
    # Missing uppercase
    with pytest.raises(PasswordValidationError) as exc_info:
        PasswordPolicyService.validate_password_against_policy("securepass123!", policy)
    assert "uppercase" in str(exc_info.value).lower()
    
    # Missing lowercase
    with pytest.raises(PasswordValidationError) as exc_info:
        PasswordPolicyService.validate_password_against_policy("SECUREPASS123!", policy)
    assert "lowercase" in str(exc_info.value).lower()
    
    # Missing number
    with pytest.raises(PasswordValidationError) as exc_info:
        PasswordPolicyService.validate_password_against_policy("SecurePass!", policy)
    assert "digit" in str(exc_info.value).lower() or "number" in str(exc_info.value).lower()
    
    # Missing special char
    with pytest.raises(PasswordValidationError) as exc_info:
        PasswordPolicyService.validate_password_against_policy("SecurePass123", policy)
    assert "special character" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_password_policy_service_check_password_against_requirements():
    """Test PasswordPolicyService.check_password_against_requirements."""
    requirements = [
        {"id": "length", "label": "At least 12 characters", "key": "min_length", "value": 12},
        {"id": "uppercase", "label": "At least one uppercase letter", "key": "require_uppercase", "value": True},
        {"id": "lowercase", "label": "At least one lowercase letter", "key": "require_lowercase", "value": True},
        {"id": "numbers", "label": "At least one number", "key": "require_numbers", "value": True},
        {"id": "special", "label": "At least one special character", "key": "require_special_chars", "value": True},
    ]
    
    # Valid password
    result = PasswordPolicyService.check_password_against_requirements("SecurePass123!", requirements)
    assert result["length"] is True
    assert result["uppercase"] is True
    assert result["lowercase"] is True
    assert result["numbers"] is True
    assert result["special"] is True
    
    # Invalid password (too short)
    result = PasswordPolicyService.check_password_against_requirements("Short1!", requirements)
    assert result["length"] is False
    # Note: "Short1!" has uppercase 'S', lowercase 'hort', number '1', and special '!'
    # Only the length check fails
    assert result["uppercase"] is True
    assert result["lowercase"] is True
    assert result["numbers"] is True
    assert result["special"] is True


@pytest.mark.asyncio
async def test_password_policy_service_get_password_requirements_display():
    """Test PasswordPolicyService.get_password_requirements_display."""
    policy = {
        "min_length": 16,
        "require_uppercase": True,
        "require_lowercase": True,
        "require_numbers": True,
        "require_special_chars": False,
    }
    
    requirements = PasswordPolicyService.get_password_requirements_display(1, policy)
    assert len(requirements) == 5
    assert requirements[0]["id"] == "length"
    assert requirements[0]["value"] == 16
    assert requirements[4]["id"] == "special"
    assert requirements[4]["value"] is False


@pytest.mark.asyncio
async def test_password_policy_service_get_default_policy():
    """Test PasswordPolicyService.get_default_policy."""
    policy = PasswordPolicyService.get_default_policy()
    assert policy["min_length"] == 12
    assert policy["require_uppercase"] is True
    assert policy["require_lowercase"] is True
    assert policy["require_numbers"] is True
    assert policy["require_special_chars"] is True
    assert policy["expiry_days"] == 90
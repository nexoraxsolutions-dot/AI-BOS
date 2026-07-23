import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_password_hash
from app.models.user import User
from app.models.environment_variable import EnvironmentVariable
from app.schemas.environment_variable import EnvironmentVariableCreate


@pytest.mark.asyncio
async def test_create_environment_variable(client: AsyncClient, db_session: AsyncSession, test_user: User):
    """Test creating an environment variable."""
    # Create a superuser for authentication
    test_user.is_superuser = True
    await db_session.commit()
    
    # Login to get token
    login_response = await client.post(
        "/api/v1/auth/login",
        data={"username": test_user.email, "password": "TestPassword123!"}
    )
    token = login_response.json()["access_token"]
    
    # Create environment variable
    payload = {
        "key": "TEST_VAR",
        "value": "test_value_123",
        "description": "Test environment variable",
        "is_secret": False
    }
    
    response = await client.post(
        "/api/v1/environment-variables/",
        json=payload,
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["key"] == "TEST_VAR"
    assert data["value"] == "test_value_123"
    assert data["description"] == "Test environment variable"
    assert data["is_secret"] is False


@pytest.mark.asyncio
async def test_create_duplicate_environment_variable(client: AsyncClient, db_session: AsyncSession, test_user: User):
    """Test creating a duplicate environment variable (should fail)."""
    # Create a superuser
    test_user.is_superuser = True
    await db_session.commit()
    
    # Create first environment variable
    env_var = EnvironmentVariable(
        key="DUPLICATE_VAR",
        value="value1",
        description="First var",
        is_secret=False
    )
    db_session.add(env_var)
    await db_session.commit()
    
    # Login
    login_response = await client.post(
        "/api/v1/auth/login",
        data={"username": test_user.email, "password": "TestPassword123!"}
    )
    token = login_response.json()["access_token"]
    
    # Try to create duplicate
    payload = {
        "key": "DUPLICATE_VAR",
        "value": "value2",
        "description": "Duplicate var",
        "is_secret": False
    }
    
    response = await client.post(
        "/api/v1/environment-variables/",
        json=payload,
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]


@pytest.mark.asyncio
async def test_list_environment_variables(client: AsyncClient, db_session: AsyncSession, test_user: User):
    """Test listing environment variables."""
    # Create multiple environment variables
    for i in range(5):
        env_var = EnvironmentVariable(
            key=f"VAR_{i}",
            value=f"value_{i}",
            description=f"Test variable {i}",
            is_secret=(i % 2 == 0)
        )
        db_session.add(env_var)
    await db_session.commit()
    
    # Login
    login_response = await client.post(
        "/api/v1/auth/login",
        data={"username": test_user.email, "password": "TestPassword123!"}
    )
    token = login_response.json()["access_token"]
    
    # List environment variables
    response = await client.get(
        "/api/v1/environment-variables/",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 5
    
    # Check that secret values are masked
    for item in data:
        if item["is_secret"]:
            assert item["value"] is None
            assert item["masked_value"] is not None
        else:
            assert item["value"] is not None


@pytest.mark.asyncio
async def test_get_environment_variable_by_id(client: AsyncClient, db_session: AsyncSession, test_user: User):
    """Test getting a specific environment variable by ID."""
    # Create environment variable
    env_var = EnvironmentVariable(
        key="SPECIFIC_VAR",
        value="specific_value",
        description="Specific test var",
        is_secret=False
    )
    db_session.add(env_var)
    await db_session.commit()
    await db_session.refresh(env_var)
    
    # Login
    login_response = await client.post(
        "/api/v1/auth/login",
        data={"username": test_user.email, "password": "TestPassword123!"}
    )
    token = login_response.json()["access_token"]
    
    # Get by ID
    response = await client.get(
        f"/api/v1/environment-variables/{env_var.id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["key"] == "SPECIFIC_VAR"
    assert data["value"] == "specific_value"


@pytest.mark.asyncio
async def test_get_environment_variable_by_key(client: AsyncClient, db_session: AsyncSession, test_user: User):
    """Test getting a specific environment variable by key."""
    # Create environment variable
    env_var = EnvironmentVariable(
        key="KEY_VAR",
        value="key_value",
        description="Key test var",
        is_secret=False
    )
    db_session.add(env_var)
    await db_session.commit()
    
    # Login
    login_response = await client.post(
        "/api/v1/auth/login",
        data={"username": test_user.email, "password": "TestPassword123!"}
    )
    token = login_response.json()["access_token"]
    
    # Get by key
    response = await client.get(
        "/api/v1/environment-variables/key/KEY_VAR",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["key"] == "KEY_VAR"
    assert data["value"] == "key_value"


@pytest.mark.asyncio
async def test_update_environment_variable(client: AsyncClient, db_session: AsyncSession, test_user: User):
    """Test updating an environment variable."""
    # Create superuser
    test_user.is_superuser = True
    await db_session.commit()
    
    # Create environment variable
    env_var = EnvironmentVariable(
        key="UPDATE_VAR",
        value="old_value",
        description="Old description",
        is_secret=False
    )
    db_session.add(env_var)
    await db_session.commit()
    await db_session.refresh(env_var)
    
    # Login
    login_response = await client.post(
        "/api/v1/auth/login",
        data={"username": test_user.email, "password": "TestPassword123!"}
    )
    token = login_response.json()["access_token"]
    
    # Update
    payload = {
        "value": "new_value",
        "description": "New description",
        "is_secret": True
    }
    
    response = await client.put(
        f"/api/v1/environment-variables/{env_var.id}",
        json=payload,
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["value"] is None  # Secret values are masked
    assert data["masked_value"] is not None
    assert data["description"] == "New description"
    assert data["is_secret"] is True


@pytest.mark.asyncio
async def test_delete_environment_variable(client: AsyncClient, db_session: AsyncSession, test_user: User):
    """Test deleting an environment variable."""
    # Create superuser
    test_user.is_superuser = True
    await db_session.commit()
    
    # Create environment variable
    env_var = EnvironmentVariable(
        key="DELETE_VAR",
        value="delete_me",
        description="To be deleted",
        is_secret=False
    )
    db_session.add(env_var)
    await db_session.commit()
    await db_session.refresh(env_var)
    
    # Login
    login_response = await client.post(
        "/api/v1/auth/login",
        data={"username": test_user.email, "password": "TestPassword123!"}
    )
    token = login_response.json()["access_token"]
    
    # Delete
    response = await client.delete(
        f"/api/v1/environment-variables/{env_var.id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 204
    
    # Verify deletion
    get_response = await client.get(
        f"/api/v1/environment-variables/{env_var.id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_export_environment_variables(client: AsyncClient, db_session: AsyncSession, test_user: User):
    """Test exporting environment variables."""
    # Create superuser
    test_user.is_superuser = True
    await db_session.commit()
    
    # Create environment variables
    for i in range(3):
        env_var = EnvironmentVariable(
            key=f"EXPORT_VAR_{i}",
            value=f"export_value_{i}",
            description=f"Export test {i}",
            is_secret=False
        )
        db_session.add(env_var)
    await db_session.commit()
    
    # Login
    login_response = await client.post(
        "/api/v1/auth/login",
        data={"username": test_user.email, "password": "TestPassword123!"}
    )
    token = login_response.json()["access_token"]
    
    # Export
    response = await client.get(
        "/api/v1/environment-variables/export/.env",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "EXPORT_VAR_0" in data
    assert "EXPORT_VAR_1" in data
    assert "EXPORT_VAR_2" in data
    assert data["EXPORT_VAR_0"] == "export_value_0"


@pytest.mark.asyncio
async def test_environment_variable_validation(client: AsyncClient, db_session: AsyncSession, test_user: User):
    """Test environment variable validation."""
    # Create superuser
    test_user.is_superuser = True
    await db_session.commit()
    
    # Login
    login_response = await client.post(
        "/api/v1/auth/login",
        data={"username": test_user.email, "password": "TestPassword123!"}
    )
    token = login_response.json()["access_token"]
    
    # Test invalid key (lowercase)
    payload = {
        "key": "invalid_key",
        "value": "value",
        "is_secret": False
    }
    response = await client.post(
        "/api/v1/environment-variables/",
        json=payload,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 422
    
    # Test empty value
    payload = {
        "key": "VALID_KEY",
        "value": "",
        "is_secret": False
    }
    response = await client.post(
        "/api/v1/environment-variables/",
        json=payload,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 422
    
    # Test key too short
    payload = {
        "key": "A",
        "value": "value",
        "is_secret": False
    }
    response = await client.post(
        "/api/v1/environment-variables/",
        json=payload,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_environment_variable_requires_auth(client: AsyncClient):
    """Test that environment variable endpoints require authentication."""
    # Try to list without auth
    response = await client.get("/api/v1/environment-variables/")
    assert response.status_code == 401
    
    # Try to create without auth
    response = await client.post(
        "/api/v1/environment-variables/",
        json={"key": "TEST", "value": "test"}
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_environment_variable_requires_superuser(client: AsyncClient, db_session: AsyncSession, test_user: User):
    """Test that create/update/delete require superuser."""
    # Ensure user is not superuser
    test_user.is_superuser = False
    await db_session.commit()
    
    # Login
    login_response = await client.post(
        "/api/v1/auth/login",
        data={"username": test_user.email, "password": "TestPassword123!"}
    )
    token = login_response.json()["access_token"]
    
    # Try to create (should fail)
    response = await client.post(
        "/api/v1/environment-variables/",
        json={"key": "TEST", "value": "test", "is_secret": False},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 403

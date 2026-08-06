import os
import sys
import pytest
from fastapi import status

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


def test_logging_configuration_model():
    """Test logging configuration model fields."""
    from app.models.logging_configuration import LoggingConfiguration

    config = LoggingConfiguration(
        company_id=1,
        log_level="INFO",
        enable_database_logging=True,
        enable_console_logging=True,
        log_format="text",
        retention_days=90,
    )
    assert config.company_id == 1
    assert config.log_level == "INFO"
    assert config.enable_database_logging is True
    assert config.enable_console_logging is True
    assert config.log_format == "text"
    assert config.retention_days == 90


def test_logging_configuration_schema():
    """Test logging configuration schema validation."""
    from app.schemas.logging_configuration import (
        LoggingConfigurationBase,
        LoggingConfigurationCreate,
        LoggingConfigurationUpdate,
        LoggingConfigurationOut,
    )

    # Base schema
    base = LoggingConfigurationBase(log_level="DEBUG", log_format="json")
    assert base.log_level == "DEBUG"
    assert base.log_format == "json"

    # Level validation - uppercase
    base_upper = LoggingConfigurationBase(log_level="info")
    assert base_upper.log_level == "INFO"

    # Invalid level
    with pytest.raises(ValueError):
        LoggingConfigurationBase(log_level="INVALID")

    # Format validation
    base_format = LoggingConfigurationBase(log_format="JSON")
    assert base_format.log_format == "json"

    # Invalid format
    with pytest.raises(ValueError):
        LoggingConfigurationBase(log_format="xml")

    # Retention days validation
    with pytest.raises(ValueError):
        LoggingConfigurationBase(retention_days=0)

    with pytest.raises(ValueError):
        LoggingConfigurationBase(retention_days=3661)

    # Create schema
    create = LoggingConfigurationCreate(
        company_id=1,
        log_level="WARNING",
        enable_database_logging=False,
        retention_days=30,
    )
    assert create.company_id == 1
    assert create.log_level == "WARNING"

    # Update schema
    update = LoggingConfigurationUpdate(log_level="ERROR", retention_days=60)
    assert update.log_level == "ERROR"
    assert update.retention_days == 60


@pytest.mark.asyncio
async def test_create_logging_configuration(db_session):
    """Test creating a logging configuration."""
    from app.services.logging_configuration import create_logging_configuration

    config = await create_logging_configuration(
        db_session,
        company_id=1,
        config_data={
            "log_level": "DEBUG",
            "enable_database_logging": True,
            "enable_console_logging": False,
            "log_format": "json",
            "retention_days": 30,
        }
    )
    assert config.id is not None
    assert config.company_id == 1
    assert config.log_level == "DEBUG"


@pytest.mark.asyncio
async def test_get_logging_configuration(db_session):
    """Test getting a logging configuration."""
    from app.services.logging_configuration import create_logging_configuration, get_logging_configuration

    # Create config
    await create_logging_configuration(
        db_session,
        company_id=2,
        config_data={"log_level": "WARNING"}
    )

    # Get config
    config = await get_logging_configuration(db_session, company_id=2)
    assert config is not None
    assert config.log_level == "WARNING"


@pytest.mark.asyncio
async def test_get_logging_configuration_not_found(db_session):
    """Test getting non-existent logging configuration."""
    from app.services.logging_configuration import get_logging_configuration

    config = await get_logging_configuration(db_session, company_id=999)
    assert config is None


@pytest.mark.asyncio
async def test_update_logging_configuration(db_session):
    """Test updating a logging configuration."""
    from app.services.logging_configuration import create_logging_configuration, update_logging_configuration

    # Create config
    config = await create_logging_configuration(
        db_session,
        company_id=3,
        config_data={"log_level": "INFO", "retention_days": 90}
    )
    assert config.log_level == "INFO"

    # Update config
    updated = await update_logging_configuration(
        db_session,
        company_id=3,
        config_data={"log_level": "ERROR", "retention_days": 60}
    )
    assert updated is not None
    assert updated.log_level == "ERROR"
    assert updated.retention_days == 60


@pytest.mark.asyncio
async def test_update_logging_configuration_creates_new(db_session):
    """Test that update creates new config if it doesn't exist."""
    from app.services.logging_configuration import update_logging_configuration

    # Update non-existent config
    config = await update_logging_configuration(
        db_session,
        company_id=4,
        config_data={"log_level": "CRITICAL"}
    )
    assert config is not None
    assert config.company_id == 4
    assert config.log_level == "CRITICAL"


@pytest.mark.asyncio
async def test_delete_logging_configuration(db_session):
    """Test deleting a logging configuration."""
    from app.services.logging_configuration import create_logging_configuration, delete_logging_configuration, get_logging_configuration

    # Create config
    await create_logging_configuration(
        db_session,
        company_id=5,
        config_data={"log_level": "INFO"}
    )

    # Delete config
    deleted = await delete_logging_configuration(db_session, company_id=5)
    assert deleted is True

    # Verify deleted
    config = await get_logging_configuration(db_session, company_id=5)
    assert config is None


@pytest.mark.asyncio
async def test_delete_logging_configuration_not_found(db_session):
    """Test deleting non-existent logging configuration."""
    from app.services.logging_configuration import delete_logging_configuration

    deleted = await delete_logging_configuration(db_session, company_id=999)
    assert deleted is False


@pytest.mark.asyncio
async def test_get_or_create_default_config(db_session):
    """Test get or create default config."""
    from app.services.logging_configuration import get_or_create_default_config

    # Should create new config
    config = await get_or_create_default_config(db_session, company_id=6)
    assert config is not None
    assert config.company_id == 6
    assert config.log_level == "INFO"  # Default value

    # Should return existing config
    config2 = await get_or_create_default_config(db_session, company_id=6)
    assert config2.id == config.id


@pytest.mark.asyncio
async def test_create_duplicate_configuration(db_session):
    """Test that creating duplicate configuration raises error."""
    from app.services.logging_configuration import create_logging_configuration

    # Create first config
    await create_logging_configuration(db_session, company_id=7, config_data={"log_level": "INFO"})

    # Try to create duplicate
    with pytest.raises(ValueError):
        await create_logging_configuration(db_session, company_id=7, config_data={"log_level": "DEBUG"})


@pytest.mark.asyncio
async def test_logging_config_endpoint_create(client, db_session, admin_token_headers, admin_user):
    """Test creating logging configuration via API (superuser only)."""
    response = await client.post(
        "/api/v1/logging-config/",
        json={"company_id": admin_user.company_id, "log_level": "DEBUG", "log_format": "json"},
        headers=admin_token_headers,
    )
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["company_id"] == admin_user.company_id
    assert data["log_level"] == "DEBUG"
    assert data["log_format"] == "json"


@pytest.mark.asyncio
async def test_logging_config_endpoint_create_duplicate(client, db_session, admin_token_headers, admin_user):
    """Test that creating a duplicate configuration returns 400."""
    from app.services.logging_configuration import create_logging_configuration

    # Pre-seed a config for the superuser's own company
    await create_logging_configuration(db_session, company_id=admin_user.company_id, config_data={})

    response = await client.post(
        "/api/v1/logging-config/",
        json={"company_id": admin_user.company_id, "log_level": "DEBUG"},
        headers=admin_token_headers,
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.asyncio
async def test_logging_config_endpoint_get(client, db_session, admin_token_headers, admin_user):
    """Test getting logging configuration via API.

    GET resolves the configuration using the authenticated user's company,
    so the config must be created for the superuser's own company.
    """
    from app.services.logging_configuration import create_logging_configuration

    # Create config for the superuser's own company
    await create_logging_configuration(
        db_session,
        company_id=admin_user.company_id,
        config_data={"log_level": "WARNING", "retention_days": 30}
    )

    # Get config
    response = await client.get(
        "/api/v1/logging-config/",
        headers=admin_token_headers,
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["company_id"] == admin_user.company_id
    assert data["log_level"] == "WARNING"
    assert data["retention_days"] == 30


@pytest.mark.asyncio
async def test_logging_config_endpoint_get_creates_default(client, db_session, admin_token_headers, admin_user):
    """Test that GET creates a default configuration when none exists."""
    response = await client.get(
        "/api/v1/logging-config/",
        headers=admin_token_headers,
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["company_id"] == admin_user.company_id
    assert data["log_level"] == "INFO"  # Default value
    assert data["retention_days"] == 90  # Default value


@pytest.mark.asyncio
async def test_logging_config_endpoint_update(client, db_session, admin_token_headers, admin_user):
    """Test updating logging configuration via API.

    PUT resolves the configuration using the authenticated user's company,
    so the config must be created for the superuser's own company.
    """
    from app.services.logging_configuration import create_logging_configuration

    # Create config for the superuser's own company
    await create_logging_configuration(
        db_session,
        company_id=admin_user.company_id,
        config_data={"log_level": "INFO", "retention_days": 90}
    )

    # Update config
    response = await client.put(
        "/api/v1/logging-config/",
        json={"log_level": "ERROR", "retention_days": 60},
        headers=admin_token_headers,
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["log_level"] == "ERROR"
    assert data["retention_days"] == 60


@pytest.mark.asyncio
async def test_logging_config_endpoint_delete(client, db_session, admin_token_headers, admin_user):
    """Test deleting logging configuration via API.

    DELETE resolves the configuration using the authenticated user's company,
    so the config must be created for the superuser's own company.
    """
    from app.services.logging_configuration import create_logging_configuration

    # Create config for the superuser's own company
    await create_logging_configuration(
        db_session, company_id=admin_user.company_id, config_data={"log_level": "INFO"}
    )

    # Delete config
    response = await client.delete(
        "/api/v1/logging-config/",
        headers=admin_token_headers,
    )
    assert response.status_code == status.HTTP_204_NO_CONTENT


@pytest.mark.asyncio
async def test_logging_config_endpoint_unauthorized(client, user_token_headers):
    """Test that non-superuser cannot create/update/delete logging configuration."""
    # Try to create
    response = await client.post(
        "/api/v1/logging-config/",
        json={"company_id": 1, "log_level": "DEBUG"},
        headers=user_token_headers,
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN

    # Try to update
    response = await client.put(
        "/api/v1/logging-config/",
        json={"log_level": "ERROR"},
        headers=user_token_headers,
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN

    # Try to delete
    response = await client.delete(
        "/api/v1/logging-config/",
        headers=user_token_headers,
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN

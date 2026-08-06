import os
import sys
import pytest
from datetime import timedelta
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock, MagicMock
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from asyncio import get_event_loop

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.main import app
from app.db import Base, get_async_session
from app.core.config import settings
from app.core.security import get_password_hash, create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES
from app.models.user import User
from app.models.company import Company
from app.models.department import Department
from app.models.role import Role
from app.models.session import UserSession
from app.models.api_key import ApiKey
from app.models.token import Token
from app.models.audit_log import AuditLog
from app.models.environment_variable import EnvironmentVariable
from app.models.organization_settings import OrganizationSettings
from app.models.two_factor import TwoFactorBackupCode
from app.models.logging_history import LogEntry
from app.models.password_history import PasswordHistory
from app.models.password_reset import PasswordResetToken

# Test database configuration
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

# Create test engine with in-memory SQLite
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
    echo=False,
)

# Test session factory
TestAsyncSessionLocal = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for the entire test session."""
    loop = get_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function", autouse=True)
async def db_session():
    """
    Provide a database session for tests.
    Creates all tables before each test and drops them after.
    """
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with TestAsyncSessionLocal() as session:
        yield session
    
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def client(db_session):
    """Provide an HTTP client with overridden database dependency."""
    async def get_test_session():
        yield db_session

    app.dependency_overrides[get_async_session] = get_test_session
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
        follow_redirects=True,
    ) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
async def test_company(db_session):
    """Create a test company."""
    company = Company(
        name="Test Company",
        domain="test-company.com",
        is_active=True,
    )
    db_session.add(company)
    await db_session.commit()
    await db_session.refresh(company)
    return company


@pytest.fixture
async def test_user(db_session, test_company):
    """Create a test user."""
    user = User(
        email="testuser@example.com",
        hashed_password=get_password_hash("TestPassword123!"),
        full_name="Test User",
        is_active=True,
        is_superuser=False,
        is_email_verified=True,
        company_id=test_company.id,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def admin_user(db_session, test_company):
    """Create an admin user."""
    user = User(
        email="admin@ai-bos.com",
        hashed_password=get_password_hash("SecurePass123!"),
        full_name="Admin User",
        is_active=True,
        is_superuser=True,
        is_email_verified=True,
        company_id=test_company.id,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def inactive_user(db_session, test_company):
    """Create an inactive user."""
    user = User(
        email="inactive@example.com",
        hashed_password=get_password_hash("InactivePass123!"),
        full_name="Inactive User",
        is_active=False,
        is_superuser=False,
        is_email_verified=False,
        company_id=test_company.id,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def user_token_headers(test_user):
    """Generate auth token headers for a regular user."""
    token = create_access_token(
        data={"sub": test_user.email},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
async def admin_token_headers(admin_user):
    """Generate auth token headers for an admin user."""
    token = create_access_token(
        data={"sub": admin_user.email},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
async def test_department(db_session, test_company):
    """Create a test department."""
    department = Department(
        name="Test Department",
        description="A test department",
        company_id=test_company.id,
        budget="$50,000",
        location="Building B",
        is_active=True,
    )
    db_session.add(department)
    await db_session.commit()
    await db_session.refresh(department)
    return department


@pytest.fixture
async def test_role(db_session):
    """Create a test role."""
    role = Role(
        name="Test Role",
        description="A test role",
        is_system_role=False,
    )
    db_session.add(role)
    await db_session.commit()
    await db_session.refresh(role)
    return role


@pytest.fixture
async def test_session(db_session, test_user):
    """Create a test user session."""
    session = UserSession(
        user_id=test_user.id,
        token="test_session_token_123",
        expires_at=test_user.created_at + timedelta(hours=24),
        is_active=True,
        ip_address="127.0.0.1",
        user_agent="Test User Agent",
    )
    db_session.add(session)
    await db_session.commit()
    await db_session.refresh(session)
    return session


@pytest.fixture
async def test_api_key(db_session, test_user):
    """Create a test API key."""
    api_key = ApiKey(
        name="Test API Key",
        key="test_api_key_12345",
        user_id=test_user.id,
        is_active=True,
        expires_at=test_user.created_at + timedelta(days=30),
    )
    db_session.add(api_key)
    await db_session.commit()
    await db_session.refresh(api_key)
    return api_key


@pytest.fixture
async def test_token(db_session, test_user):
    """Create a test token."""
    token = Token(
        token="test_token_12345",
        token_type="access",
        user_id=test_user.id,
        is_revoked=False,
        expires_at=test_user.created_at + timedelta(minutes=60),
    )
    db_session.add(token)
    await db_session.commit()
    await db_session.refresh(token)
    return token


@pytest.fixture
async def test_audit_log(db_session, test_user, test_company):
    """Create a test audit log."""
    audit_log = AuditLog(
        action="test_action",
        resource_type="user",
        resource_id=test_user.id,
        user_id=test_user.id,
        company_id=test_company.id,
        ip_address="127.0.0.1",
        user_agent="Test User Agent",
        details={"test": "data"},
    )
    db_session.add(audit_log)
    await db_session.commit()
    await db_session.refresh(audit_log)
    return audit_log


@pytest.fixture
async def test_environment_variable(db_session, test_company):
    """Create a test environment variable."""
    env_var = EnvironmentVariable(
        key="TEST_VAR",
        value="test_value",
        description="A test environment variable",
        company_id=test_company.id,
        is_active=True,
    )
    db_session.add(env_var)
    await db_session.commit()
    await db_session.refresh(env_var)
    return env_var


@pytest.fixture
async def test_organization_settings(db_session, test_company):
    """Create test organization settings."""
    settings = OrganizationSettings(
        company_id=test_company.id,
        allow_registration=True,
        require_email_verification=True,
        max_users_per_company=100,
        session_timeout_minutes=1440,
        password_expiry_days=90,
        two_factor_required=False,
    )
    db_session.add(settings)
    await db_session.commit()
    await db_session.refresh(settings)
    return settings


@pytest.fixture
async def test_two_factor_auth(db_session, test_user):
    """Create test two-factor authentication."""
    two_factor = TwoFactorBackupCode(
        user_id=test_user.id,
        secret_key="test_secret_key_12345",
        is_enabled=True,
        backup_codes=["code1", "code2", "code3"],
    )
    db_session.add(two_factor)
    await db_session.commit()
    await db_session.refresh(two_factor)
    return two_factor


@pytest.fixture
async def test_logging_history(db_session, test_user, test_company):
    """Create test logging history."""
    log = LogEntry(
        level="INFO",
        message="Test log message",
        user_id=test_user.id,
        company_id=test_company.id,
        ip_address="127.0.0.1",
        user_agent="Test User Agent",
        metadata={"test": "data"},
    )
    db_session.add(log)
    await db_session.commit()
    await db_session.refresh(log)
    return log


@pytest.fixture
async def test_password_history(db_session, test_user):
    """Create test password history."""
    password_history = PasswordHistory(
        user_id=test_user.id,
        hashed_password=get_password_hash("OldPassword123!"),
    )
    db_session.add(password_history)
    await db_session.commit()
    await db_session.refresh(password_history)
    return password_history


@pytest.fixture
async def test_password_reset_token(db_session, test_user):
    """Create test password reset token."""
    reset_token = PasswordResetToken(
        user_id=test_user.id,
        token="test_reset_token_12345",
        expires_at=test_user.created_at + timedelta(hours=1),
        is_used=False,
    )
    db_session.add(reset_token)
    await db_session.commit()
    await db_session.refresh(reset_token)
    return reset_token


@pytest.fixture
def mock_redis():
    """Provide a mock Redis client."""
    mock = MagicMock()
    mock.get = AsyncMock(return_value=None)
    mock.set = AsyncMock(return_value=True)
    mock.delete = AsyncMock(return_value=True)
    mock.exists = AsyncMock(return_value=False)
    mock.expire = AsyncMock(return_value=True)
    mock.flushdb = AsyncMock(return_value=True)
    return mock


@pytest.fixture
def mock_email_service():
    """Provide a mock email service."""
    mock = MagicMock()
    mock.send_email = AsyncMock(return_value=True)
    mock.send_verification_email = AsyncMock(return_value=True)
    mock.send_password_reset_email = AsyncMock(return_value=True)
    return mock


@pytest.fixture
def test_settings():
    """Provide test settings with overridden values."""
    settings.database_url = TEST_DATABASE_URL
    settings.secret_key = "test-secret-key-for-testing-only"
    settings.access_token_expire_minutes = 5
    settings.refresh_token_expire_minutes = 60
    settings.redis_url = "redis://localhost:6379/15"  # Use separate DB for tests
    return settings


@pytest.fixture
async def authenticated_client(client, test_user):
    """Provide an authenticated client with user token."""
    token = create_access_token(
        data={"sub": test_user.email},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    client.headers["Authorization"] = f"Bearer {token}"
    return client


@pytest.fixture
async def admin_client(client, admin_user):
    """Provide an authenticated client with admin token."""
    token = create_access_token(
        data={"sub": admin_user.email},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    client.headers["Authorization"] = f"Bearer {token}"
    return client


@pytest.fixture
def mock_database_session():
    """Provide a mock database session for unit tests."""
    session = MagicMock(spec=AsyncSession)
    session.add = MagicMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    session.delete = AsyncMock()
    session.rollback = AsyncMock()
    session.close = AsyncMock()
    session.execute = AsyncMock()
    session.scalars = MagicMock()
    session.scalar = AsyncMock()
    return session
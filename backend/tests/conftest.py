import os
import sys
import pytest
from datetime import timedelta
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.main import app
from app.db import Base, get_async_session
from app.core.security import get_password_hash, create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES
from app.models.user import User
from app.models.company import Company

DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine = create_async_engine(DATABASE_URL, future=True)
AsyncSessionTest = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


@pytest.fixture
async def db_session():
    """Provide a database session for tests."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with AsyncSessionTest() as session:
        yield session
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def client(db_session):
    """Provide an HTTP client with overridden database dependency."""
    async def get_test_session():
        yield db_session

    app.dependency_overrides[get_async_session] = get_test_session
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
async def test_company(db_session):
    """Create a test company."""
    company = Company(name="Test Company", domain="test-company.com")
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
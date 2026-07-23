"""Integration tests for the dashboard endpoint."""

import pytest
from datetime import datetime
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.company import Company


@pytest.mark.asyncio
async def test_dashboard_summary_unauthorized(client: AsyncClient):
    """Test that dashboard summary returns 401 without auth."""
    response = await client.get("/api/v1/dashboard/summary")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_dashboard_summary_returns_data(
    client: AsyncClient,
    user_token_headers: dict,
    db_session: AsyncSession,
    test_company: Company,
    test_user: User,
):
    """Test that dashboard summary returns aggregated statistics."""
    response = await client.get(
        "/api/v1/dashboard/summary",
        headers=user_token_headers,
    )
    assert response.status_code == 200

    data = response.json()
    assert "summary" in data
    assert "message" in data

    summary = data["summary"]
    assert summary["total_users"] >= 1
    assert summary["active_users"] >= 1
    assert summary["total_companies"] >= 1
    assert summary["total_sales_monthly"] == 1850000.00
    assert summary["total_tasks_pending"] == 84
    assert isinstance(summary["recent_users_count"], int)
    assert isinstance(summary["recent_companies_count"], int)

    # Check welcome message includes user info
    assert test_user.email in data["message"] or test_user.full_name in data["message"]


@pytest.mark.asyncio
async def test_dashboard_summary_admin_access(
    client: AsyncClient,
    admin_token_headers: dict,
):
    """Test that admin users can access dashboard summary."""
    response = await client.get(
        "/api/v1/dashboard/summary",
        headers=admin_token_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert "summary" in data
    assert data["summary"]["total_users"] >= 0


@pytest.mark.asyncio
async def test_dashboard_summary_with_multiple_users(
    client: AsyncClient,
    db_session: AsyncSession,
    test_company: Company,
    test_user: User,
):
    """Test dashboard summary counts multiple users and companies correctly."""
    # Create additional users
    for i in range(5):
        user = User(
            email=f"testuser{i}@example.com",
            hashed_password="$2b$12$dummy_hash_for_testing",
            full_name=f"Test User {i}",
            is_active=True,
            company_id=test_company.id,
            created_at=datetime.utcnow(),
        )
        db_session.add(user)
    await db_session.commit()

    # Create additional companies
    for i in range(3):
        company = Company(
            name=f"Test Company {i}",
            domain=f"test-company-{i}.com",
            is_active=True,
            created_at=datetime.utcnow(),
        )
        db_session.add(company)
    await db_session.commit()

    # Generate token for one of the new users
    from app.core.security import create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES
    from datetime import timedelta

    token = create_access_token(
        data={"sub": "testuser0@example.com"},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    headers = {"Authorization": f"Bearer {token}"}

    response = await client.get(
        "/api/v1/dashboard/summary",
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()
    summary = data["summary"]

    # Should have test_user fixture + 5 new users = 6, plus company fixture + 3 new = 4
    assert summary["total_users"] == 6  # 1 fixture + 5 new
    assert summary["total_companies"] == 4  # 1 fixture + 3 new
    assert summary["active_users"] == 6  # all active

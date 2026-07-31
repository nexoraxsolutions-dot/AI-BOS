import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta

from app.services.security_dashboard import get_security_dashboard_data
from app.schemas.security_dashboard import SecurityDashboardResponse


@pytest.fixture
def mock_db():
    """Create a mock database session."""
    db = AsyncMock()
    return db


def create_mock_result(scalar_value=None, scalars_list=None, all_list=None):
    """Create a mock result object with proper sync methods."""
    result = MagicMock()
    result.scalar.return_value = scalar_value
    if scalars_list is not None:
        result.scalars.return_value.all.return_value = scalars_list
    if all_list is not None:
        result.all.return_value = all_list
    return result


@pytest.mark.asyncio
async def test_get_security_dashboard_data_success(mock_db):
    """Test that security dashboard data is returned successfully."""
    # Mock execute to return a result with scalar=10 and scalars=[]
    mock_result = create_mock_result(scalar_value=10, scalars_list=[])
    mock_db.execute.return_value = mock_result

    with patch("app.services.security_dashboard.cache_service") as mock_cache:
        mock_cache.get = AsyncMock(return_value=None)
        mock_cache.set = AsyncMock(return_value=None)

        result = await get_security_dashboard_data(mock_db)

        assert result is not None
        assert "security_score" in result
        assert "total_users" in result
        assert "users_with_2fa" in result
        assert "locked_accounts" in result
        assert "active_sessions" in result
        assert "failed_logins_24h" in result
        assert "failed_logins_7d" in result
        assert "account_lockouts_30d" in result
        assert "recent_events" in result
        assert result["total_users"] == 10


@pytest.mark.asyncio
async def test_get_security_dashboard_data_cached(mock_db):
    """Test that cached data is returned when available."""
    cached_data = {
        "security_score": 85,
        "total_users": 100,
        "users_with_2fa": 50,
        "locked_accounts": 2,
        "users_with_failed_logins": 5,
        "active_sessions": 45,
        "failed_logins_24h": 10,
        "failed_logins_7d": 50,
        "account_lockouts_30d": 3,
        "password_changes_30d": 8,
        "two_fa_enabled_30d": 5,
        "suspicious_ips_count": 1,
        "recent_events": []
    }

    with patch("app.services.security_dashboard.cache_service") as mock_cache:
        mock_cache.get = AsyncMock(return_value=cached_data)

        result = await get_security_dashboard_data(mock_db)

        assert result == cached_data
        mock_db.execute.assert_not_called()


@pytest.mark.asyncio
async def test_security_dashboard_response_schema():
    """Test that the security dashboard response schema works correctly."""
    data = {
        "security_score": 75,
        "total_users": 100,
        "users_with_2fa": 60,
        "locked_accounts": 1,
        "users_with_failed_logins": 10,
        "active_sessions": 50,
        "failed_logins_24h": 5,
        "failed_logins_7d": 25,
        "account_lockouts_30d": 2,
        "password_changes_30d": 10,
        "two_fa_enabled_30d": 8,
        "suspicious_ips_count": 0,
        "recent_events": [
            {
                "id": 1,
                "action": "login_failed",
                "user_id": 1,
                "ip_address": "192.168.1.1",
                "created_at": datetime.utcnow().isoformat(),
                "details": {"attempts": 3}
            }
        ]
    }

    response = SecurityDashboardResponse(**data)
    assert response.security_score == 75
    assert response.total_users == 100
    assert response.users_with_2fa == 60
    assert len(response.recent_events) == 1


@pytest.mark.asyncio
async def test_security_score_calculation():
    """Test the security score calculation logic."""
    with patch("app.services.security_dashboard.cache_service") as mock_cache:
        mock_cache.get = AsyncMock(return_value=None)
        mock_cache.set = AsyncMock(return_value=None)

        # Mock a db session with specific data
        db = AsyncMock()
        # All queries return 0 by default, which is perfect security
        mock_result = create_mock_result(scalar_value=0, scalars_list=[], all_list=[])
        db.execute.return_value = mock_result

        # Override the first scalar call to return 10 for total_users
        call_count = [0]
        def scalar_side_effect(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                return 10
            return 0

        # Create a fresh mock result for each call
        results = []
        for i in range(12):
            r = create_mock_result(scalar_value=0, scalars_list=[], all_list=[])
            if i == 0:
                r.scalar.return_value = 10  # total_users
            if i == 1:
                r.scalar.return_value = 10  # users_with_2fa (100% adoption)
            results.append(r)

        db.execute.side_effect = results

        result = await get_security_dashboard_data(db)

        # With all security features enabled (100% 2FA, no failed logins, no locked accounts)
        # the score should be 100
        assert result["security_score"] == 100


@pytest.mark.asyncio
async def test_security_dashboard_with_suspicious_activity():
    """Test that suspicious activity reduces the security score."""
    with patch("app.services.security_dashboard.cache_service") as mock_cache:
        mock_cache.get = AsyncMock(return_value=None)
        mock_cache.set = AsyncMock(return_value=None)

        db = AsyncMock()

        # Create mock results for each query call
        # 11 query calls: total_users, users_with_2fa, locked_accounts, users_with_failed_logins,
        # active_sessions, failed_logins_24h, failed_logins_7d, account_lockouts_30d,
        # password_changes_30d, two_fa_enabled_30d, suspicious_activities
        results = []

        # total_users = 10
        r = create_mock_result(scalar_value=10, scalars_list=[], all_list=[])
        results.append(r)

        # users_with_2fa = 5
        r = create_mock_result(scalar_value=5, scalars_list=[], all_list=[])
        results.append(r)

        # locked_accounts = 0
        r = create_mock_result(scalar_value=0, scalars_list=[], all_list=[])
        results.append(r)

        # users_with_failed_logins = 3
        r = create_mock_result(scalar_value=3, scalars_list=[], all_list=[])
        results.append(r)

        # active_sessions = 8
        r = create_mock_result(scalar_value=8, scalars_list=[], all_list=[])
        results.append(r)

        # failed_logins_24h = 15
        r = create_mock_result(scalar_value=15, scalars_list=[], all_list=[])
        results.append(r)

        # failed_logins_7d = 50
        r = create_mock_result(scalar_value=50, scalars_list=[], all_list=[])
        results.append(r)

        # account_lockouts_30d = 0
        r = create_mock_result(scalar_value=0, scalars_list=[], all_list=[])
        results.append(r)

        # password_changes_30d = 5
        r = create_mock_result(scalar_value=5, scalars_list=[], all_list=[])
        results.append(r)

        # two_fa_enabled_30d = 2
        r = create_mock_result(scalar_value=2, scalars_list=[], all_list=[])
        results.append(r)

        # suspicious_activities (uses .all())
        r = create_mock_result(all_list=[("192.168.1.1", 5), ("10.0.0.1", 6)])
        results.append(r)

        # recent_events (uses .scalars().all())
        r = create_mock_result(scalars_list=[], all_list=[])
        results.append(r)

        db.execute.side_effect = results

        result = await get_security_dashboard_data(db)

        # Score should be reduced due to failed logins and suspicious IPs
        assert result["security_score"] < 100
"""Unit tests for company service layer."""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.company import (
    create_company,
    get_company,
    get_company_by_domain,
    get_companies,
    update_company,
    delete_company,
    get_company_stats,
    get_company_with_user_count,
)

pytestmark = pytest.mark.asyncio


class TestCreateCompany:
    """Test cases for create_company function."""

    async def test_create_company_success(self, mock_database_session):
        """Test successful company creation."""
        # Arrange
        from tests.unit.factories import MockDataFactory
        
        mock_company = MockDataFactory.create_mock_company(
            name="New Company",
            domain="newcompany.com"
        )
        
        mock_payload = MagicMock()
        mock_payload.model_dump.return_value = {
            "name": "New Company",
            "domain": "newcompany.com",
            "email": "info@newcompany.com",
            "industry": "Technology",
            "subscription_plan": "premium",
            "is_active": True,
            "employee_count": 50,
        }
        
        mock_cache_service = MockDataFactory.create_mock_cache_service()
        
        with patch('app.services.company.cache_service', mock_cache_service):
            # Act
            result = await create_company(mock_database_session, mock_payload)
            
            # Assert
            assert result is not None
            assert result.name == "New Company"
            assert result.domain == "newcompany.com"
            mock_database_session.add.assert_called_once()
            mock_database_session.commit.assert_called_once()
            mock_database_session.refresh.assert_called_once()
            # Verify cache invalidation
            mock_cache_service.delete_pattern.assert_called_once()
            mock_cache_service.delete.assert_called_once()

    async def test_create_company_with_minimal_data(self, mock_database_session):
        """Test company creation with minimal required data."""
        # Arrange
        from tests.unit.factories import MockDataFactory
        
        mock_company = MockDataFactory.create_mock_company(
            name="Minimal Company",
            domain="minimal.com"
        )
        
        mock_payload = MagicMock()
        mock_payload.model_dump.return_value = {
            "name": "Minimal Company",
            "domain": "minimal.com",
        }
        
        mock_cache_service = MockDataFactory.create_mock_cache_service()
        
        with patch('app.services.company.cache_service', mock_cache_service):
            # Act
            result = await create_company(mock_database_session, mock_payload)
            
            # Assert
            assert result is not None
            mock_database_session.add.assert_called_once()


class TestGetCompany:
    """Test cases for get_company function."""

    async def test_get_company_from_cache(self, mock_database_session):
        """Test getting company from cache."""
        # Arrange
        from tests.unit.factories import MockDataFactory
        
        cached_company = {
            "id": 1,
            "name": "Cached Company",
            "domain": "cached.com",
        }
        
        mock_cache_service = MockDataFactory.create_mock_cache_service()
        mock_cache_service.get = AsyncMock(return_value=cached_company)
        
        with patch('app.services.company.cache_service', mock_cache_service):
            # Act
            result = await get_company(mock_database_session, 1)
            
            # Assert
            assert result is not None
            assert result["name"] == "Cached Company"
            # Database should not be queried when cache hit
            mock_database_session.execute.assert_not_called()

    async def test_get_company_from_database(self, mock_database_session):
        """Test getting company from database when not in cache."""
        # Arrange
        from tests.unit.factories import MockDataFactory
        
        mock_company = MockDataFactory.create_mock_company(
            company_id=1,
            name="Database Company",
            domain="database.com"
        )
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_company
        mock_database_session.execute.return_value = mock_result
        
        mock_cache_service = MockDataFactory.create_mock_cache_service()
        mock_cache_service.get = AsyncMock(return_value=None)
        
        with patch('app.services.company.cache_service', mock_cache_service):
            # Act
            result = await get_company(mock_database_session, 1)
            
            # Assert
            assert result is not None
            assert result.name == "Database Company"
            mock_database_session.execute.assert_called_once()
            # Verify cache was set
            mock_cache_service.set.assert_called_once()

    async def test_get_company_not_found(self, mock_database_session):
        """Test getting non-existent company."""
        # Arrange
        from tests.unit.factories import MockDataFactory
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_database_session.execute.return_value = mock_result
        
        mock_cache_service = MockDataFactory.create_mock_cache_service()
        mock_cache_service.get = AsyncMock(return_value=None)
        
        with patch('app.services.company.cache_service', mock_cache_service):
            # Act
            result = await get_company(mock_database_session, 999)
            
            # Assert
            assert result is None


class TestGetCompanyByDomain:
    """Test cases for get_company_by_domain function."""

    async def test_get_company_by_domain_success(self, mock_database_session):
        """Test getting company by domain."""
        # Arrange
        from tests.unit.factories import MockDataFactory
        
        mock_company = MockDataFactory.create_mock_company(
            name="Domain Company",
            domain="domaincompany.com"
        )
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_company
        mock_database_session.execute.return_value = mock_result
        
        # Act
        result = await get_company_by_domain(mock_database_session, "domaincompany.com")
        
        # Assert
        assert result is not None
        assert result.domain == "domaincompany.com"
        mock_database_session.execute.assert_called_once()

    async def test_get_company_by_domain_not_found(self, mock_database_session):
        """Test getting company with non-existent domain."""
        # Arrange
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_database_session.execute.return_value = mock_result
        
        # Act
        result = await get_company_by_domain(mock_database_session, "nonexistent.com")
        
        # Assert
        assert result is None


class TestGetCompanies:
    """Test cases for get_companies function."""

    async def test_get_companies_success(self, mock_database_session):
        """Test getting list of companies."""
        # Arrange
        from tests.unit.factories import MockDataFactory
        
        mock_companies = [
            MockDataFactory.create_mock_company(company_id=1, name="Company 1"),
            MockDataFactory.create_mock_company(company_id=2, name="Company 2"),
        ]
        
        # Mock for companies query
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_companies
        
        # Mock for count query
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 2
        
        mock_database_session.execute.side_effect = [mock_count_result, mock_result]
        
        # Act
        companies, total = await get_companies(mock_database_session)
        
        # Assert
        assert len(companies) == 2
        assert total == 2
        assert companies[0].name == "Company 1"
        assert companies[1].name == "Company 2"

    async def test_get_companies_with_search(self, mock_database_session):
        """Test getting companies with search filter."""
        # Arrange
        from tests.unit.factories import MockDataFactory
        
        mock_companies = [
            MockDataFactory.create_mock_company(company_id=1, name="Tech Corp"),
        ]
        
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_companies
        
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 1
        
        mock_database_session.execute.side_effect = [mock_count_result, mock_result]
        
        # Act
        companies, total = await get_companies(
            mock_database_session,
            search="Tech"
        )
        
        # Assert
        assert len(companies) == 1
        assert total == 1

    async def test_get_companies_with_filters(self, mock_database_session):
        """Test getting companies with multiple filters."""
        # Arrange
        from tests.unit.factories import MockDataFactory
        
        mock_companies = [
            MockDataFactory.create_mock_company(
                company_id=1,
                name="Active Tech",
                is_active=True,
                industry="Technology"
            ),
        ]
        
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_companies
        
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 1
        
        mock_database_session.execute.side_effect = [mock_count_result, mock_result]
        
        # Act
        companies, total = await get_companies(
            mock_database_session,
            is_active=True,
            industry="Technology"
        )
        
        # Assert
        assert len(companies) == 1
        assert total == 1

    async def test_get_companies_with_pagination(self, mock_database_session):
        """Test getting companies with pagination."""
        # Arrange
        from tests.unit.factories import MockDataFactory
        
        mock_companies = [
            MockDataFactory.create_mock_company(company_id=1, name="Company 1"),
        ]
        
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_companies
        
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 10  # Total 10 companies
        
        mock_database_session.execute.side_effect = [mock_count_result, mock_result]
        
        # Act
        companies, total = await get_companies(
            mock_database_session,
            skip=0,
            limit=1
        )
        
        # Assert
        assert len(companies) == 1
        assert total == 10

    async def test_get_companies_with_sorting(self, mock_database_session):
        """Test getting companies with sorting."""
        # Arrange
        from tests.unit.factories import MockDataFactory
        
        mock_companies = [
            MockDataFactory.create_mock_company(company_id=1, name="A Company"),
            MockDataFactory.create_mock_company(company_id=2, name="B Company"),
        ]
        
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_companies
        
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 2
        
        mock_database_session.execute.side_effect = [mock_count_result, mock_result]
        
        # Act
        companies, total = await get_companies(
            mock_database_session,
            sort_by="name",
            sort_order="asc"
        )
        
        # Assert
        assert len(companies) == 2
        assert total == 2


class TestUpdateCompany:
    """Test cases for update_company function."""

    async def test_update_company_success(self, mock_database_session):
        """Test successful company update."""
        # Arrange
        from tests.unit.factories import MockDataFactory
        
        mock_company = MockDataFactory.create_mock_company(
            company_id=1,
            name="Old Name",
            domain="old.com"
        )
        
        mock_payload = MagicMock()
        mock_payload.model_dump.return_value = {
            "name": "New Name",
            "industry": "Finance",
        }
        mock_payload.model_dump.side_effect = lambda exclude_unset=False: {
            "name": "New Name",
            "industry": "Finance",
        } if exclude_unset else {
            "name": "New Name",
            "domain": "old.com",
            "industry": "Finance",
        }
        
        # Mock get_company to return the company
        with patch('app.services.company.get_company', new_callable=AsyncMock) as mock_get:
            with patch('app.services.company.cache_service', MockDataFactory.create_mock_cache_service()):
                mock_get.return_value = mock_company
                
                # Act
                result = await update_company(mock_database_session, 1, mock_payload)
                
                # Assert
                assert result is not None
                assert result.name == "New Name"
                mock_database_session.commit.assert_called_once()
                mock_database_session.refresh.assert_called_once()

    async def test_update_company_not_found(self, mock_database_session):
        """Test updating non-existent company."""
        # Arrange
        mock_payload = MagicMock()
        mock_payload.model_dump.return_value = {"name": "New Name"}
        
        # Mock get_company to return None
        with patch('app.services.company.get_company', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = None
            
            # Act
            result = await update_company(mock_database_session, 999, mock_payload)
            
            # Assert
            assert result is None


class TestDeleteCompany:
    """Test cases for delete_company function."""

    async def test_delete_company_success(self, mock_database_session):
        """Test successful company deletion."""
        # Arrange
        from tests.unit.factories import MockDataFactory
        
        mock_company = MockDataFactory.create_mock_company(company_id=1)
        
        # Mock get_company to return the company
        with patch('app.services.company.get_company', new_callable=AsyncMock) as mock_get:
            with patch('app.services.company.cache_service', MockDataFactory.create_mock_cache_service()):
                mock_get.return_value = mock_company
                
                # Act
                result = await delete_company(mock_database_session, 1)
                
                # Assert
                assert result is True
                mock_database_session.delete.assert_called_once_with(mock_company)
                mock_database_session.commit.assert_called_once()

    async def test_delete_company_not_found(self, mock_database_session):
        """Test deleting non-existent company."""
        # Arrange
        # Mock get_company to return None
        with patch('app.services.company.get_company', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = None
            
            # Act
            result = await delete_company(mock_database_session, 999)
            
            # Assert
            assert result is False
            mock_database_session.delete.assert_not_called()


class TestGetCompanyStats:
    """Test cases for get_company_stats function."""

    async def test_get_company_stats_from_cache(self, mock_database_session):
        """Test getting company stats from cache."""
        # Arrange
        from tests.unit.factories import MockDataFactory
        
        cached_stats = {
            "total_companies": 10,
            "active_companies": 8,
            "inactive_companies": 2,
        }
        
        mock_cache_service = MockDataFactory.create_mock_cache_service()
        mock_cache_service.get = AsyncMock(return_value=cached_stats)
        
        with patch('app.services.company.cache_service', mock_cache_service):
            # Act
            result = await get_company_stats(mock_database_session)
            
            # Assert
            assert result is not None
            assert result["total_companies"] == 10
            # Database should not be queried when cache hit
            mock_database_session.execute.assert_not_called()

    async def test_get_company_stats_from_database(self, mock_database_session):
        """Test getting company stats from database."""
        # Arrange
        from tests.unit.factories import MockDataFactory
        from app.models.company import Company
        from app.models.user import User
        
        mock_cache_service = MockDataFactory.create_mock_cache_service()
        mock_cache_service.get = AsyncMock(return_value=None)
        
        # Mock count results
        mock_total_result = MagicMock()
        mock_total_result.scalar.return_value = 10
        
        mock_active_result = MagicMock()
        mock_active_result.scalar.return_value = 8
        
        mock_users_result = MagicMock()
        mock_users_result.scalar.return_value = 50
        
        mock_avg_result = MagicMock()
        mock_avg_result.scalar.return_value = 25.5
        
        mock_plan_result = MagicMock()
        mock_plan_result.all.return_value = [
            ("premium", 5),
            ("basic", 3),
        ]
        
        mock_database_session.execute.side_effect = [
            mock_total_result,
            mock_active_result,
            mock_users_result,
            mock_avg_result,
            mock_plan_result,
        ]
        
        with patch('app.services.company.cache_service', mock_cache_service):
            # Act
            result = await get_company_stats(mock_database_session)
            
            # Assert
            assert result is not None
            assert result["total_companies"] == 10
            assert result["active_companies"] == 8
            assert result["inactive_companies"] == 2
            assert result["total_users_across_companies"] == 50
            assert result["avg_employees"] == 25.5
            assert "plan_distribution" in result
            # Verify cache was set
            mock_cache_service.set.assert_called_once()


class TestGetCompanyWithUserCount:
    """Test cases for get_company_with_user_count function."""

    async def test_get_company_with_user_count_success(self, mock_database_session):
        """Test getting company with user count."""
        # Arrange
        from tests.unit.factories import MockDataFactory
        
        mock_company = MockDataFactory.create_mock_company(
            company_id=1,
            name="Test Company"
        )
        
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 15
        
        # Mock get_company to return the company
        with patch('app.services.company.get_company', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_company
            mock_database_session.execute.return_value = mock_count_result
            
            # Act
            result = await get_company_with_user_count(mock_database_session, 1)
            
            # Assert
            assert result is not None
            assert result["name"] == "Test Company"
            assert result["user_count"] == 15

    async def test_get_company_with_user_count_not_found(self, mock_database_session):
        """Test getting non-existent company with user count."""
        # Arrange
        # Mock get_company to return None
        with patch('app.services.company.get_company', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = None
            
            # Act
            result = await get_company_with_user_count(mock_database_session, 999)
            
            # Assert
            assert result is None
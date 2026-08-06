"""Mock data factories for unit testing service layer."""
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from unittest.mock import MagicMock, AsyncMock
from faker import Faker

fake = Faker()


class MockDataFactory:
    """Factory for creating mock data objects for testing."""
    
    @staticmethod
    def create_mock_user(user_id: int = 1, **kwargs) -> MagicMock:
        """Create a mock user object."""
        user = MagicMock()
        user.id = user_id
        user.email = kwargs.get('email', fake.email())
        user.full_name = kwargs.get('full_name', fake.name())
        user.hashed_password = kwargs.get('hashed_password', fake.password())
        user.is_active = kwargs.get('is_active', True)
        user.is_superuser = kwargs.get('is_superuser', False)
        user.is_verified = kwargs.get('is_verified', True)
        user.is_email_verified = kwargs.get('is_email_verified', True)
        user.username = kwargs.get('username', fake.user_name())
        user.company_id = kwargs.get('company_id', 1)
        user.created_at = kwargs.get('created_at', datetime.utcnow())
        user.email_verification_token = kwargs.get('email_verification_token', None)
        user.failed_login_attempts = kwargs.get('failed_login_attempts', 0)
        user.locked_until = kwargs.get('locked_until', None)
        return user
    
    @staticmethod
    def create_mock_company(company_id: int = 1, **kwargs) -> MagicMock:
        """Create a mock company object."""
        company = MagicMock()
        company.id = company_id
        company.name = kwargs.get('name', fake.company())
        company.domain = kwargs.get('domain', fake.domain_name())
        company.email = kwargs.get('email', fake.company_email())
        company.industry = kwargs.get('industry', fake.word())
        company.subscription_plan = kwargs.get('subscription_plan', 'premium')
        company.is_active = kwargs.get('is_active', True)
        company.employee_count = kwargs.get('employee_count', fake.random_int(min=10, max=500))
        company.created_at = kwargs.get('created_at', datetime.utcnow())
        return company
    
    @staticmethod
    def create_mock_register_request(**kwargs) -> MagicMock:
        """Create a mock registration request."""
        request = MagicMock()
        request.email = kwargs.get('email', fake.email())
        request.password = kwargs.get('password', 'ValidPass123!')
        request.full_name = kwargs.get('full_name', fake.name())
        request.username = kwargs.get('username', fake.user_name())
        request.company_name = kwargs.get('company_name', fake.company())
        request.company_domain = kwargs.get('company_domain', fake.domain_name())
        return request
    
    @staticmethod
    def create_mock_db_session() -> MagicMock:
        """Create a mock database session."""
        session = MagicMock()
        session.add = MagicMock()
        session.commit = AsyncMock()
        session.refresh = AsyncMock()
        session.delete = MagicMock()
        session.rollback = AsyncMock()
        session.close = AsyncMock()
        session.execute = AsyncMock()
        session.scalars = MagicMock()
        session.scalar = AsyncMock()
        session.flush = AsyncMock()
        return session
    
    @staticmethod
    def create_mock_request(ip: str = "127.0.0.1", user_agent: str = "Test Agent") -> MagicMock:
        """Create a mock FastAPI Request object."""
        request = MagicMock()
        request.client = MagicMock()
        request.client.host = ip
        request.headers = {"user-agent": user_agent}
        return request
    
    @staticmethod
    def create_mock_cache_service() -> MagicMock:
        """Create a mock cache service."""
        cache = MagicMock()
        cache.get = AsyncMock(return_value=None)
        cache.set = AsyncMock(return_value=True)
        cache.delete = AsyncMock(return_value=True)
        cache.delete_pattern = AsyncMock(return_value=True)
        cache.exists = AsyncMock(return_value=False)
        cache.expire = AsyncMock(return_value=True)
        cache.flushdb = AsyncMock(return_value=True)
        return cache
    
    @staticmethod
    def create_mock_account_lock_service() -> MagicMock:
        """Create a mock account lock service."""
        service = MagicMock()
        service.record_failed_login = AsyncMock()
        service.is_account_locked = AsyncMock(return_value=(False, None))
        service.reset_failed_attempts = AsyncMock()
        service.lock_account = AsyncMock()
        service.unlock_account = AsyncMock()
        return service
    
    @staticmethod
    def create_mock_email_service() -> MagicMock:
        """Create a mock email service."""
        service = MagicMock()
        service.send_verification_email = AsyncMock(return_value=True)
        service.send_password_reset_email = AsyncMock(return_value=True)
        service.send_email = AsyncMock(return_value=True)
        return service
    
    @staticmethod
    def create_mock_audit_log() -> MagicMock:
        """Create a mock audit log."""
        log = MagicMock()
        log.id = fake.random_int(min=1, max=1000)
        log.action = fake.word()
        log.resource_type = fake.word()
        log.resource_id = fake.random_int(min=1, max=100)
        log.user_id = fake.random_int(min=1, max=100)
        log.company_id = fake.random_int(min=1, max=10)
        log.ip_address = fake.ipv4()
        log.user_agent = fake.user_agent()
        log.details = {"test": "data"}
        log.created_at = datetime.utcnow()
        return log


# Helper functions for common test scenarios
def get_valid_password() -> str:
    """Return a valid password for testing."""
    return "ValidPass123!"


def get_invalid_password() -> str:
    """Return an invalid password for testing."""
    return "short"


def get_test_email() -> str:
    """Return a test email."""
    return "test@example.com"


def get_test_company_data(**kwargs) -> Dict[str, Any]:
    """Return test company data."""
    return {
        "name": kwargs.get('name', "Test Company"),
        "domain": kwargs.get('domain', "test-company.com"),
        "email": kwargs.get('email', "test@test-company.com"),
        "industry": kwargs.get('industry', "Technology"),
        "subscription_plan": kwargs.get('subscription_plan', "premium"),
        "is_active": kwargs.get('is_active', True),
        "employee_count": kwargs.get('employee_count', 50),
    }


def get_test_user_data(**kwargs) -> Dict[str, Any]:
    """Return test user data."""
    return {
        "email": kwargs.get('email', "testuser@example.com"),
        "password": kwargs.get('password', "ValidPass123!"),
        "full_name": kwargs.get('full_name', "Test User"),
        "username": kwargs.get('username', "testuser"),
        "is_active": kwargs.get('is_active', True),
        "is_superuser": kwargs.get('is_superuser', False),
        "is_verified": kwargs.get('is_verified', True),
    }


def get_test_register_data(**kwargs) -> Dict[str, Any]:
    """Return test registration data."""
    return {
        "email": kwargs.get('email', "newuser@example.com"),
        "password": kwargs.get('password', "ValidPass123!"),
        "full_name": kwargs.get('full_name', "New User"),
        "username": kwargs.get('username', "newuser"),
        "company_name": kwargs.get('company_name', "New Company"),
        "company_domain": kwargs.get('company_domain', "new-company.com"),
    }
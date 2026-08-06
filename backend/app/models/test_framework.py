from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Enum, Float
from sqlalchemy.orm import relationship
import enum

from app.db import Base


class TestStatus(str, enum.Enum):
    __test__ = False
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"


class TestPriority(str, enum.Enum):
    __test__ = False
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class TestSuite(Base):
    __test__ = False
    __tablename__ = "test_suites"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    is_automated = Column(Boolean, default=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=True, index=True)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    company = relationship("Company", back_populates="test_suites")
    created_by = relationship("User", back_populates="created_test_suites")
    test_cases = relationship(
        "TestCase",
        back_populates="test_suite",
        cascade="all, delete-orphan",
        order_by="TestCase.order"
    )
    test_runs = relationship(
        "TestRun",
        back_populates="test_suite",
        cascade="all, delete-orphan"
    )


class TestCase(Base):
    __test__ = False
    __tablename__ = "test_cases"

    id = Column(Integer, primary_key=True, index=True)
    test_suite_id = Column(Integer, ForeignKey("test_suites.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    priority = Column(Enum(TestPriority), default=TestPriority.MEDIUM, index=True)
    status = Column(Enum(TestStatus), default=TestStatus.PENDING, index=True)
    order = Column(Integer, default=0)
    
    # Test configuration
    test_type = Column(String(50), nullable=False)  # unit, integration, e2e, performance
    endpoint = Column(String(500), nullable=True)  # API endpoint or test path
    method = Column(String(10), nullable=True)  # GET, POST, PUT, DELETE
    payload = Column(Text, nullable=True)  # JSON payload for API tests
    expected_status = Column(Integer, nullable=True)  # Expected HTTP status code
    expected_response = Column(Text, nullable=True)  # Expected response JSON
    
    # Test metadata
    tags = Column(String(500), nullable=True)  # Comma-separated tags
    timeout = Column(Integer, default=30)  # Timeout in seconds
    retry_count = Column(Integer, default=0)  # Number of retries on failure
    is_active = Column(Boolean, default=True)
    
    # Results tracking
    last_run_at = Column(DateTime, nullable=True)
    last_run_status = Column(Enum(TestStatus), nullable=True)
    last_run_duration = Column(Float, nullable=True)  # Duration in seconds
    success_count = Column(Integer, default=0)
    failure_count = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    test_suite = relationship("TestSuite", back_populates="test_cases")
    test_results = relationship(
        "TestResult",
        back_populates="test_case",
        cascade="all, delete-orphan"
    )


class TestRun(Base):
    __test__ = False
    __tablename__ = "test_runs"

    id = Column(Integer, primary_key=True, index=True)
    test_suite_id = Column(Integer, ForeignKey("test_suites.id"), nullable=False, index=True)
    triggered_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Run metadata
    status = Column(Enum(TestStatus), default=TestStatus.RUNNING, index=True)
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    duration = Column(Float, nullable=True)  # Duration in seconds
    
    # Results summary
    total_tests = Column(Integer, default=0)
    passed_tests = Column(Integer, default=0)
    failed_tests = Column(Integer, default=0)
    skipped_tests = Column(Integer, default=0)
    error_tests = Column(Integer, default=0)
    success_rate = Column(Float, nullable=True)  # Percentage
    
    # Environment info
    environment = Column(String(50), default="development")  # development, staging, production
    branch = Column(String(255), nullable=True)  # Git branch
    commit_hash = Column(String(255), nullable=True)  # Git commit hash
    triggered_by = Column(String(50), default="manual")  # manual, scheduled, webhook
    
    # Error details
    error_message = Column(Text, nullable=True)
    error_traceback = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    test_suite = relationship("TestSuite", back_populates="test_runs")
    triggered_by_user = relationship("User", back_populates="test_runs")
    test_results = relationship(
        "TestResult",
        back_populates="test_run",
        cascade="all, delete-orphan"
    )


class TestResult(Base):
    __test__ = False
    __tablename__ = "test_results"

    id = Column(Integer, primary_key=True, index=True)
    test_run_id = Column(Integer, ForeignKey("test_runs.id"), nullable=False, index=True)
    test_case_id = Column(Integer, ForeignKey("test_cases.id"), nullable=False, index=True)
    
    # Result details
    status = Column(Enum(TestStatus), nullable=False, index=True)
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    duration = Column(Float, nullable=True)  # Duration in seconds
    
    # Output and errors
    output = Column(Text, nullable=True)  # Test output/logs
    error_message = Column(Text, nullable=True)  # Error message if failed
    error_traceback = Column(Text, nullable=True)  # Full traceback if error
    
    # Request/Response for API tests
    request_url = Column(String(500), nullable=True)
    request_method = Column(String(10), nullable=True)
    request_headers = Column(Text, nullable=True)  # JSON headers
    request_body = Column(Text, nullable=True)  # JSON request body
    response_status = Column(Integer, nullable=True)  # Actual HTTP status
    response_headers = Column(Text, nullable=True)  # JSON response headers
    response_body = Column(Text, nullable=True)  # JSON response body
    
    # Metadata
    retry_attempt = Column(Integer, default=0)  # Which retry attempt this is
    environment = Column(String(50), default="development")
    
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    test_run = relationship("TestRun", back_populates="test_results")
    test_case = relationship("TestCase", back_populates="test_results")
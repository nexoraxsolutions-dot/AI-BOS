from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, validator
from app.models.test_framework import TestStatus, TestPriority


# Test Suite Schemas
class TestSuiteBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    is_active: bool = True
    is_automated: bool = True
    company_id: Optional[int] = None


class TestSuiteCreate(TestSuiteBase):
    pass


class TestSuiteUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    is_active: Optional[bool] = None
    is_automated: Optional[bool] = None
    company_id: Optional[int] = None


class TestSuiteOut(TestSuiteBase):
    id: int
    created_by_id: Optional[int]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Test Case Schemas
class TestCaseBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    priority: TestPriority = TestPriority.MEDIUM
    test_type: str = Field(..., min_length=1, max_length=50)
    endpoint: Optional[str] = Field(None, max_length=500)
    method: Optional[str] = Field(None, max_length=10)
    payload: Optional[str] = None
    expected_status: Optional[int] = None
    expected_response: Optional[str] = None
    tags: Optional[str] = Field(None, max_length=500)
    timeout: int = Field(default=30, ge=1, le=300)
    retry_count: int = Field(default=0, ge=0, le=10)
    is_active: bool = True
    order: int = 0

    @validator('method')
    def validate_method(cls, v):
        if v and v.upper() not in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH']:
            raise ValueError('Method must be GET, POST, PUT, DELETE, or PATCH')
        return v.upper() if v else v

    @validator('test_type')
    def validate_test_type(cls, v):
        allowed_types = ['unit', 'integration', 'e2e', 'performance', 'security']
        if v not in allowed_types:
            raise ValueError(f'Test type must be one of: {", ".join(allowed_types)}')
        return v


class TestCaseCreate(TestCaseBase):
    test_suite_id: int


class TestCaseUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    priority: Optional[TestPriority] = None
    test_type: Optional[str] = Field(None, min_length=1, max_length=50)
    endpoint: Optional[str] = Field(None, max_length=500)
    method: Optional[str] = Field(None, max_length=10)
    payload: Optional[str] = None
    expected_status: Optional[int] = None
    expected_response: Optional[str] = None
    tags: Optional[str] = Field(None, max_length=500)
    timeout: Optional[int] = Field(None, ge=1, le=300)
    retry_count: Optional[int] = Field(None, ge=0, le=10)
    is_active: Optional[bool] = None
    order: Optional[int] = None

    @validator('method')
    def validate_method(cls, v):
        if v and v.upper() not in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH']:
            raise ValueError('Method must be GET, POST, PUT, DELETE, or PATCH')
        return v.upper() if v else v

    @validator('test_type')
    def validate_test_type(cls, v):
        if v:
            allowed_types = ['unit', 'integration', 'e2e', 'performance', 'security']
            if v not in allowed_types:
                raise ValueError(f'Test type must be one of: {", ".join(allowed_types)}')
        return v


class TestCaseOut(TestCaseBase):
    id: int
    test_suite_id: int
    status: TestStatus
    last_run_at: Optional[datetime]
    last_run_status: Optional[TestStatus]
    last_run_duration: Optional[float]
    success_count: int
    failure_count: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Test Run Schemas
class TestRunBase(BaseModel):
    test_suite_id: int
    environment: str = Field(default="development", max_length=50)
    branch: Optional[str] = Field(None, max_length=255)
    commit_hash: Optional[str] = Field(None, max_length=255)
    triggered_by: str = Field(default="manual", max_length=50)


class TestRunCreate(TestRunBase):
    pass


class TestRunOut(TestRunBase):
    id: int
    triggered_by_id: Optional[int]
    status: TestStatus
    started_at: datetime
    completed_at: Optional[datetime]
    duration: Optional[float]
    total_tests: int
    passed_tests: int
    failed_tests: int
    skipped_tests: int
    error_tests: int
    success_rate: Optional[float]
    error_message: Optional[str]
    error_traceback: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class TestRunSummary(BaseModel):
    id: int
    test_suite_name: str
    status: TestStatus
    started_at: datetime
    completed_at: Optional[datetime]
    duration: Optional[float]
    total_tests: int
    passed_tests: int
    failed_tests: int
    skipped_tests: int
    error_tests: int
    success_rate: Optional[float]
    environment: str
    triggered_by: str
    triggered_by_user: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# Test Result Schemas
class TestResultBase(BaseModel):
    test_case_id: int
    status: TestStatus
    output: Optional[str] = None
    error_message: Optional[str] = None
    error_traceback: Optional[str] = None
    duration: Optional[float] = Field(None, ge=0)
    request_url: Optional[str] = Field(None, max_length=500)
    request_method: Optional[str] = Field(None, max_length=10)
    request_headers: Optional[str] = None
    request_body: Optional[str] = None
    response_status: Optional[int] = None
    response_headers: Optional[str] = None
    response_body: Optional[str] = None
    retry_attempt: int = 0
    environment: str = "development"


class TestResultCreate(TestResultBase):
    test_run_id: int


class TestResultOut(TestResultBase):
    id: int
    test_run_id: int
    started_at: datetime
    completed_at: Optional[datetime]
    duration: Optional[float]
    created_at: datetime

    class Config:
        from_attributes = True


class TestResultDetail(TestResultOut):
    test_case_name: str
    test_suite_name: str
    test_type: str
    priority: TestPriority

    class Config:
        from_attributes = True


# Response Schemas
class TestSuiteListResponse(BaseModel):
    items: List[TestSuiteOut]
    total: int
    page: int
    page_size: int
    total_pages: int


class TestCaseListResponse(BaseModel):
    items: List[TestCaseOut]
    total: int
    page: int
    page_size: int
    total_pages: int


class TestRunListResponse(BaseModel):
    items: List[TestRunSummary]
    total: int
    page: int
    page_size: int
    total_pages: int


class TestResultListResponse(BaseModel):
    items: List[TestResultDetail]
    total: int
    page: int
    page_size: int
    total_pages: int


class TestStatistics(BaseModel):
    total_suites: int
    total_cases: int
    total_runs: int
    total_results: int
    passed_tests: int
    failed_tests: int
    skipped_tests: int
    error_tests: int
    success_rate: float
    average_duration: Optional[float]
    most_failed_tests: List[dict]
    recent_runs: List[TestRunSummary]


class TestRunExecutionRequest(BaseModel):
    test_suite_id: int
    environment: str = Field(default="development", max_length=50)
    branch: Optional[str] = Field(None, max_length=255)
    commit_hash: Optional[str] = Field(None, max_length=255)
    triggered_by: str = Field(default="manual", max_length=50)


class TestRunCompleteRequest(BaseModel):
    status: TestStatus
    total_tests: int = Field(ge=0)
    passed_tests: int = Field(ge=0)
    failed_tests: int = Field(ge=0)
    skipped_tests: int = Field(ge=0)
    error_tests: int = Field(ge=0)
    duration: float = Field(ge=0)
    error_message: Optional[str] = None
    error_traceback: Optional[str] = None

    @validator('total_tests')
    def validate_total_tests(cls, v, values):
        if 'passed_tests' in values and 'failed_tests' in values and 'skipped_tests' in values and 'error_tests' in values:
            total = values['passed_tests'] + values['failed_tests'] + values['skipped_tests'] + values['error_tests']
            if v != total:
                raise ValueError(f'total_tests ({v}) must equal sum of passed, failed, skipped, and error tests ({total})')
        return v

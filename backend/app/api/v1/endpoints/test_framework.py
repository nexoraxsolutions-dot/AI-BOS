from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app.core.request import get_client_ip, get_user_agent
from app.db.dependencies import get_async_session
from app.schemas import test_framework as test_framework_schema
from app.services import test_framework as test_framework_service
from app.services.audit_log import create_audit_log
from app.core.security import get_current_active_user, require_superuser

router = APIRouter()


# ==================== Test Suite Endpoints ====================

@router.post("/suites", response_model=test_framework_schema.TestSuiteOut, status_code=status.HTTP_201_CREATED)
async def create_test_suite(
    request: Request,
    payload: test_framework_schema.TestSuiteCreate,
    db: AsyncSession = Depends(get_async_session),
    current_user=Depends(require_superuser),
):
    """Create a new test suite."""
    test_suite = await test_framework_service.create_test_suite(
        db=db,
        name=payload.name,
        description=payload.description,
        is_active=payload.is_active,
        is_automated=payload.is_automated,
        company_id=payload.company_id,
        created_by_id=current_user.id,
    )
    return test_suite


@router.get("/suites", response_model=test_framework_schema.TestSuiteListResponse)
async def list_test_suites(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=100, description="Number of records to return"),
    search: Optional[str] = Query(None, description="Search by name"),
    company_id: Optional[int] = Query(None, description="Filter by company ID"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    db: AsyncSession = Depends(get_async_session),
    current_user=Depends(get_current_active_user),
):
    """List test suites with filtering and pagination."""
    test_suites, total = await test_framework_service.get_test_suites(
        db,
        skip=skip,
        limit=limit,
        company_id=company_id,
        is_active=is_active,
        search=search,
    )
    return test_framework_schema.TestSuiteListResponse(
        items=test_suites,
        total=total,
        page=(skip // limit) + 1,
        page_size=limit,
        total_pages=(total + limit - 1) // limit,
    )


@router.get("/suites/{test_suite_id}", response_model=test_framework_schema.TestSuiteOut)
async def get_test_suite(
    test_suite_id: int,
    db: AsyncSession = Depends(get_async_session),
    current_user=Depends(get_current_active_user),
):
    """Get test suite by ID."""
    test_suite = await test_framework_service.get_test_suite(db, test_suite_id)
    if not test_suite:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Test suite not found")
    return test_suite


@router.put("/suites/{test_suite_id}", response_model=test_framework_schema.TestSuiteOut)
async def update_test_suite(
    request: Request,
    test_suite_id: int,
    payload: test_framework_schema.TestSuiteUpdate,
    db: AsyncSession = Depends(get_async_session),
    current_user=Depends(require_superuser),
):
    """Update test suite."""
    test_suite = await test_framework_service.update_test_suite(
        db=db,
        test_suite_id=test_suite_id,
        name=payload.name,
        description=payload.description,
        is_active=payload.is_active,
        is_automated=payload.is_automated,
        company_id=payload.company_id,
    )
    if not test_suite:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Test suite not found")
    
    # Log test suite update
    await create_audit_log(
        db,
        action="update",
        resource_type="test_suite",
        resource_id=test_suite_id,
        user_id=current_user.id,
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request),
        details={"updated_fields": payload.model_dump(exclude_none=True)},
    )
    return test_suite


@router.delete("/suites/{test_suite_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_test_suite(
    request: Request,
    test_suite_id: int,
    db: AsyncSession = Depends(get_async_session),
    current_user=Depends(require_superuser),
):
    """Delete test suite."""
    # Fetch test suite before deletion for audit log
    test_suite_to_delete = await test_framework_service.get_test_suite(db, test_suite_id)
    deleted = await test_framework_service.delete_test_suite(db, test_suite_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Test suite not found")
    
    # Log test suite deletion
    await create_audit_log(
        db,
        action="delete",
        resource_type="test_suite",
        resource_id=test_suite_id,
        user_id=current_user.id,
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request),
        details={"suite_name": test_suite_to_delete.name if test_suite_to_delete else "unknown"},
    )
    return None


# ==================== Test Case Endpoints ====================

@router.post("/cases", response_model=test_framework_schema.TestCaseOut, status_code=status.HTTP_201_CREATED)
async def create_test_case(
    request: Request,
    payload: test_framework_schema.TestCaseCreate,
    db: AsyncSession = Depends(get_async_session),
    current_user=Depends(require_superuser),
):
    """Create a new test case."""
    test_case = await test_framework_service.create_test_case(
        db=db,
        test_suite_id=payload.test_suite_id,
        name=payload.name,
        description=payload.description,
        priority=payload.priority,
        test_type=payload.test_type,
        endpoint=payload.endpoint,
        method=payload.method,
        payload=payload.payload,
        expected_status=payload.expected_status,
        expected_response=payload.expected_response,
        tags=payload.tags,
        timeout=payload.timeout,
        retry_count=payload.retry_count,
        is_active=payload.is_active,
        order=payload.order,
    )
    
    # Log test case creation
    await create_audit_log(
        db,
        action="create",
        resource_type="test_case",
        resource_id=test_case.id,
        user_id=current_user.id,
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request),
        details={"test_case_name": test_case.name, "test_suite_id": test_case.test_suite_id},
    )
    return test_case


@router.get("/cases", response_model=test_framework_schema.TestCaseListResponse)
async def list_test_cases(
    test_suite_id: int = Query(..., description="Test suite ID"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=100, description="Number of records to return"),
    priority: Optional[test_framework_schema.TestPriority] = Query(None, description="Filter by priority"),
    status: Optional[test_framework_schema.TestStatus] = Query(None, description="Filter by status"),
    test_type: Optional[str] = Query(None, description="Filter by test type"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    db: AsyncSession = Depends(get_async_session),
    current_user=Depends(get_current_active_user),
):
    """List test cases with filtering and pagination."""
    test_cases, total = await test_framework_service.get_test_cases(
        db,
        test_suite_id=test_suite_id,
        skip=skip,
        limit=limit,
        priority=priority,
        status=status,
        test_type=test_type,
        is_active=is_active,
    )
    return test_framework_schema.TestCaseListResponse(
        items=test_cases,
        total=total,
        page=(skip // limit) + 1,
        page_size=limit,
        total_pages=(total + limit - 1) // limit,
    )


@router.get("/cases/{test_case_id}", response_model=test_framework_schema.TestCaseOut)
async def get_test_case(
    test_case_id: int,
    db: AsyncSession = Depends(get_async_session),
    current_user=Depends(get_current_active_user),
):
    """Get test case by ID."""
    test_case = await test_framework_service.get_test_case(db, test_case_id)
    if not test_case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Test case not found")
    return test_case


@router.put("/cases/{test_case_id}", response_model=test_framework_schema.TestCaseOut)
async def update_test_case(
    request: Request,
    test_case_id: int,
    payload: test_framework_schema.TestCaseUpdate,
    db: AsyncSession = Depends(get_async_session),
    current_user=Depends(require_superuser),
):
    """Update test case."""
    test_case = await test_framework_service.update_test_case(
        db=db,
        test_case_id=test_case_id,
        name=payload.name,
        description=payload.description,
        priority=payload.priority,
        test_type=payload.test_type,
        endpoint=payload.endpoint,
        method=payload.method,
        payload=payload.payload,
        expected_status=payload.expected_status,
        expected_response=payload.expected_response,
        tags=payload.tags,
        timeout=payload.timeout,
        retry_count=payload.retry_count,
        is_active=payload.is_active,
        order=payload.order,
    )
    if not test_case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Test case not found")
    
    # Log test case update
    await create_audit_log(
        db,
        action="update",
        resource_type="test_case",
        resource_id=test_case_id,
        user_id=current_user.id,
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request),
        details={"updated_fields": payload.model_dump(exclude_none=True)},
    )
    return test_case


@router.delete("/cases/{test_case_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_test_case(
    request: Request,
    test_case_id: int,
    db: AsyncSession = Depends(get_async_session),
    current_user=Depends(require_superuser),
):
    """Delete test case."""
    # Fetch test case before deletion for audit log
    test_case_to_delete = await test_framework_service.get_test_case(db, test_case_id)
    deleted = await test_framework_service.delete_test_case(db, test_case_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Test case not found")
    
    # Log test case deletion
    await create_audit_log(
        db,
        action="delete",
        resource_type="test_case",
        resource_id=test_case_id,
        user_id=current_user.id,
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request),
        details={"test_case_name": test_case_to_delete.name if test_case_to_delete else "unknown"},
    )
    return None


# ==================== Test Run Endpoints ====================

@router.post("/runs", response_model=test_framework_schema.TestRunOut, status_code=status.HTTP_201_CREATED)
async def create_test_run(
    request: Request,
    payload: test_framework_schema.TestRunCreate,
    db: AsyncSession = Depends(get_async_session),
    current_user=Depends(get_current_active_user),
):
    """Create a new test run."""
    test_run = await test_framework_service.create_test_run(
        db=db,
        test_suite_id=payload.test_suite_id,
        triggered_by_id=current_user.id,
        environment=payload.environment,
        branch=payload.branch,
        commit_hash=payload.commit_hash,
        triggered_by=payload.triggered_by,
    )
    
    # Log test run creation
    await create_audit_log(
        db,
        action="create",
        resource_type="test_run",
        resource_id=test_run.id,
        user_id=current_user.id,
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request),
        details={"test_suite_id": payload.test_suite_id, "environment": payload.environment},
    )
    return test_run


@router.get("/runs", response_model=test_framework_schema.TestRunListResponse)
async def list_test_runs(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=100, description="Number of records to return"),
    test_suite_id: Optional[int] = Query(None, description="Filter by test suite ID"),
    status: Optional[test_framework_schema.TestStatus] = Query(None, description="Filter by status"),
    environment: Optional[str] = Query(None, description="Filter by environment"),
    db: AsyncSession = Depends(get_async_session),
    current_user=Depends(get_current_active_user),
):
    """List test runs with filtering and pagination."""
    test_runs, total = await test_framework_service.get_test_runs(
        db,
        skip=skip,
        limit=limit,
        test_suite_id=test_suite_id,
        status=status,
        environment=environment,
    )
    
    # Convert to summary format
    items = []
    for run in test_runs:
        suite_name = run.test_suite.name if run.test_suite else "Unknown"
        triggered_by_user = run.triggered_by_user.full_name if run.triggered_by_user else None
        items.append(test_framework_schema.TestRunSummary(
            id=run.id,
            test_suite_name=suite_name,
            status=run.status,
            started_at=run.started_at,
            completed_at=run.completed_at,
            duration=run.duration,
            total_tests=run.total_tests,
            passed_tests=run.passed_tests,
            failed_tests=run.failed_tests,
            skipped_tests=run.skipped_tests,
            error_tests=run.error_tests,
            success_rate=run.success_rate,
            environment=run.environment,
            triggered_by=run.triggered_by,
            triggered_by_user=triggered_by_user,
            created_at=run.created_at,
        ))
    
    return test_framework_schema.TestRunListResponse(
        items=items,
        total=total,
        page=(skip // limit) + 1,
        page_size=limit,
        total_pages=(total + limit - 1) // limit,
    )


@router.get("/runs/{test_run_id}", response_model=test_framework_schema.TestRunOut)
async def get_test_run(
    test_run_id: int,
    db: AsyncSession = Depends(get_async_session),
    current_user=Depends(get_current_active_user),
):
    """Get test run by ID."""
    test_run = await test_framework_service.get_test_run(db, test_run_id)
    if not test_run:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Test run not found")
    return test_run


@router.post("/runs/{test_run_id}/complete", response_model=test_framework_schema.TestRunOut)
async def complete_test_run(
    request: Request,
    test_run_id: int,
    payload: test_framework_schema.TestRunCompleteRequest,
    db: AsyncSession = Depends(get_async_session),
    current_user=Depends(get_current_active_user),
):
    """Complete a test run with results."""
    test_run = await test_framework_service.complete_test_run(
        db=db,
        test_run_id=test_run_id,
        status=payload.status,
        total_tests=payload.total_tests,
        passed_tests=payload.passed_tests,
        failed_tests=payload.failed_tests,
        skipped_tests=payload.skipped_tests,
        error_tests=payload.error_tests,
        duration=payload.duration,
        error_message=payload.error_message,
        error_traceback=payload.error_traceback,
    )
    if not test_run:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Test run not found")
    
    # Log test run completion
    await create_audit_log(
        db,
        action="complete",
        resource_type="test_run",
        resource_id=test_run_id,
        user_id=current_user.id,
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request),
        details={
            "status": payload.status.value,
            "total_tests": payload.total_tests,
            "passed_tests": payload.passed_tests,
            "failed_tests": payload.failed_tests,
            "success_rate": test_run.success_rate,
        },
    )
    return test_run


# ==================== Test Result Endpoints ====================

@router.post("/results", response_model=test_framework_schema.TestResultOut, status_code=status.HTTP_201_CREATED)
async def create_test_result(
    request: Request,
    payload: test_framework_schema.TestResultCreate,
    db: AsyncSession = Depends(get_async_session),
    current_user=Depends(get_current_active_user),
):
    """Create a new test result."""
    test_result = await test_framework_service.create_test_result(
        db=db,
        test_run_id=payload.test_run_id,
        test_case_id=payload.test_case_id,
        status=payload.status,
        output=payload.output,
        error_message=payload.error_message,
        error_traceback=payload.error_traceback,
        request_url=payload.request_url,
        request_method=payload.request_method,
        request_headers=payload.request_headers,
        request_body=payload.request_body,
        response_status=payload.response_status,
        response_headers=payload.response_headers,
        response_body=payload.response_body,
        duration=payload.duration,
        retry_attempt=payload.retry_attempt,
        environment=payload.environment,
    )
    return test_result


@router.get("/results", response_model=test_framework_schema.TestResultListResponse)
async def list_test_results(
    test_run_id: int = Query(..., description="Test run ID"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=100, description="Number of records to return"),
    status: Optional[test_framework_schema.TestStatus] = Query(None, description="Filter by status"),
    db: AsyncSession = Depends(get_async_session),
    current_user=Depends(get_current_active_user),
):
    """List test results for a test run."""
    test_results, total = await test_framework_service.get_test_results(
        db,
        test_run_id=test_run_id,
        skip=skip,
        limit=limit,
        status=status,
    )
    
    # Convert to detail format
    items = []
    for result in test_results:
        test_case = result.test_case
        test_suite = test_case.test_suite if test_case else None
        items.append(test_framework_schema.TestResultDetail(
            id=result.id,
            test_run_id=result.test_run_id,
            test_case_id=result.test_case_id,
            test_case_name=test_case.name if test_case else "Unknown",
            test_suite_name=test_suite.name if test_suite else "Unknown",
            test_type=test_case.test_type if test_case else "unknown",
            priority=test_case.priority if test_case else test_framework_schema.TestPriority.MEDIUM,
            status=result.status,
            started_at=result.started_at,
            completed_at=result.completed_at,
            duration=result.duration,
            output=result.output,
            error_message=result.error_message,
            error_traceback=result.error_traceback,
            request_url=result.request_url,
            request_method=result.request_method,
            response_status=result.response_status,
            retry_attempt=result.retry_attempt,
            environment=result.environment,
            created_at=result.created_at,
        ))
    
    return test_framework_schema.TestResultListResponse(
        items=items,
        total=total,
        page=(skip // limit) + 1,
        page_size=limit,
        total_pages=(total + limit - 1) // limit,
    )


# ==================== Statistics Endpoints ====================

@router.get("/statistics", response_model=test_framework_schema.TestStatistics)
async def get_test_statistics(
    company_id: Optional[int] = Query(None, description="Filter by company ID"),
    db: AsyncSession = Depends(get_async_session),
    current_user=Depends(get_current_active_user),
):
    """Get test framework statistics."""
    stats = await test_framework_service.get_test_statistics(db, company_id=company_id)
    return test_framework_schema.TestStatistics(**stats)
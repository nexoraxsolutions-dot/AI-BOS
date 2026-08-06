import logging
from datetime import datetime
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.test_framework import TestSuite, TestCase, TestRun, TestResult, TestStatus, TestPriority
from app.models.audit_log import AuditLog
from app.services.cache import cache_service
from app.services.audit_log import create_audit_log

logger = logging.getLogger("ai_bos")


# Test Suite Services
async def create_test_suite(
    db: AsyncSession,
    name: str,
    created_by_id: int,
    description: str | None = None,
    is_active: bool = True,
    is_automated: bool = True,
    company_id: int | None = None,
) -> TestSuite:
    """Create a new test suite."""
    test_suite = TestSuite(
        name=name,
        description=description,
        is_active=is_active,
        is_automated=is_automated,
        company_id=company_id,
        created_by_id=created_by_id,
    )
    db.add(test_suite)
    await db.commit()
    await db.refresh(test_suite)

    # Create audit log
    await create_audit_log(
        db=db,
        action="create",
        resource_type="test_suite",
        resource_id=test_suite.id,
        user_id=created_by_id,
        details={"name": name, "company_id": company_id},
    )

    return test_suite


async def get_test_suite(db: AsyncSession, test_suite_id: int) -> TestSuite | None:
    """Get test suite by ID."""
    cache_key = f"test_suite:{test_suite_id}"
    cached = await cache_service.get(cache_key)
    if cached:
        return cached

    result = await db.execute(
        select(TestSuite)
        .options(joinedload(TestSuite.test_cases))
        .where(TestSuite.id == test_suite_id)
    )
    test_suite = result.scalars().unique().first()

    if test_suite:
        await cache_service.set(cache_key, test_suite.__dict__, ttl=600)

    return test_suite


async def get_test_suites(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 50,
    company_id: int | None = None,
    is_active: bool | None = None,
    search: str | None = None,
) -> tuple[list[TestSuite], int]:
    """Get test suites with filtering and pagination."""
    cache_key = f"test_suites:{skip}:{limit}:{company_id or 'all'}:{is_active or 'all'}:{search or 'all'}"
    cached = await cache_service.get(cache_key)
    if cached:
        return cached

    query = select(TestSuite)

    if company_id:
        query = query.where(TestSuite.company_id == company_id)
    if is_active is not None:
        query = query.where(TestSuite.is_active == is_active)
    if search:
        query = query.where(TestSuite.name.ilike(f"%{search}%"))

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar_one()

    # Get paginated results
    query = query.offset(skip).limit(limit).order_by(TestSuite.created_at.desc())
    result = await db.execute(query)
    test_suites = result.scalars().all()

    result = (test_suites, total)
    await cache_service.set(cache_key, result, ttl=300)

    return result


async def update_test_suite(
    db: AsyncSession,
    test_suite_id: int,
    name: str | None = None,
    description: str | None = None,
    is_active: bool | None = None,
    is_automated: bool | None = None,
    company_id: int | None = None,
) -> TestSuite | None:
    """Update test suite."""
    test_suite = await get_test_suite(db, test_suite_id)
    if not test_suite:
        return None

    if name is not None:
        test_suite.name = name
    if description is not None:
        test_suite.description = description
    if is_active is not None:
        test_suite.is_active = is_active
    if is_automated is not None:
        test_suite.is_automated = is_automated
    if company_id is not None:
        test_suite.company_id = company_id

    await db.commit()
    await db.refresh(test_suite)

    # Invalidate cache
    await cache_service.delete(f"test_suite:{test_suite_id}")
    await cache_service.delete_pattern("test_suites:*")

    # Create audit log
    await create_audit_log(
        db=db,
        action="update",
        resource_type="test_suite",
        resource_id=test_suite_id,
        details={"updated_fields": {"name": name, "description": description, "is_active": is_active}},
    )

    return test_suite


async def delete_test_suite(db: AsyncSession, test_suite_id: int) -> bool:
    """Delete test suite."""
    test_suite = await get_test_suite(db, test_suite_id)
    if not test_suite:
        return False

    await db.delete(test_suite)
    await db.commit()

    # Invalidate cache
    await cache_service.delete(f"test_suite:{test_suite_id}")
    await cache_service.delete_pattern("test_suites:*")

    # Create audit log
    await create_audit_log(
        db=db,
        action="delete",
        resource_type="test_suite",
        resource_id=test_suite_id,
        details={"name": test_suite.name},
    )

    return True


# Test Case Services
async def create_test_case(
    db: AsyncSession,
    test_suite_id: int,
    name: str,
    test_type: str,
    priority: TestPriority = TestPriority.MEDIUM,
    description: str | None = None,
    endpoint: str | None = None,
    method: str | None = None,
    payload: str | None = None,
    expected_status: int | None = None,
    expected_response: str | None = None,
    tags: str | None = None,
    timeout: int = 30,
    retry_count: int = 0,
    is_active: bool = True,
    order: int = 0,
) -> TestCase:
    """Create a new test case."""
    test_case = TestCase(
        test_suite_id=test_suite_id,
        name=name,
        description=description,
        priority=priority,
        test_type=test_type,
        endpoint=endpoint,
        method=method,
        payload=payload,
        expected_status=expected_status,
        expected_response=expected_response,
        tags=tags,
        timeout=timeout,
        retry_count=retry_count,
        is_active=is_active,
        order=order,
    )
    db.add(test_case)
    await db.commit()
    await db.refresh(test_case)

    # Invalidate cache
    await cache_service.delete_pattern(f"test_suite:{test_suite_id}:*")

    return test_case


async def get_test_case(db: AsyncSession, test_case_id: int) -> TestCase | None:
    """Get test case by ID."""
    cache_key = f"test_case:{test_case_id}"
    cached = await cache_service.get(cache_key)
    if cached:
        return cached

    result = await db.execute(select(TestCase).where(TestCase.id == test_case_id))
    test_case = result.scalar_one_or_none()

    if test_case:
        await cache_service.set(cache_key, test_case.__dict__, ttl=600)

    return test_case


async def get_test_cases(
    db: AsyncSession,
    test_suite_id: int,
    skip: int = 0,
    limit: int = 50,
    priority: TestPriority | None = None,
    status: TestStatus | None = None,
    test_type: str | None = None,
    is_active: bool | None = None,
) -> tuple[list[TestCase], int]:
    """Get test cases with filtering and pagination."""
    cache_key = f"test_cases:{test_suite_id}:{skip}:{limit}:{priority or 'all'}:{status or 'all'}:{test_type or 'all'}:{is_active or 'all'}"
    cached = await cache_service.get(cache_key)
    if cached:
        return cached

    query = select(TestCase).where(TestCase.test_suite_id == test_suite_id)

    if priority:
        query = query.where(TestCase.priority == priority)
    if status:
        query = query.where(TestCase.status == status)
    if test_type:
        query = query.where(TestCase.test_type == test_type)
    if is_active is not None:
        query = query.where(TestCase.is_active == is_active)

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar_one()

    # Get paginated results
    query = query.offset(skip).limit(limit).order_by(TestCase.order, TestCase.id)
    result = await db.execute(query)
    test_cases = result.scalars().all()

    result = (test_cases, total)
    await cache_service.set(cache_key, result, ttl=300)

    return result


async def update_test_case(
    db: AsyncSession,
    test_case_id: int,
    name: str | None = None,
    description: str | None = None,
    priority: TestPriority | None = None,
    test_type: str | None = None,
    endpoint: str | None = None,
    method: str | None = None,
    payload: str | None = None,
    expected_status: int | None = None,
    expected_response: str | None = None,
    tags: str | None = None,
    timeout: int | None = None,
    retry_count: int | None = None,
    is_active: bool | None = None,
    order: int | None = None,
) -> TestCase | None:
    """Update test case."""
    test_case = await get_test_case(db, test_case_id)
    if not test_case:
        return None

    if name is not None:
        test_case.name = name
    if description is not None:
        test_case.description = description
    if priority is not None:
        test_case.priority = priority
    if test_type is not None:
        test_case.test_type = test_type
    if endpoint is not None:
        test_case.endpoint = endpoint
    if method is not None:
        test_case.method = method
    if payload is not None:
        test_case.payload = payload
    if expected_status is not None:
        test_case.expected_status = expected_status
    if expected_response is not None:
        test_case.expected_response = expected_response
    if tags is not None:
        test_case.tags = tags
    if timeout is not None:
        test_case.timeout = timeout
    if retry_count is not None:
        test_case.retry_count = retry_count
    if is_active is not None:
        test_case.is_active = is_active
    if order is not None:
        test_case.order = order

    await db.commit()
    await db.refresh(test_case)

    # Invalidate cache
    await cache_service.delete(f"test_case:{test_case_id}")
    await cache_service.delete_pattern(f"test_cases:{test_case.test_suite_id}:*")

    return test_case


async def delete_test_case(db: AsyncSession, test_case_id: int) -> bool:
    """Delete test case."""
    test_case = await get_test_case(db, test_case_id)
    if not test_case:
        return False

    test_suite_id = test_case.test_suite_id
    await db.delete(test_case)
    await db.commit()

    # Invalidate cache
    await cache_service.delete(f"test_case:{test_case_id}")
    await cache_service.delete_pattern(f"test_cases:{test_suite_id}:*")

    return True


# Test Run Services
async def create_test_run(
    db: AsyncSession,
    test_suite_id: int,
    triggered_by_id: int | None = None,
    environment: str = "development",
    branch: str | None = None,
    commit_hash: str | None = None,
    triggered_by: str = "manual",
) -> TestRun:
    """Create a new test run."""
    test_run = TestRun(
        test_suite_id=test_suite_id,
        triggered_by_id=triggered_by_id,
        environment=environment,
        branch=branch,
        commit_hash=commit_hash,
        triggered_by=triggered_by,
        status=TestStatus.RUNNING,
    )
    db.add(test_run)
    await db.commit()
    await db.refresh(test_run)

    return test_run


async def get_test_run(db: AsyncSession, test_run_id: int) -> TestRun | None:
    """Get test run by ID."""
    cache_key = f"test_run:{test_run_id}"
    cached = await cache_service.get(cache_key)
    if cached:
        return cached

    result = await db.execute(
        select(TestRun)
        .options(joinedload(TestRun.test_results))
        .where(TestRun.id == test_run_id)
    )
    test_run = result.scalars().unique().first()

    if test_run:
        await cache_service.set(cache_key, test_run.__dict__, ttl=600)

    return test_run


async def get_test_runs(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 50,
    test_suite_id: int | None = None,
    status: TestStatus | None = None,
    environment: str | None = None,
) -> tuple[list[TestRun], int]:
    """Get test runs with filtering and pagination."""
    cache_key = f"test_runs:{skip}:{limit}:{test_suite_id or 'all'}:{status or 'all'}:{environment or 'all'}"
    cached = await cache_service.get(cache_key)
    if cached:
        return cached

    query = select(TestRun)

    if test_suite_id:
        query = query.where(TestRun.test_suite_id == test_suite_id)
    if status:
        query = query.where(TestRun.status == status)
    if environment:
        query = query.where(TestRun.environment == environment)

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar_one()

    # Get paginated results
    query = query.offset(skip).limit(limit).order_by(TestRun.created_at.desc())
    result = await db.execute(query)
    test_runs = result.scalars().all()

    result = (test_runs, total)
    await cache_service.set(cache_key, result, ttl=300)

    return result


async def complete_test_run(
    db: AsyncSession,
    test_run_id: int,
    status: TestStatus,
    total_tests: int,
    passed_tests: int,
    failed_tests: int,
    skipped_tests: int,
    error_tests: int,
    duration: float,
    error_message: str | None = None,
    error_traceback: str | None = None,
) -> TestRun | None:
    """Complete a test run with results."""
    test_run = await get_test_run(db, test_run_id)
    if not test_run:
        return None

    test_run.status = status
    test_run.completed_at = datetime.utcnow()
    test_run.duration = duration
    test_run.total_tests = total_tests
    test_run.passed_tests = passed_tests
    test_run.failed_tests = failed_tests
    test_run.skipped_tests = skipped_tests
    test_run.error_tests = error_tests
    test_run.success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
    test_run.error_message = error_message
    test_run.error_traceback = error_traceback

    await db.commit()
    await db.refresh(test_run)

    # Invalidate cache
    await cache_service.delete(f"test_run:{test_run_id}")
    await cache_service.delete_pattern("test_runs:*")

    return test_run


# Test Result Services
async def create_test_result(
    db: AsyncSession,
    test_run_id: int,
    test_case_id: int,
    status: TestStatus,
    output: str | None = None,
    error_message: str | None = None,
    error_traceback: str | None = None,
    request_url: str | None = None,
    request_method: str | None = None,
    request_headers: str | None = None,
    request_body: str | None = None,
    response_status: int | None = None,
    response_headers: str | None = None,
    response_body: str | None = None,
    duration: float | None = None,
    retry_attempt: int = 0,
    environment: str = "development",
) -> TestResult:
    """Create a new test result."""
    test_result = TestResult(
        test_run_id=test_run_id,
        test_case_id=test_case_id,
        status=status,
        output=output,
        error_message=error_message,
        error_traceback=error_traceback,
        request_url=request_url,
        request_method=request_method,
        request_headers=request_headers,
        request_body=request_body,
        response_status=response_status,
        response_headers=response_headers,
        response_body=response_body,
        duration=duration,
        retry_attempt=retry_attempt,
        environment=environment,
    )
    db.add(test_result)
    await db.commit()
    await db.refresh(test_result)

    # Update test case statistics
    test_case = await get_test_case(db, test_case_id)
    if test_case:
        test_case.last_run_at = datetime.utcnow()
        test_case.last_run_status = status
        test_case.last_run_duration = duration
        if status == TestStatus.PASSED:
            test_case.success_count += 1
        elif status == TestStatus.FAILED:
            test_case.failure_count += 1
        await db.commit()

    return test_result


async def get_test_results(
    db: AsyncSession,
    test_run_id: int,
    skip: int = 0,
    limit: int = 50,
    status: TestStatus | None = None,
) -> tuple[list[TestResult], int]:
    """Get test results for a test run."""
    query = select(TestResult).where(TestResult.test_run_id == test_run_id)

    if status:
        query = query.where(TestResult.status == status)

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar_one()

    # Get paginated results
    query = query.offset(skip).limit(limit).order_by(TestResult.created_at.desc())
    result = await db.execute(query)
    test_results = result.scalars().all()

    return test_results, total


# Statistics Services
async def get_test_statistics(db: AsyncSession, company_id: int | None = None) -> dict:
    """Get test framework statistics."""
    # Get test suites count
    suites_query = select(func.count()).select_from(TestSuite)
    if company_id:
        suites_query = suites_query.where(TestSuite.company_id == company_id)
    total_suites = (await db.execute(suites_query)).scalar_one()

    # Get test cases count
    cases_query = select(func.count()).select_from(TestCase)
    if company_id:
        cases_query = cases_query.join(TestSuite).where(TestSuite.company_id == company_id)
    total_cases = (await db.execute(cases_query)).scalar_one()

    # Get test runs count
    runs_query = select(func.count()).select_from(TestRun)
    if company_id:
        runs_query = runs_query.join(TestSuite).where(TestSuite.company_id == company_id)
    total_runs = (await db.execute(runs_query)).scalar_one()

    # Get test results count
    results_query = select(func.count()).select_from(TestResult)
    if company_id:
        results_query = results_query.join(TestRun).join(TestSuite).where(TestSuite.company_id == company_id)
    total_results = (await db.execute(results_query)).scalar_one()

    # Get passed/failed/skipped/error counts
    passed_query = select(func.count()).select_from(TestResult).where(TestResult.status == TestStatus.PASSED)
    failed_query = select(func.count()).select_from(TestResult).where(TestResult.status == TestStatus.FAILED)
    skipped_query = select(func.count()).select_from(TestResult).where(TestResult.status == TestStatus.SKIPPED)
    error_query = select(func.count()).select_from(TestResult).where(TestResult.status == TestStatus.ERROR)

    if company_id:
        passed_query = passed_query.join(TestRun).join(TestSuite).where(TestSuite.company_id == company_id)
        failed_query = failed_query.join(TestRun).join(TestSuite).where(TestSuite.company_id == company_id)
        skipped_query = skipped_query.join(TestRun).join(TestSuite).where(TestSuite.company_id == company_id)
        error_query = error_query.join(TestRun).join(TestSuite).where(TestSuite.company_id == company_id)

    passed_tests = (await db.execute(passed_query)).scalar_one()
    failed_tests = (await db.execute(failed_query)).scalar_one()
    skipped_tests = (await db.execute(skipped_query)).scalar_one()
    error_tests = (await db.execute(error_query)).scalar_one()

    # Calculate success rate
    success_rate = (passed_tests / total_results * 100) if total_results > 0 else 0

    # Get most failed tests
    most_failed = []
    failed_tests_query = (
        select(TestCase.name, func.count(TestResult.id).label('failure_count'))
        .join(TestResult)
        .where(TestResult.status == TestStatus.FAILED)
        .group_by(TestCase.id, TestCase.name)
        .order_by(desc('failure_count'))
        .limit(5)
    )
    if company_id:
        failed_tests_query = failed_tests_query.join(TestSuite).where(TestSuite.company_id == company_id)

    failed_tests_result = await db.execute(failed_tests_query)
    for row in failed_tests_result.all():
        most_failed.append({"name": row[0], "failures": row[1]})

    # Get recent runs
    recent_runs_query = (
        select(TestRun, TestSuite.name.label('suite_name'))
        .join(TestSuite)
        .options(joinedload(TestRun.triggered_by_user))
        .order_by(TestRun.created_at.desc())
        .limit(10)
    )
    if company_id:
        recent_runs_query = recent_runs_query.where(TestSuite.company_id == company_id)

    recent_runs_result = await db.execute(recent_runs_query)
    recent_runs = []
    for row in recent_runs_result.all():
        run = row[0]
        triggered_by_user_name = run.triggered_by_user.full_name if run.triggered_by_user else None
        recent_runs.append({
            "id": run.id,
            "test_suite_name": row[1],
            "status": run.status,
            "started_at": run.started_at,
            "completed_at": run.completed_at,
            "duration": run.duration,
            "total_tests": run.total_tests,
            "passed_tests": run.passed_tests,
            "failed_tests": run.failed_tests,
            "skipped_tests": run.skipped_tests,
            "error_tests": run.error_tests,
            "success_rate": run.success_rate,
            "environment": run.environment,
            "triggered_by": run.triggered_by,
            "triggered_by_user": triggered_by_user_name,
            "created_at": run.created_at,
        })

    # Calculate average duration from completed runs
    avg_duration_query = select(func.avg(TestRun.duration)).where(TestRun.duration.isnot(None))
    if company_id:
        avg_duration_query = avg_duration_query.join(TestSuite).where(TestSuite.company_id == company_id)
    avg_duration_result = await db.execute(avg_duration_query)
    average_duration = avg_duration_result.scalar_one_or_none()

    return {
        "total_suites": total_suites,
        "total_cases": total_cases,
        "total_runs": total_runs,
        "total_results": total_results,
        "passed_tests": passed_tests,
        "failed_tests": failed_tests,
        "skipped_tests": skipped_tests,
        "error_tests": error_tests,
        "success_rate": round(success_rate, 2),
        "average_duration": round(average_duration, 2) if average_duration else None,
        "most_failed_tests": most_failed,
        "recent_runs": recent_runs,
    }

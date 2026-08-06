import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta

from app.models.test_framework import TestSuite, TestCase, TestRun, TestResult, TestStatus, TestPriority
from app.schemas.test_framework import TestRunExecutionRequest


class TestTestSuites:
    """Test test suite endpoints."""

    @pytest.mark.asyncio
    async def test_create_test_suite(self, client: AsyncClient, admin_token_headers: dict, test_company):
        """Test creating a test suite."""
        response = await client.post(
            "/api/v1/testing/suites",
            headers=admin_token_headers,
            json={
                "name": "API Tests",
                "description": "API integration tests",
                "is_active": True,
                "is_automated": True,
                "company_id": test_company.id,
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "API Tests"
        assert data["description"] == "API integration tests"
        assert data["is_active"] is True
        assert data["is_automated"] is True
        assert data["company_id"] == test_company.id
        assert "id" in data

    @pytest.mark.asyncio
    async def test_create_test_suite_unauthorized(self, client: AsyncClient, user_token_headers: dict):
        """Test that regular users cannot create test suites."""
        response = await client.post(
            "/api/v1/testing/suites",
            headers=user_token_headers,
            json={
                "name": "Test Suite",
                "description": "Test",
            },
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_list_test_suites(self, client: AsyncClient, admin_token_headers: dict, db_session: AsyncSession, test_company):
        """Test listing test suites."""
        # Create test suites
        suite1 = TestSuite(name="Suite 1", company_id=test_company.id, created_by_id=1)
        suite2 = TestSuite(name="Suite 2", company_id=test_company.id, created_by_id=1)
        db_session.add_all([suite1, suite2])
        await db_session.commit()

        response = await client.get(
            "/api/v1/testing/suites",
            headers=admin_token_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert data["total"] >= 2

    @pytest.mark.asyncio
    async def test_list_test_suites_with_filters(self, client: AsyncClient, admin_token_headers: dict, db_session: AsyncSession, test_company):
        """Test listing test suites with filters."""
        # Create test suites
        suite1 = TestSuite(name="Active Suite", company_id=test_company.id, is_active=True, created_by_id=1)
        suite2 = TestSuite(name="Inactive Suite", company_id=test_company.id, is_active=False, created_by_id=1)
        db_session.add_all([suite1, suite2])
        await db_session.commit()

        # Filter by active status
        response = await client.get(
            "/api/v1/testing/suites",
            headers=admin_token_headers,
            params={"is_active": True},
        )
        assert response.status_code == 200
        data = response.json()
        assert all(suite["is_active"] for suite in data["items"])

    @pytest.mark.asyncio
    async def test_get_test_suite(self, client: AsyncClient, admin_token_headers: dict, db_session: AsyncSession, test_company, admin_user):
        """Test getting a specific test suite."""
        suite = TestSuite(name="Test Suite", company_id=test_company.id, created_by_id=admin_user.id)
        db_session.add(suite)
        await db_session.commit()
        await db_session.refresh(suite)

        response = await client.get(
            f"/api/v1/testing/suites/{suite.id}",
            headers=admin_token_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Test Suite"
        assert data["id"] == suite.id

    @pytest.mark.asyncio
    async def test_get_test_suite_not_found(self, client: AsyncClient, admin_token_headers: dict):
        """Test getting a non-existent test suite."""
        response = await client.get(
            "/api/v1/testing/suites/99999",
            headers=admin_token_headers,
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_test_suite(self, client: AsyncClient, admin_token_headers: dict, db_session: AsyncSession, test_company, admin_user):
        """Test updating a test suite."""
        suite = TestSuite(name="Old Name", company_id=test_company.id, created_by_id=admin_user.id)
        db_session.add(suite)
        await db_session.commit()
        await db_session.refresh(suite)

        response = await client.put(
            f"/api/v1/testing/suites/{suite.id}",
            headers=admin_token_headers,
            json={
                "name": "New Name",
                "description": "Updated description",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "New Name"
        assert data["description"] == "Updated description"

    @pytest.mark.asyncio
    async def test_delete_test_suite(self, client: AsyncClient, admin_token_headers: dict, db_session: AsyncSession, test_company, admin_user):
        """Test deleting a test suite."""
        suite = TestSuite(name="To Delete", company_id=test_company.id, created_by_id=admin_user.id)
        db_session.add(suite)
        await db_session.commit()
        await db_session.refresh(suite)

        response = await client.delete(
            f"/api/v1/testing/suites/{suite.id}",
            headers=admin_token_headers,
        )
        assert response.status_code == 204

        # Verify deletion
        result = await db_session.execute(
            select(TestSuite).where(TestSuite.id == suite.id)
        )
        assert result.scalar_one_or_none() is None


class TestTestCases:
    """Test test case endpoints."""

    @pytest.mark.asyncio
    async def test_create_test_case(self, client: AsyncClient, admin_token_headers: dict, db_session: AsyncSession, test_company):
        """Test creating a test case."""
        # Create test suite
        suite = TestSuite(name="Test Suite", company_id=test_company.id, created_by_id=1)
        db_session.add(suite)
        await db_session.commit()
        await db_session.refresh(suite)

        response = await client.post(
            "/api/v1/testing/cases",
            headers=admin_token_headers,
            json={
                "test_suite_id": suite.id,
                "name": "Test Login API",
                "description": "Test user login",
                "priority": "high",
                "test_type": "integration",
                "endpoint": "/api/v1/auth/login",
                "method": "POST",
                "payload": '{"email": "test@example.com", "password": "pass123"}',
                "expected_status": 200,
                "timeout": 30,
                "retry_count": 2,
                "order": 1,
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test Login API"
        assert data["priority"] == "high"
        assert data["test_type"] == "integration"
        assert data["method"] == "POST"
        assert data["test_suite_id"] == suite.id

    @pytest.mark.asyncio
    async def test_create_test_case_invalid_method(self, client: AsyncClient, admin_token_headers: dict, db_session: AsyncSession, test_company):
        """Test creating a test case with invalid HTTP method."""
        suite = TestSuite(name="Test Suite", company_id=test_company.id, created_by_id=1)
        db_session.add(suite)
        await db_session.commit()
        await db_session.refresh(suite)

        response = await client.post(
            "/api/v1/testing/cases",
            headers=admin_token_headers,
            json={
                "test_suite_id": suite.id,
                "name": "Test Case",
                "test_type": "unit",
                "method": "INVALID",
            },
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_test_case_invalid_type(self, client: AsyncClient, admin_token_headers: dict, db_session: AsyncSession, test_company):
        """Test creating a test case with invalid test type."""
        suite = TestSuite(name="Test Suite", company_id=test_company.id, created_by_id=1)
        db_session.add(suite)
        await db_session.commit()
        await db_session.refresh(suite)

        response = await client.post(
            "/api/v1/testing/cases",
            headers=admin_token_headers,
            json={
                "test_suite_id": suite.id,
                "name": "Test Case",
                "test_type": "invalid_type",
            },
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_list_test_cases(self, client: AsyncClient, admin_token_headers: dict, db_session: AsyncSession, test_company):
        """Test listing test cases."""
        suite = TestSuite(name="Test Suite", company_id=test_company.id, created_by_id=1)
        db_session.add(suite)
        await db_session.commit()
        await db_session.refresh(suite)

        # Create test cases
        case1 = TestCase(test_suite_id=suite.id, name="Case 1", test_type="unit", priority=TestPriority.HIGH)
        case2 = TestCase(test_suite_id=suite.id, name="Case 2", test_type="integration", priority=TestPriority.MEDIUM)
        db_session.add_all([case1, case2])
        await db_session.commit()

        response = await client.get(
            f"/api/v1/testing/cases?test_suite_id={suite.id}",
            headers=admin_token_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert data["total"] >= 2

    @pytest.mark.asyncio
    async def test_list_test_cases_with_filters(self, client: AsyncClient, admin_token_headers: dict, db_session: AsyncSession, test_company):
        """Test listing test cases with filters."""
        suite = TestSuite(name="Test Suite", company_id=test_company.id, created_by_id=1)
        db_session.add(suite)
        await db_session.commit()
        await db_session.refresh(suite)

        # Create test cases
        case1 = TestCase(test_suite_id=suite.id, name="High Priority", test_type="unit", priority=TestPriority.HIGH)
        case2 = TestCase(test_suite_id=suite.id, name="Low Priority", test_type="unit", priority=TestPriority.LOW)
        db_session.add_all([case1, case2])
        await db_session.commit()

        # Filter by priority
        response = await client.get(
            f"/api/v1/testing/cases?test_suite_id={suite.id}&priority=high",
            headers=admin_token_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert all(case["priority"] == "high" for case in data["items"])

    @pytest.mark.asyncio
    async def test_get_test_case(self, client: AsyncClient, admin_token_headers: dict, db_session: AsyncSession, test_company):
        """Test getting a specific test case."""
        suite = TestSuite(name="Test Suite", company_id=test_company.id, created_by_id=1)
        db_session.add(suite)
        await db_session.commit()
        await db_session.refresh(suite)

        case = TestCase(test_suite_id=suite.id, name="Test Case", test_type="unit")
        db_session.add(case)
        await db_session.commit()
        await db_session.refresh(case)

        response = await client.get(
            f"/api/v1/testing/cases/{case.id}",
            headers=admin_token_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Test Case"
        assert data["id"] == case.id

    @pytest.mark.asyncio
    async def test_update_test_case(self, client: AsyncClient, admin_token_headers: dict, db_session: AsyncSession, test_company):
        """Test updating a test case."""
        suite = TestSuite(name="Test Suite", company_id=test_company.id, created_by_id=1)
        db_session.add(suite)
        await db_session.commit()
        await db_session.refresh(suite)

        case = TestCase(test_suite_id=suite.id, name="Old Name", test_type="unit")
        db_session.add(case)
        await db_session.commit()
        await db_session.refresh(case)

        response = await client.put(
            f"/api/v1/testing/cases/{case.id}",
            headers=admin_token_headers,
            json={
                "name": "New Name",
                "priority": "critical",
                "timeout": 60,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "New Name"
        assert data["priority"] == "critical"
        assert data["timeout"] == 60

    @pytest.mark.asyncio
    async def test_delete_test_case(self, client: AsyncClient, admin_token_headers: dict, db_session: AsyncSession, test_company):
        """Test deleting a test case."""
        suite = TestSuite(name="Test Suite", company_id=test_company.id, created_by_id=1)
        db_session.add(suite)
        await db_session.commit()
        await db_session.refresh(suite)

        case = TestCase(test_suite_id=suite.id, name="To Delete", test_type="unit")
        db_session.add(case)
        await db_session.commit()
        await db_session.refresh(case)

        response = await client.delete(
            f"/api/v1/testing/cases/{case.id}",
            headers=admin_token_headers,
        )
        assert response.status_code == 204


class TestTestRuns:
    """Test test run endpoints."""

    @pytest.mark.asyncio
    async def test_create_test_run(self, client: AsyncClient, admin_token_headers: dict, db_session: AsyncSession, test_company):
        """Test creating a test run."""
        suite = TestSuite(name="Test Suite", company_id=test_company.id, created_by_id=1)
        db_session.add(suite)
        await db_session.commit()
        await db_session.refresh(suite)

        response = await client.post(
            "/api/v1/testing/runs",
            headers=admin_token_headers,
            json={
                "test_suite_id": suite.id,
                "environment": "staging",
                "branch": "main",
                "commit_hash": "abc123",
                "triggered_by": "manual",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["test_suite_id"] == suite.id
        assert data["status"] == "running"
        assert data["environment"] == "staging"
        assert data["branch"] == "main"
        assert data["commit_hash"] == "abc123"

    @pytest.mark.asyncio
    async def test_list_test_runs(self, client: AsyncClient, admin_token_headers: dict, db_session: AsyncSession, test_company):
        """Test listing test runs."""
        suite = TestSuite(name="Test Suite", company_id=test_company.id, created_by_id=1)
        db_session.add(suite)
        await db_session.commit()
        await db_session.refresh(suite)

        # Create test runs
        run1 = TestRun(test_suite_id=suite.id, status=TestStatus.PASSED, environment="development")
        run2 = TestRun(test_suite_id=suite.id, status=TestStatus.FAILED, environment="staging")
        db_session.add_all([run1, run2])
        await db_session.commit()

        response = await client.get(
            "/api/v1/testing/runs",
            headers=admin_token_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data

    @pytest.mark.asyncio
    async def test_list_test_runs_with_filters(self, client: AsyncClient, admin_token_headers: dict, db_session: AsyncSession, test_company):
        """Test listing test runs with filters."""
        suite = TestSuite(name="Test Suite", company_id=test_company.id, created_by_id=1)
        db_session.add(suite)
        await db_session.commit()
        await db_session.refresh(suite)

        # Create test runs
        run1 = TestRun(test_suite_id=suite.id, status=TestStatus.PASSED, environment="development")
        run2 = TestRun(test_suite_id=suite.id, status=TestStatus.FAILED, environment="staging")
        db_session.add_all([run1, run2])
        await db_session.commit()

        # Filter by environment
        response = await client.get(
            "/api/v1/testing/runs",
            headers=admin_token_headers,
            params={"environment": "development"},
        )
        assert response.status_code == 200
        data = response.json()
        assert all(run["environment"] == "development" for run in data["items"])

    @pytest.mark.asyncio
    async def test_get_test_run(self, client: AsyncClient, admin_token_headers: dict, db_session: AsyncSession, test_company):
        """Test getting a specific test run."""
        suite = TestSuite(name="Test Suite", company_id=test_company.id, created_by_id=1)
        db_session.add(suite)
        await db_session.commit()
        await db_session.refresh(suite)

        run = TestRun(test_suite_id=suite.id, status=TestStatus.RUNNING)
        db_session.add(run)
        await db_session.commit()
        await db_session.refresh(run)

        response = await client.get(
            f"/api/v1/testing/runs/{run.id}",
            headers=admin_token_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == run.id
        assert data["status"] == "running"

    @pytest.mark.asyncio
    async def test_complete_test_run(self, client: AsyncClient, admin_token_headers: dict, db_session: AsyncSession, test_company):
        """Test completing a test run."""
        suite = TestSuite(name="Test Suite", company_id=test_company.id, created_by_id=1)
        db_session.add(suite)
        await db_session.commit()
        await db_session.refresh(suite)

        run = TestRun(test_suite_id=suite.id, status=TestStatus.RUNNING)
        db_session.add(run)
        await db_session.commit()
        await db_session.refresh(run)

        response = await client.post(
            f"/api/v1/testing/runs/{run.id}/complete",
            headers=admin_token_headers,
            json={
                "status": "passed",
                "total_tests": 10,
                "passed_tests": 8,
                "failed_tests": 2,
                "skipped_tests": 0,
                "error_tests": 0,
                "duration": 45.5,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "passed"
        assert data["total_tests"] == 10
        assert data["passed_tests"] == 8
        assert data["failed_tests"] == 2
        assert data["success_rate"] == 80.0
        assert data["completed_at"] is not None


class TestTestResults:
    """Test test result endpoints."""

    @pytest.mark.asyncio
    async def test_create_test_result(self, client: AsyncClient, admin_token_headers: dict, db_session: AsyncSession, test_company):
        """Test creating a test result."""
        suite = TestSuite(name="Test Suite", company_id=test_company.id, created_by_id=1)
        db_session.add(suite)
        await db_session.commit()
        await db_session.refresh(suite)

        case = TestCase(test_suite_id=suite.id, name="Test Case", test_type="unit")
        db_session.add(case)
        await db_session.commit()
        await db_session.refresh(case)

        run = TestRun(test_suite_id=suite.id, status=TestStatus.RUNNING)
        db_session.add(run)
        await db_session.commit()
        await db_session.refresh(run)

        response = await client.post(
            "/api/v1/testing/results",
            headers=admin_token_headers,
            json={
                "test_run_id": run.id,
                "test_case_id": case.id,
                "status": "passed",
                "output": "Test passed successfully",
                "duration": 2.5,
                "request_url": "http://example.com/api/test",
                "request_method": "GET",
                "response_status": 200,
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "passed"
        assert data["test_run_id"] == run.id
        assert data["test_case_id"] == case.id
        assert data["duration"] == 2.5

    @pytest.mark.asyncio
    async def test_list_test_results(self, client: AsyncClient, admin_token_headers: dict, db_session: AsyncSession, test_company):
        """Test listing test results."""
        suite = TestSuite(name="Test Suite", company_id=test_company.id, created_by_id=1)
        db_session.add(suite)
        await db_session.commit()
        await db_session.refresh(suite)

        case = TestCase(test_suite_id=suite.id, name="Test Case", test_type="unit")
        db_session.add(case)
        await db_session.commit()
        await db_session.refresh(case)

        run = TestRun(test_suite_id=suite.id, status=TestStatus.RUNNING)
        db_session.add(run)
        await db_session.commit()
        await db_session.refresh(run)

        # Create test results
        result1 = TestResult(test_run_id=run.id, test_case_id=case.id, status=TestStatus.PASSED)
        result2 = TestResult(test_run_id=run.id, test_case_id=case.id, status=TestStatus.FAILED)
        db_session.add_all([result1, result2])
        await db_session.commit()

        response = await client.get(
            f"/api/v1/testing/results?test_run_id={run.id}",
            headers=admin_token_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert data["total"] >= 2


class TestStatistics:
    """Test statistics endpoints."""

    @pytest.mark.asyncio
    async def test_get_test_statistics(self, client: AsyncClient, admin_token_headers: dict, db_session: AsyncSession, test_company):
        """Test getting test statistics."""
        # Create test data
        suite = TestSuite(name="Test Suite", company_id=test_company.id, created_by_id=1)
        db_session.add(suite)
        await db_session.commit()
        await db_session.refresh(suite)

        case = TestCase(test_suite_id=suite.id, name="Test Case", test_type="unit")
        db_session.add(case)
        await db_session.commit()
        await db_session.refresh(case)

        run = TestRun(test_suite_id=suite.id, status=TestStatus.PASSED, total_tests=10, passed_tests=8, failed_tests=2)
        db_session.add(run)
        await db_session.commit()
        await db_session.refresh(run)

        result = TestResult(test_run_id=run.id, test_case_id=case.id, status=TestStatus.PASSED)
        db_session.add(result)
        await db_session.commit()

        response = await client.get(
            "/api/v1/testing/statistics",
            headers=admin_token_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "total_suites" in data
        assert "total_cases" in data
        assert "total_runs" in data
        assert "total_results" in data
        assert "success_rate" in data
        assert "most_failed_tests" in data
        assert "recent_runs" in data


class TestValidation:
    """Test validation rules."""

    @pytest.mark.asyncio
    async def test_test_suite_name_required(self, client: AsyncClient, admin_token_headers: dict):
        """Test that test suite name is required."""
        response = await client.post(
            "/api/v1/testing/suites",
            headers=admin_token_headers,
            json={},
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_test_case_name_too_long(self, client: AsyncClient, admin_token_headers: dict, db_session: AsyncSession, test_company):
        """Test that test case name cannot exceed 255 characters."""
        suite = TestSuite(name="Test Suite", company_id=test_company.id, created_by_id=1)
        db_session.add(suite)
        await db_session.commit()
        await db_session.refresh(suite)

        response = await client.post(
            "/api/v1/testing/cases",
            headers=admin_token_headers,
            json={
                "test_suite_id": suite.id,
                "name": "a" * 256,  # Too long
                "test_type": "unit",
            },
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_test_case_timeout_range(self, client: AsyncClient, admin_token_headers: dict, db_session: AsyncSession, test_company):
        """Test that timeout must be between 1 and 300 seconds."""
        suite = TestSuite(name="Test Suite", company_id=test_company.id, created_by_id=1)
        db_session.add(suite)
        await db_session.commit()
        await db_session.refresh(suite)

        # Test minimum timeout
        response = await client.post(
            "/api/v1/testing/cases",
            headers=admin_token_headers,
            json={
                "test_suite_id": suite.id,
                "name": "Test Case",
                "test_type": "unit",
                "timeout": 0,
            },
        )
        assert response.status_code == 422

        # Test maximum timeout
        response = await client.post(
            "/api/v1/testing/cases",
            headers=admin_token_headers,
            json={
                "test_suite_id": suite.id,
                "name": "Test Case",
                "test_type": "unit",
                "timeout": 301,
            },
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_test_case_retry_count_range(self, client: AsyncClient, admin_token_headers: dict, db_session: AsyncSession, test_company):
        """Test that retry count must be between 0 and 10."""
        suite = TestSuite(name="Test Suite", company_id=test_company.id, created_by_id=1)
        db_session.add(suite)
        await db_session.commit()
        await db_session.refresh(suite)

        # Test maximum retry count
        response = await client.post(
            "/api/v1/testing/cases",
            headers=admin_token_headers,
            json={
                "test_suite_id": suite.id,
                "name": "Test Case",
                "test_type": "unit",
                "retry_count": 11,
            },
        )
        assert response.status_code == 422


class TestIntegration:
    """Integration tests for test framework."""

    @pytest.mark.asyncio
    async def test_full_test_lifecycle(self, client: AsyncClient, admin_token_headers: dict, db_session: AsyncSession, test_company):
        """Test complete test lifecycle: create suite, case, run, result."""
        # 1. Create test suite
        suite_response = await client.post(
            "/api/v1/testing/suites",
            headers=admin_token_headers,
            json={
                "name": "Integration Test Suite",
                "description": "Full lifecycle test",
                "company_id": test_company.id,
            },
        )
        assert suite_response.status_code == 201
        suite_id = suite_response.json()["id"]

        # 2. Create test case
        case_response = await client.post(
            "/api/v1/testing/cases",
            headers=admin_token_headers,
            json={
                "test_suite_id": suite_id,
                "name": "Integration Test Case",
                "test_type": "integration",
                "priority": "high",
                "endpoint": "/api/test",
                "method": "POST",
            },
        )
        assert case_response.status_code == 201
        case_id = case_response.json()["id"]

        # 3. Create test run
        run_response = await client.post(
            "/api/v1/testing/runs",
            headers=admin_token_headers,
            json={
                "test_suite_id": suite_id,
                "environment": "development",
                "triggered_by": "manual",
            },
        )
        assert run_response.status_code == 201
        run_id = run_response.json()["id"]

        # 4. Create test result
        result_response = await client.post(
            "/api/v1/testing/results",
            headers=admin_token_headers,
            json={
                "test_run_id": run_id,
                "test_case_id": case_id,
                "status": "passed",
                "duration": 1.5,
            },
        )
        assert result_response.status_code == 201

        # 5. Complete test run
        complete_response = await client.post(
            f"/api/v1/testing/runs/{run_id}/complete",
            headers=admin_token_headers,
            json={
                "status": "passed",
                "total_tests": 1,
                "passed_tests": 1,
                "failed_tests": 0,
                "skipped_tests": 0,
                "error_tests": 0,
                "duration": 1.5,
            },
        )
        assert complete_response.status_code == 200
        assert complete_response.json()["status"] == "passed"

        # 6. Verify statistics updated
        stats_response = await client.get(
            "/api/v1/testing/statistics",
            headers=admin_token_headers,
        )
        assert stats_response.status_code == 200
        stats = stats_response.json()
        assert stats["total_suites"] >= 1
        assert stats["total_cases"] >= 1
        assert stats["total_runs"] >= 1
        assert stats["total_results"] >= 1

    @pytest.mark.asyncio
    async def test_cascade_delete_suite(self, client: AsyncClient, admin_token_headers: dict, db_session: AsyncSession, test_company):
        """Test that deleting a suite cascades to cases."""
        # Create suite
        suite_response = await client.post(
            "/api/v1/testing/suites",
            headers=admin_token_headers,
            json={
                "name": "To Delete",
                "company_id": test_company.id,
            },
        )
        suite_id = suite_response.json()["id"]

        # Create case
        case_response = await client.post(
            "/api/v1/testing/cases",
            headers=admin_token_headers,
            json={
                "test_suite_id": suite_id,
                "name": "Test Case",
                "test_type": "unit",
            },
        )
        case_id = case_response.json()["id"]

        # Delete suite
        await client.delete(
            f"/api/v1/testing/suites/{suite_id}",
            headers=admin_token_headers,
        )

        # Verify case is also deleted
        case_check = await client.get(
            f"/api/v1/testing/cases/{case_id}",
            headers=admin_token_headers,
        )
        assert case_check.status_code == 404
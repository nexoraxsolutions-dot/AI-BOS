import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.department import Department
from app.models.company import Company
from app.models.user import User
from app.schemas.department import DepartmentCreate, DepartmentUpdate
from app.core.security import get_password_hash


@pytest.mark.asyncio
async def test_create_department(client: AsyncClient, test_company: Company, admin_user: User):
    """Test creating a department."""
    payload = {
        "name": "Engineering",
        "description": "Software engineering department",
        "company_id": test_company.id,
        "budget": "$100,000",
        "location": "Building A",
        "is_active": True,
    }
    # Get token for admin user
    from app.core.security import create_access_token
    token = create_access_token(data={"sub": admin_user.email})
    headers = {"Authorization": f"Bearer {token}"}
    
    response = await client.post(
        "/api/v1/departments/",
        json=payload,
        headers=headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Engineering"
    assert data["company_id"] == test_company.id
    assert data["budget"] == "$100,000"


@pytest.mark.asyncio
async def test_create_department_unauthorized(client: AsyncClient, test_company: Company, test_user: User):
    """Test that regular users cannot create departments."""
    payload = {
        "name": "Engineering",
        "company_id": test_company.id,
    }
    from app.core.security import create_access_token
    token = create_access_token(data={"sub": test_user.email})
    headers = {"Authorization": f"Bearer {token}"}
    
    response = await client.post(
        "/api/v1/departments/",
        json=payload,
        headers=headers,
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_list_departments(client: AsyncClient, test_department: Department, test_user: User):
    """Test listing departments."""
    from app.core.security import create_access_token
    token = create_access_token(data={"sub": test_user.email})
    headers = {"Authorization": f"Bearer {token}"}
    
    response = await client.get(
        "/api/v1/departments/",
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert data["total"] >= 1


@pytest.mark.asyncio
async def test_get_department(client: AsyncClient, test_department: Department, test_user: User):
    """Test getting a specific department."""
    from app.core.security import create_access_token
    token = create_access_token(data={"sub": test_user.email})
    headers = {"Authorization": f"Bearer {token}"}
    
    response = await client.get(
        f"/api/v1/departments/{test_department.id}",
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == test_department.id
    assert data["name"] == test_department.name


@pytest.mark.asyncio
async def test_get_department_not_found(client: AsyncClient, test_user: User):
    """Test getting a non-existent department."""
    from app.core.security import create_access_token
    token = create_access_token(data={"sub": test_user.email})
    headers = {"Authorization": f"Bearer {token}"}
    
    response = await client.get(
        "/api/v1/departments/99999",
        headers=headers,
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_department(client: AsyncClient, test_department: Department, admin_user: User):
    """Test updating a department."""
    payload = {
        "name": "Updated Engineering",
        "budget": "$150,000",
    }
    from app.core.security import create_access_token
    token = create_access_token(data={"sub": admin_user.email})
    headers = {"Authorization": f"Bearer {token}"}
    
    response = await client.put(
        f"/api/v1/departments/{test_department.id}",
        json=payload,
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Engineering"
    assert data["budget"] == "$150,000"


@pytest.mark.asyncio
async def test_delete_department(client: AsyncClient, test_company: Company, admin_user: User, test_user: User):
    """Test deleting a department."""
    from app.core.security import create_access_token
    admin_token = create_access_token(data={"sub": admin_user.email})
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    user_token = create_access_token(data={"sub": test_user.email})
    user_headers = {"Authorization": f"Bearer {user_token}"}
    
    # Create a department to delete
    payload = {
        "name": "To Delete",
        "company_id": test_company.id,
    }
    create_response = await client.post(
        "/api/v1/departments/",
        json=payload,
        headers=admin_headers,
    )
    assert create_response.status_code == 201
    department_id = create_response.json()["id"]

    # Delete the department
    response = await client.delete(
        f"/api/v1/departments/{department_id}",
        headers=admin_headers,
    )
    assert response.status_code == 204

    # Verify it's deleted
    get_response = await client.get(
        f"/api/v1/departments/{department_id}",
        headers=user_headers,
    )
    assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_get_department_stats(client: AsyncClient, test_user: User):
    """Test getting department statistics."""
    from app.core.security import create_access_token
    token = create_access_token(data={"sub": test_user.email})
    headers = {"Authorization": f"Bearer {token}"}
    
    response = await client.get(
        "/api/v1/departments/stats",
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert "total_departments" in data
    assert "active_departments" in data
    assert "inactive_departments" in data


@pytest.mark.asyncio
async def test_filter_departments_by_company(client: AsyncClient, test_company: Company, test_department: Department, test_user: User):
    """Test filtering departments by company."""
    from app.core.security import create_access_token
    token = create_access_token(data={"sub": test_user.email})
    headers = {"Authorization": f"Bearer {token}"}
    
    response = await client.get(
        f"/api/v1/departments/?company_id={test_company.id}",
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    for dept in data["items"]:
        assert dept["company_id"] == test_company.id


@pytest.mark.asyncio
async def test_search_departments(client: AsyncClient, test_department: Department, test_user: User):
    """Test searching departments."""
    from app.core.security import create_access_token
    token = create_access_token(data={"sub": test_user.email})
    headers = {"Authorization": f"Bearer {token}"}
    
    response = await client.get(
        f"/api/v1/departments/?search={test_department.name}",
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    assert any(dept["name"] == test_department.name for dept in data["items"])


@pytest.mark.asyncio
async def test_department_validation(client: AsyncClient, test_company: Company, admin_user: User):
    """Test department validation."""
    from app.core.security import create_access_token
    token = create_access_token(data={"sub": admin_user.email})
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test short name
    payload = {
        "name": "A",
        "company_id": test_company.id,
    }
    response = await client.post(
        "/api/v1/departments/",
        json=payload,
        headers=headers,
    )
    assert response.status_code == 422

    # Test invalid budget format
    payload = {
        "name": "Valid Department",
        "company_id": test_company.id,
        "budget": "invalid",
    }
    response = await client.post(
        "/api/v1/departments/",
        json=payload,
        headers=headers,
    )
    assert response.status_code == 422

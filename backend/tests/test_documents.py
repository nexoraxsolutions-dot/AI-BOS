import pytest
from httpx import AsyncClient

from app.models.company import Company
from app.models.user import User
from app.core.security import create_access_token


def _admin_headers(admin_user: User) -> dict:
    token = create_access_token(data={"sub": admin_user.email})
    return {"Authorization": f"Bearer {token}"}


def _user_headers(test_user: User) -> dict:
    token = create_access_token(data={"sub": test_user.email})
    return {"Authorization": f"Bearer {token}"}


def _payload(title: str = "Getting Started Guide", **overrides) -> dict:
    data = {
        "title": title,
        "slug": "getting-started-guide",
        "summary": "A guide to get started.",
        "content": "# Getting Started\n\nDetailed body content.",
        "category": "general",
        "tags": "guide,onboarding",
        "status": "draft",
    }
    data.update(overrides)
    return data


@pytest.mark.asyncio
async def test_create_document(client: AsyncClient, admin_user: User):
    """Test creating a document as superuser."""
    response = await client.post(
        "/api/v1/documents/",
        json=_payload(),
        headers=_admin_headers(admin_user),
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Getting Started Guide"
    assert data["status"] == "draft"
    assert data["version"] == 1
    assert data["author_id"] == admin_user.id


@pytest.mark.asyncio
async def test_create_document_unauthorized(client: AsyncClient, test_user: User):
    """Test that regular users cannot create documents."""
    response = await client.post(
        "/api/v1/documents/",
        json=_payload(),
        headers=_user_headers(test_user),
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_create_document_validation(client: AsyncClient, admin_user: User):
    """Test document validation (short title, invalid status, invalid slug)."""
    headers = _admin_headers(admin_user)

    # Short title
    response = await client.post("/api/v1/documents/", json=_payload(title="AB"), headers=headers)
    assert response.status_code == 422

    # Invalid status
    response = await client.post(
        "/api/v1/documents/", json=_payload(status="invalid-status"), headers=headers
    )
    assert response.status_code == 422

    # Invalid slug (spaces/uppercase)
    response = await client.post(
        "/api/v1/documents/", json=_payload(slug="Invalid Slug!"), headers=headers
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_list_documents(client: AsyncClient, admin_user: User, test_company: Company):
    """Test listing documents."""
    headers = _admin_headers(admin_user)
    await client.post(
        "/api/v1/documents/",
        json=_payload(title="API Reference", company_id=test_company.id),
        headers=headers,
    )

    response = await client.get(
        "/api/v1/documents/",
        headers=_user_headers(admin_user),
    )
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert data["total"] >= 1


@pytest.mark.asyncio
async def test_get_document(client: AsyncClient, admin_user: User):
    """Test getting a specific document."""
    create_resp = await client.post(
        "/api/v1/documents/",
        json=_payload(),
        headers=_admin_headers(admin_user),
    )
    doc_id = create_resp.json()["id"]

    response = await client.get(
        f"/api/v1/documents/{doc_id}",
        headers=_user_headers(admin_user),
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == doc_id
    assert data["author_name"] == admin_user.full_name


@pytest.mark.asyncio
async def test_get_document_not_found(client: AsyncClient, test_user: User):
    """Test getting a non-existent document."""
    response = await client.get(
        "/api/v1/documents/99999",
        headers=_user_headers(test_user),
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_document_increments_version(client: AsyncClient, admin_user: User):
    """Test updating a document bumps its version."""
    create_resp = await client.post(
        "/api/v1/documents/",
        json=_payload(),
        headers=_admin_headers(admin_user),
    )
    doc_id = create_resp.json()["id"]
    assert create_resp.json()["version"] == 1

    response = await client.put(
        f"/api/v1/documents/{doc_id}",
        json={"title": "Updated Guide Title"},
        headers=_admin_headers(admin_user),
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Updated Guide Title"
    assert data["version"] == 2


@pytest.mark.asyncio
async def test_update_document_unauthorized(client: AsyncClient, admin_user: User, test_user: User):
    """Test that regular users cannot update documents."""
    create_resp = await client.post(
        "/api/v1/documents/",
        json=_payload(),
        headers=_admin_headers(admin_user),
    )
    doc_id = create_resp.json()["id"]

    response = await client.put(
        f"/api/v1/documents/{doc_id}",
        json={"title": "New Title"},
        headers=_user_headers(test_user),
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_publish_document(client: AsyncClient, admin_user: User):
    """Test publishing a document changes its status."""
    create_resp = await client.post(
        "/api/v1/documents/",
        json=_payload(),
        headers=_admin_headers(admin_user),
    )
    doc_id = create_resp.json()["id"]

    response = await client.post(
        f"/api/v1/documents/{doc_id}/publish",
        headers=_admin_headers(admin_user),
    )
    assert response.status_code == 200
    assert response.json()["status"] == "published"


@pytest.mark.asyncio
async def test_delete_document(client: AsyncClient, admin_user: User, test_user: User):
    """Test deleting a document."""
    create_resp = await client.post(
        "/api/v1/documents/",
        json=_payload(),
        headers=_admin_headers(admin_user),
    )
    doc_id = create_resp.json()["id"]

    delete_resp = await client.delete(
        f"/api/v1/documents/{doc_id}",
        headers=_admin_headers(admin_user),
    )
    assert delete_resp.status_code == 204

    get_resp = await client.get(
        f"/api/v1/documents/{doc_id}",
        headers=_user_headers(test_user),
    )
    assert get_resp.status_code == 404


@pytest.mark.asyncio
async def test_get_document_stats(client: AsyncClient, admin_user: User):
    """Test getting document statistics."""
    headers = _admin_headers(admin_user)
    await client.post("/api/v1/documents/", json=_payload(), headers=headers)
    await client.post(
        "/api/v1/documents/",
        json=_payload(title="Published Doc", status="published"),
        headers=headers,
    )

    response = await client.get(
        "/api/v1/documents/stats",
        headers=_user_headers(admin_user),
    )
    assert response.status_code == 200
    data = response.json()
    assert "total_documents" in data
    assert "published_documents" in data
    assert "draft_documents" in data
    assert data["total_documents"] >= 2


@pytest.mark.asyncio
async def test_search_documents(client: AsyncClient, admin_user: User):
    """Test searching documents."""
    headers = _admin_headers(admin_user)
    await client.post(
        "/api/v1/documents/",
        json=_payload(title="Deployment Runbook"),
        headers=headers,
    )

    response = await client.get(
        "/api/v1/documents/?search=deployment",
        headers=_user_headers(admin_user),
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    assert any(doc["title"] == "Deployment Runbook" for doc in data["items"])


@pytest.mark.asyncio
async def test_filter_documents_by_status(client: AsyncClient, admin_user: User):
    """Test filtering documents by status."""
    headers = _admin_headers(admin_user)
    await client.post(
        "/api/v1/documents/",
        json=_payload(title="Archived Old Doc", status="archived"),
        headers=headers,
    )

    response = await client.get(
        "/api/v1/documents/?status=archived",
        headers=_user_headers(admin_user),
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    for doc in data["items"]:
        assert doc["status"] == "archived"

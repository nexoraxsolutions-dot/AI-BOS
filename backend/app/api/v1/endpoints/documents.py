from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.request import get_client_ip, get_user_agent
from app.core.security import get_current_active_user, require_superuser
from app.db.dependencies import get_async_session
from app.schemas import document as document_schema
from app.services import document as document_service
from app.services.audit_log import create_audit_log

router = APIRouter()


@router.post(
    "/",
    response_model=document_schema.DocumentOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_document(
    request: Request,
    payload: document_schema.DocumentCreate,
    db: AsyncSession = Depends(get_async_session),
    current_user=Depends(require_superuser),
):
    """Create a new documentation article (superuser only)."""
    document = await document_service.create_document(db, payload, author_id=current_user.id)
    await create_audit_log(
        db,
        action="create",
        resource_type="document",
        resource_id=document.id,
        user_id=current_user.id,
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request),
        details={"document_title": document.title, "status": document.status, "created_by": current_user.email},
    )
    return document


@router.get(
    "/",
    response_model=document_schema.DocumentListResponse,
)
async def list_documents(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=100, description="Number of records to return"),
    search: Optional[str] = Query(None, description="Search by title, summary, content, category, or tags"),
    category: Optional[str] = Query(None, description="Filter by category"),
    status: Optional[str] = Query(None, description="Filter by status (draft, published, archived)"),
    company_id: Optional[int] = Query(None, description="Filter by company ID"),
    author_id: Optional[int] = Query(None, description="Filter by author ID"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    sort_by: str = Query("title", description="Sort field"),
    sort_order: str = Query("asc", description="Sort order (asc or desc)"),
    db: AsyncSession = Depends(get_async_session),
    current_user=Depends(get_current_active_user),
):
    """List documentation articles with search, filters, and pagination."""
    documents, total = await document_service.get_documents(
        db,
        skip=skip,
        limit=limit,
        search=search,
        category=category,
        status=status,
        company_id=company_id,
        author_id=author_id,
        is_active=is_active,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    return document_schema.DocumentListResponse(
        items=documents,
        total=total,
        page=(skip // limit) + 1,
        page_size=limit,
    )


@router.get(
    "/stats",
    response_model=document_schema.DocumentStats,
)
async def get_document_stats(
    db: AsyncSession = Depends(get_async_session),
    current_user=Depends(get_current_active_user),
):
    """Get documentation statistics (counts by status/category, company distribution)."""
    return await document_service.get_document_stats(db)


@router.get(
    "/{document_id}",
    response_model=document_schema.DocumentOut,
)
async def get_document(
    document_id: int,
    db: AsyncSession = Depends(get_async_session),
    current_user=Depends(get_current_active_user),
):
    """Get a single documentation article by ID."""
    document = await document_service.get_document_with_details(db, document_id)
    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    return document


@router.put(
    "/{document_id}",
    response_model=document_schema.DocumentOut,
)
async def update_document(
    request: Request,
    document_id: int,
    payload: document_schema.DocumentUpdate,
    db: AsyncSession = Depends(get_async_session),
    current_user=Depends(require_superuser),
):
    """Update a documentation article and bump its version (superuser only)."""
    document = await document_service.update_document(db, document_id, payload)
    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    await create_audit_log(
        db,
        action="update",
        resource_type="document",
        resource_id=document_id,
        user_id=current_user.id,
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request),
        details={
            "document_title": document.title,
            "version": document.version,
            "updated_by": current_user.email,
            "updated_fields": payload.model_dump(exclude_none=True),
        },
    )
    return document


@router.delete(
    "/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_document(
    request: Request,
    document_id: int,
    db: AsyncSession = Depends(get_async_session),
    current_user=Depends(require_superuser),
):
    """Delete a documentation article permanently (superuser only)."""
    document_to_delete = await document_service.get_document(db, document_id)
    deleted = await document_service.delete_document(db, document_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    await create_audit_log(
        db,
        action="delete",
        resource_type="document",
        resource_id=document_id,
        user_id=current_user.id,
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request),
        details={
            "document_title": document_to_delete.title if document_to_delete else "unknown",
            "deleted_by": current_user.email,
        },
    )
    return None


@router.post(
    "/{document_id}/publish",
    response_model=document_schema.DocumentOut,
)
async def publish_document(
    request: Request,
    document_id: int,
    db: AsyncSession = Depends(get_async_session),
    current_user=Depends(require_superuser),
):
    """Publish a documentation article (superuser only)."""
    document = await document_service.publish_document(db, document_id)
    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    await create_audit_log(
        db,
        action="publish",
        resource_type="document",
        resource_id=document_id,
        user_id=current_user.id,
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request),
        details={"document_title": document.title, "published_by": current_user.email},
    )
    return document

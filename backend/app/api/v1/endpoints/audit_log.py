from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app.db.dependencies import get_async_session
from app.schemas import audit_log as audit_log_schema
from app.services import audit_log as audit_log_service
from app.core.security import get_current_active_user, require_superuser

router = APIRouter()


@router.get("/", response_model=audit_log_schema.AuditLogListResponse)
async def list_audit_logs(
    skip: int = 0,
    limit: int = Query(default=50, le=100),
    action: Optional[str] = Query(None, description="Filter by action"),
    resource_type: Optional[str] = Query(None, description="Filter by resource type"),
    user_id: Optional[int] = Query(None, description="Filter by user ID"),
    db: AsyncSession = Depends(get_async_session),
    current_user=Depends(require_superuser),
):
    """List audit logs with optional filtering. Superuser only."""
    logs = await audit_log_service.get_audit_logs(
        db, skip=skip, limit=limit, action=action, resource_type=resource_type, user_id=user_id
    )
    total = await audit_log_service.count_audit_logs(
        db, action=action, resource_type=resource_type, user_id=user_id
    )
    page = skip // limit + 1 if limit > 0 else 1
    return audit_log_schema.AuditLogListResponse(
        items=logs,
        total=total,
        page=page,
        page_size=limit,
    )


@router.get("/{log_id}", response_model=audit_log_schema.AuditLogOut)
async def get_audit_log(
    log_id: int,
    db: AsyncSession = Depends(get_async_session),
    current_user=Depends(require_superuser),
):
    """Get a specific audit log entry. Superuser only."""
    log = await audit_log_service.get_audit_log(db, log_id)
    if not log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audit log not found",
        )
    return log


@router.get("/my-logs/", response_model=audit_log_schema.AuditLogListResponse)
async def get_my_audit_logs(
    skip: int = 0,
    limit: int = Query(default=50, le=100),
    action: Optional[str] = Query(None, description="Filter by action"),
    resource_type: Optional[str] = Query(None, description="Filter by resource type"),
    db: AsyncSession = Depends(get_async_session),
    current_user=Depends(get_current_active_user),
):
    """Get audit logs for the current user."""
    logs = await audit_log_service.get_audit_logs(
        db, skip=skip, limit=limit, action=action, resource_type=resource_type, user_id=current_user.id
    )
    total = await audit_log_service.count_audit_logs(
        db, action=action, resource_type=resource_type, user_id=current_user.id
    )
    page = skip // limit + 1 if limit > 0 else 1
    return audit_log_schema.AuditLogListResponse(
        items=logs,
        total=total,
        page=page,
        page_size=limit,
    )

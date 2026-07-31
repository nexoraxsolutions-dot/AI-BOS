from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import security
from app.core.request import get_client_ip, get_user_agent
from app.db.dependencies import get_async_session
from app.schemas import session as session_schema
from app.services import session as session_service
from app.services.audit_log import create_audit_log

router = APIRouter(tags=["sessions"])


@router.get("/", response_model=session_schema.SessionListResponse)
async def list_sessions(
    request: Request,
    skip: int = 0,
    limit: int = 50,
    include_inactive: bool = False,
    current_user=Depends(security.get_current_active_user),
    db: AsyncSession = Depends(get_async_session),
):
    """List sessions for the current user with pagination."""
    sessions, total = await session_service.get_user_sessions(
        db,
        user_id=current_user.id,
        skip=skip,
        limit=limit,
        include_inactive=include_inactive,
    )
    
    session_outputs = [session_service.session_to_out(s) for s in sessions]
    
    return {
        "items": session_outputs,
        "total": total,
        "page": (skip // limit) + 1 if limit > 0 else 1,
        "page_size": limit,
    }


@router.get("/stats", response_model=dict)
async def get_session_stats(
    request: Request,
    current_user=Depends(security.get_current_active_user),
    db: AsyncSession = Depends(get_async_session),
):
    """Get session statistics for the current user."""
    stats = await session_service.get_session_stats(db, current_user.id)
    return stats


@router.get("/{session_id}", response_model=session_schema.SessionOut)
async def get_session(
    session_id: int,
    request: Request,
    current_user=Depends(security.get_current_active_user),
    db: AsyncSession = Depends(get_async_session),
):
    """Get a specific session by ID (own sessions only)."""
    session = await session_service.get_session_by_id(db, session_id, current_user.id)
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    
    return session_service.session_to_out(session)


@router.post("/terminate", response_model=session_schema.SessionTerminateResponse)
async def terminate_session(
    request: Request,
    terminate_data: session_schema.SessionTerminateRequest,
    current_user=Depends(security.get_current_active_user),
    db: AsyncSession = Depends(get_async_session),
):
    """Terminate a specific session (own sessions only)."""
    session = await session_service.terminate_session(db, terminate_data.session_id, current_user.id)
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    
    # Log session termination
    await create_audit_log(
        db,
        action="session_terminated",
        resource_type="auth",
        resource_id=current_user.id,
        user_id=current_user.id,
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request),
        details={"session_id": terminate_data.session_id},
    )
    
    return {
        "message": "Session terminated successfully",
        "session_id": terminate_data.session_id,
        "terminated": True,
    }


@router.post("/terminate-all", response_model=dict)
async def terminate_all_sessions(
    request: Request,
    current_user=Depends(security.get_current_active_user),
    db: AsyncSession = Depends(get_async_session),
):
    """Terminate all active sessions for the current user."""
    count = await session_service.terminate_user_sessions(db, current_user.id)
    
    # Log mass termination
    await create_audit_log(
        db,
        action="all_sessions_terminated",
        resource_type="auth",
        resource_id=current_user.id,
        user_id=current_user.id,
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request),
        details={"terminated_count": count},
    )
    
    return {
        "message": f"All sessions terminated successfully",
        "terminated_count": count,
    }


@router.post("/cleanup", response_model=session_schema.SessionCleanupResponse)
async def cleanup_sessions(
    request: Request,
    current_user=Depends(security.require_superuser),
    db: AsyncSession = Depends(get_async_session),
):
    """Clean up expired sessions (superuser only)."""
    deleted_count = await session_service.cleanup_expired_sessions(db)
    
    await create_audit_log(
        db,
        action="sessions_cleanup",
        resource_type="auth",
        resource_id=current_user.id,
        user_id=current_user.id,
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request),
        details={"deleted_count": deleted_count},
    )
    
    return {
        "message": f"Cleaned up {deleted_count} expired sessions",
        "deleted_count": deleted_count,
    }
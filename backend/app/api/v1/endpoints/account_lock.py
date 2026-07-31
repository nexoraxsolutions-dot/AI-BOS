from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.db.dependencies import get_async_session
from app.schemas import user as user_schema
from app.services import account_lock as account_lock_service
from app.services.audit_log import create_audit_log
from app.core.security import get_current_active_user, require_superuser
from app.core.request import get_client_ip, get_user_agent

router = APIRouter()


@router.get("/locked", response_model=List[user_schema.UserOut])
async def get_locked_accounts(
    skip: int = 0,
    limit: int = 20,
    db: AsyncSession = Depends(get_async_session),
    current_user=Depends(require_superuser),
):
    """Get list of currently locked accounts (admin only)."""
    service = account_lock_service.AccountLockService(db)
    users = await service.get_locked_accounts(skip=skip, limit=limit)
    return users


@router.post("/{user_id}/unlock", response_model=user_schema.UserOut)
async def unlock_account(
    request: Request,
    user_id: int,
    db: AsyncSession = Depends(get_async_session),
    current_user=Depends(require_superuser),
):
    """Manually unlock a user account (admin only)."""
    service = account_lock_service.AccountLockService(db)
    try:
        user = await service.unlock_account(user_id, request, unlocked_by=current_user.id)
        return user
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.get("/me/status")
async def get_my_account_lock_status(
    db: AsyncSession = Depends(get_async_session),
    current_user=Depends(get_current_active_user),
):
    """Get current user's account lock status."""
    service = account_lock_service.AccountLockService(db)
    is_locked, reason = await service.is_account_locked(current_user)
    
    return {
        "is_locked": is_locked,
        "reason": reason,
        "failed_attempts": current_user.failed_login_attempts,
        "locked_until": current_user.locked_until,
    }
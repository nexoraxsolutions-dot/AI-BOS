from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import security
from app.core.request import get_client_ip, get_user_agent
from app.db.dependencies import get_async_session
from app.schemas import token as token_schema
from app.services import token as token_service
from app.services.audit_log import create_audit_log

router = APIRouter()


@router.get("/", response_model=token_schema.TokenListResponse)
async def list_tokens(
    request: Request,
    skip: int = 0,
    limit: int = 50,
    include_revoked: bool = False,
    current_user=Depends(security.get_current_active_user),
    db: AsyncSession = Depends(get_async_session),
):
    """List tokens for the current user with pagination."""
    tokens, total = await token_service.get_user_tokens(
        db,
        user_id=current_user.id,
        skip=skip,
        limit=limit,
        include_revoked=include_revoked,
    )
    return {
        "items": tokens,
        "total": total,
        "page": (skip // limit) + 1 if limit > 0 else 1,
        "page_size": limit,
    }


@router.get("/all", response_model=token_schema.TokenListResponse)
async def list_all_tokens(
    request: Request,
    skip: int = 0,
    limit: int = 50,
    include_revoked: bool = False,
    current_user=Depends(security.require_superuser),
    db: AsyncSession = Depends(get_async_session),
):
    """List all tokens (superuser only) with pagination."""
    tokens, total = await token_service.get_all_tokens(
        db,
        skip=skip,
        limit=limit,
        include_revoked=include_revoked,
    )
    return {
        "items": tokens,
        "total": total,
        "page": (skip // limit) + 1 if limit > 0 else 1,
        "page_size": limit,
    }


@router.get("/{token_id}", response_model=token_schema.TokenOut)
async def get_token(
    token_id: int,
    request: Request,
    current_user=Depends(security.get_current_active_user),
    db: AsyncSession = Depends(get_async_session),
):
    """Get a specific token by ID (own tokens or superuser)."""
    token = await token_service.get_token_by_id(db, token_id)
    if not token:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Token not found")
    if token.user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to view this token")
    return token


@router.post("/revoke", response_model=token_schema.TokenRevokeResponse)
async def revoke_token(
    request: Request,
    revoke_data: token_schema.TokenRevokeRequest,
    current_user=Depends(security.get_current_active_user),
    db: AsyncSession = Depends(get_async_session),
):
    """Revoke a specific token by ID (own tokens only)."""
    token = await token_service.get_token_by_id(db, revoke_data.token_id)
    if not token:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Token not found")
    if token.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot revoke another user's token")

    result = await token_service.revoke_token(db, revoke_data.token_id, current_user.id)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Token not found or already revoked")

    # Log token revocation
    await create_audit_log(
        db,
        action="token_revoked",
        resource_type="auth",
        resource_id=current_user.id,
        user_id=current_user.id,
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request),
        details={"token_id": revoke_data.token_id, "token_type": token.token_type},
    )

    return {
        "message": "Token revoked successfully",
        "token_id": revoke_data.token_id,
        "revoked": True,
    }


@router.post("/revoke-all", response_model=dict)
async def revoke_all_tokens(
    request: Request,
    current_user=Depends(security.get_current_active_user),
    db: AsyncSession = Depends(get_async_session),
):
    """Revoke all refresh tokens for the current user."""
    count = await token_service.revoke_user_tokens(db, current_user.id, token_type="refresh")

    # Log mass revocation
    await create_audit_log(
        db,
        action="all_tokens_revoked",
        resource_type="auth",
        resource_id=current_user.id,
        user_id=current_user.id,
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request),
        details={"revoked_count": count},
    )

    return {
        "message": f"All refresh tokens revoked successfully",
        "revoked_count": count,
    }


@router.post("/cleanup", response_model=token_schema.TokenCleanupResponse)
async def cleanup_tokens(
    request: Request,
    current_user=Depends(security.require_superuser),
    db: AsyncSession = Depends(get_async_session),
):
    """Clean up expired tokens (superuser only)."""
    deleted_count = await token_service.cleanup_expired_tokens(db)

    await create_audit_log(
        db,
        action="tokens_cleanup",
        resource_type="auth",
        resource_id=current_user.id,
        user_id=current_user.id,
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request),
        details={"deleted_count": deleted_count},
    )

    return {
        "message": f"Cleaned up {deleted_count} expired tokens",
        "deleted_count": deleted_count,
    }
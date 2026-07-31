from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import security
from app.core.request import get_client_ip, get_user_agent
from app.db.dependencies import get_async_session
from app.schemas import api_key as api_key_schema
from app.services import api_key as api_key_service
from app.services.audit_log import create_audit_log

router = APIRouter()


@router.post("/", response_model=api_key_schema.ApiKeyCreateResponse)
async def create_api_key(
    request: Request,
    key_data: api_key_schema.ApiKeyCreate,
    current_user=Depends(security.get_current_active_user),
    db: AsyncSession = Depends(get_async_session),
):
    """Create a new API key. The plain text key is returned only once."""
    api_key, plain_key = await api_key_service.create_api_key(
        db,
        user_id=current_user.id,
        key_name=key_data.key_name,
        permissions=key_data.permissions,
        expires_at=key_data.expires_at,
    )

    # Log API key creation
    await create_audit_log(
        db,
        action="api_key_created",
        resource_type="api_key",
        resource_id=api_key.id,
        user_id=current_user.id,
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request),
        details={"key_name": api_key.key_name},
    )

    return {
        "id": api_key.id,
        "key_name": api_key.key_name,
        "api_key": plain_key,
        "message": "API key created successfully. Save this key securely - it will not be shown again.",
    }


@router.get("/", response_model=api_key_schema.ApiKeyListResponse)
async def list_api_keys(
    request: Request,
    skip: int = 0,
    limit: int = 50,
    include_inactive: bool = False,
    current_user=Depends(security.get_current_active_user),
    db: AsyncSession = Depends(get_async_session),
):
    """List API keys for the current user with pagination."""
    keys, total = await api_key_service.get_user_api_keys(
        db,
        user_id=current_user.id,
        skip=skip,
        limit=limit,
        include_inactive=include_inactive,
    )
    return {
        "items": keys,
        "total": total,
        "page": (skip // limit) + 1 if limit > 0 else 1,
        "page_size": limit,
    }


@router.get("/all", response_model=api_key_schema.ApiKeyListResponse)
async def list_all_api_keys(
    request: Request,
    skip: int = 0,
    limit: int = 50,
    include_inactive: bool = False,
    current_user=Depends(security.require_superuser),
    db: AsyncSession = Depends(get_async_session),
):
    """List all API keys (superuser only) with pagination."""
    keys, total = await api_key_service.get_all_api_keys(
        db,
        skip=skip,
        limit=limit,
        include_inactive=include_inactive,
    )
    return {
        "items": keys,
        "total": total,
        "page": (skip // limit) + 1 if limit > 0 else 1,
        "page_size": limit,
    }


@router.get("/{api_key_id}", response_model=api_key_schema.ApiKeyOut)
async def get_api_key(
    api_key_id: int,
    request: Request,
    current_user=Depends(security.get_current_active_user),
    db: AsyncSession = Depends(get_async_session),
):
    """Get a specific API key by ID (own keys or superuser)."""
    api_key = await api_key_service.get_api_key_by_id(db, api_key_id)
    if not api_key:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="API key not found")
    if api_key.user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to view this API key")
    return api_key


@router.put("/{api_key_id}", response_model=api_key_schema.ApiKeyOut)
async def update_api_key(
    api_key_id: int,
    request: Request,
    key_data: api_key_schema.ApiKeyUpdate,
    current_user=Depends(security.get_current_active_user),
    db: AsyncSession = Depends(get_async_session),
):
    """Update an API key (owner or superuser only)."""
    api_key = await api_key_service.update_api_key(
        db,
        api_key_id=api_key_id,
        user_id=current_user.id,
        data=key_data,
    )
    if not api_key:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="API key not found or not authorized")

    # Log API key update
    await create_audit_log(
        db,
        action="api_key_updated",
        resource_type="api_key",
        resource_id=api_key.id,
        user_id=current_user.id,
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request),
        details={"key_name": api_key.key_name},
    )

    return api_key


@router.delete("/{api_key_id}", response_model=dict)
async def delete_api_key(
    api_key_id: int,
    request: Request,
    current_user=Depends(security.get_current_active_user),
    db: AsyncSession = Depends(get_async_session),
):
    """Delete an API key (owner or superuser only)."""
    # Get key info before deletion for audit log
    api_key = await api_key_service.get_api_key_by_id(db, api_key_id)
    if not api_key:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="API key not found")

    success = await api_key_service.delete_api_key(db, api_key_id, current_user.id)
    if not success:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete this API key")

    # Log API key deletion
    await create_audit_log(
        db,
        action="api_key_deleted",
        resource_type="api_key",
        resource_id=api_key_id,
        user_id=current_user.id,
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request),
        details={"key_name": api_key.key_name},
    )

    return {"message": "API key deleted successfully"}


@router.post("/revoke/{api_key_id}", response_model=dict)
async def revoke_api_key(
    api_key_id: int,
    request: Request,
    current_user=Depends(security.get_current_active_user),
    db: AsyncSession = Depends(get_async_session),
):
    """Revoke an API key (owner or superuser only)."""
    # Get key info before revocation for audit log
    api_key = await api_key_service.get_api_key_by_id(db, api_key_id)
    if not api_key:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="API key not found")

    revoked_key = await api_key_service.revoke_api_key(db, api_key_id, current_user.id)
    if not revoked_key:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to revoke this API key")

    # Log API key revocation
    await create_audit_log(
        db,
        action="api_key_revoked",
        resource_type="api_key",
        resource_id=api_key_id,
        user_id=current_user.id,
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request),
        details={"key_name": api_key.key_name},
    )

    return {"message": "API key revoked successfully"}
"""
Device Management API Endpoints

Provides:
- GET /devices/ - List all devices/sessions for current user
- GET /devices/stats - Get device statistics
- GET /devices/{device_id} - Get device details
- POST /devices/revoke - Revoke a specific device
- POST /devices/revoke-all - Revoke all devices
- POST /devices/{device_id}/mark-current - Mark device as current
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import security
from app.core.request import get_client_ip, get_user_agent
from app.db.dependencies import get_async_session
from app.schemas import token as token_schema
from app.services import device as device_service
from app.services.audit_log import create_audit_log

logger = logging.getLogger("ai_bos")

router = APIRouter()


@router.get("/", response_model=token_schema.DeviceListResponse)
async def list_devices(
    request: Request,
    skip: int = 0,
    limit: int = 50,
    include_revoked: bool = False,
    current_user=Depends(security.get_current_active_user),
    db: AsyncSession = Depends(get_async_session),
):
    """List all devices/sessions for the current user with pagination."""
    tokens, total = await device_service.get_user_devices(
        db,
        user_id=current_user.id,
        skip=skip,
        limit=limit,
        include_revoked=include_revoked,
    )
    devices = [device_service.token_to_device_out(t) for t in tokens]
    return {
        "items": devices,
        "total": total,
        "page": (skip // limit) + 1 if limit > 0 else 1,
        "page_size": limit,
    }


@router.get("/stats", response_model=dict)
async def get_device_stats(
    request: Request,
    current_user=Depends(security.get_current_active_user),
    db: AsyncSession = Depends(get_async_session),
):
    """Get device statistics for the current user."""
    return await device_service.get_device_stats(db, current_user.id)


@router.get("/{device_id}", response_model=token_schema.DeviceOut)
async def get_device(
    device_id: int,
    request: Request,
    current_user=Depends(security.get_current_active_user),
    db: AsyncSession = Depends(get_async_session),
):
    """Get details of a specific device/session."""
    token = await device_service.get_device_by_id(db, device_id, current_user.id)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found",
        )
    return device_service.token_to_device_out(token)


@router.post("/revoke", response_model=token_schema.DeviceRevokeResponse)
async def revoke_device(
    request: Request,
    revoke_data: token_schema.TokenRevokeRequest,
    current_user=Depends(security.get_current_active_user),
    db: AsyncSession = Depends(get_async_session),
):
    """Revoke a specific device/session by ID."""
    token = await device_service.get_device_by_id(db, revoke_data.token_id, current_user.id)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found",
        )

    result = await device_service.revoke_device(db, revoke_data.token_id, current_user.id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found or already revoked",
        )

    await create_audit_log(
        db,
        action="device_revoked",
        resource_type="auth",
        resource_id=current_user.id,
        user_id=current_user.id,
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request),
        details={
            "device_id": revoke_data.token_id,
            "device_name": token.device_name,
            "device_type": token.device_type,
        },
    )

    return {
        "message": "Device revoked successfully",
        "device_id": revoke_data.token_id,
        "revoked": True,
    }


@router.post("/revoke-all", response_model=dict)
async def revoke_all_devices(
    request: Request,
    current_user=Depends(security.get_current_active_user),
    db: AsyncSession = Depends(get_async_session),
):
    """Revoke all active devices/sessions for the current user."""
    count = await device_service.revoke_all_devices(db, current_user.id)

    await create_audit_log(
        db,
        action="all_devices_revoked",
        resource_type="auth",
        resource_id=current_user.id,
        user_id=current_user.id,
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request),
        details={"revoked_count": count},
    )

    return {
        "message": f"All devices revoked successfully",
        "revoked_count": count,
    }


@router.post("/{device_id}/mark-current", response_model=dict)
async def mark_device_current(
    device_id: int,
    request: Request,
    current_user=Depends(security.get_current_active_user),
    db: AsyncSession = Depends(get_async_session),
):
    """Mark a device as the current device."""
    token = await device_service.get_device_by_id(db, device_id, current_user.id)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found",
        )

    await device_service.mark_current_device(db, device_id, current_user.id)

    await create_audit_log(
        db,
        action="device_marked_current",
        resource_type="auth",
        resource_id=current_user.id,
        user_id=current_user.id,
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request),
        details={"device_id": device_id},
    )

    return {
        "message": "Device marked as current",
        "device_id": device_id,
    }

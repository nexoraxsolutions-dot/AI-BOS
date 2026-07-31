"""
Two-Factor Authentication (2FA) API Endpoints

Provides:
- POST /auth/2fa/setup - Initialize 2FA setup (returns secret + QR URL + backup codes)
- POST /auth/2fa/verify - Verify and enable 2FA with TOTP token
- POST /auth/2fa/disable - Disable 2FA
- GET  /auth/2fa/status - Check 2FA status
- POST /auth/2fa/regenerate-backup-codes - Regenerate backup codes
- GET  /auth/2fa/backup-codes-remaining - Get remaining backup code count
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import security
from app.core.request import get_client_ip, get_user_agent
from app.db.dependencies import get_async_session
from app.schemas import two_factor as two_factor_schema
from app.services import two_factor as two_factor_service
from app.services.audit_log import create_audit_log

logger = logging.getLogger("ai_bos")

router = APIRouter()


@router.post("/2fa/setup", response_model=two_factor_schema.TwoFactorSetupResponse)
async def setup_2fa(
    request: Request,
    current_user=Depends(security.get_current_active_user),
    db: AsyncSession = Depends(get_async_session),
):
    """Initialize 2FA setup. Returns secret, QR code URL, and backup codes."""
    if current_user.is_2fa_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="2FA is already enabled. Disable it first to reconfigure.",
        )

    secret, qr_code_url, backup_codes = await two_factor_service.setup_2fa(db, current_user)

    await create_audit_log(
        db,
        action="2fa_setup_initiated",
        resource_type="auth",
        resource_id=current_user.id,
        user_id=current_user.id,
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request),
        details={"email": current_user.email},
    )

    return two_factor_schema.TwoFactorSetupResponse(
        secret=secret,
        qr_code_url=qr_code_url,
        backup_codes=backup_codes,
    )


@router.post("/2fa/verify", response_model=two_factor_schema.TwoFactorVerifyResponse)
async def verify_2fa(
    request: Request,
    payload: two_factor_schema.TwoFactorVerifyRequest,
    current_user=Depends(security.get_current_active_user),
    db: AsyncSession = Depends(get_async_session),
):
    """Verify a TOTP token and enable 2FA."""
    if current_user.is_2fa_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="2FA is already enabled.",
        )

    if not current_user.otp_secret:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="2FA setup not initiated. Call /auth/2fa/setup first.",
        )

    valid = two_factor_service.verify_totp_token(current_user.otp_secret, payload.token)
    if not valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid token. Please try again.",
        )

    await two_factor_service.enable_2fa(db, current_user)

    await create_audit_log(
        db,
        action="2fa_enabled",
        resource_type="auth",
        resource_id=current_user.id,
        user_id=current_user.id,
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request),
        details={"email": current_user.email},
    )

    return two_factor_schema.TwoFactorVerifyResponse(
        verified=True,
        message="Two-factor authentication has been enabled successfully.",
    )


@router.post("/2fa/disable", response_model=two_factor_schema.TwoFactorVerifyResponse)
async def disable_2fa(
    request: Request,
    payload: two_factor_schema.TwoFactorDisableRequest,
    current_user=Depends(security.get_current_active_user),
    db: AsyncSession = Depends(get_async_session),
):
    """Disable 2FA. Requires password confirmation."""
    if not current_user.is_2fa_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="2FA is not enabled.",
        )

    # Verify password
    if not security.verify_password(payload.password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid password.",
        )

    await two_factor_service.disable_2fa(db, current_user)

    await create_audit_log(
        db,
        action="2fa_disabled",
        resource_type="auth",
        resource_id=current_user.id,
        user_id=current_user.id,
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request),
        details={"email": current_user.email},
    )

    return two_factor_schema.TwoFactorVerifyResponse(
        verified=True,
        message="Two-factor authentication has been disabled.",
    )


@router.get("/2fa/status", response_model=two_factor_schema.TwoFactorStatusResponse)
async def get_2fa_status(
    current_user=Depends(security.get_current_active_user),
):
    """Check if 2FA is enabled for the current user."""
    return two_factor_schema.TwoFactorStatusResponse(
        is_2fa_enabled=current_user.is_2fa_enabled,
    )


@router.post("/2fa/regenerate-backup-codes", response_model=two_factor_schema.TwoFactorSetupResponse)
async def regenerate_backup_codes(
    request: Request,
    current_user=Depends(security.get_current_active_user),
    db: AsyncSession = Depends(get_async_session),
):
    """Regenerate backup codes for an existing 2FA setup."""
    if not current_user.is_2fa_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="2FA is not enabled. Enable it first.",
        )

    if not current_user.otp_secret:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="2FA is not properly configured.",
        )

    backup_codes = await two_factor_service.regenerate_backup_codes(db, current_user)

    await create_audit_log(
        db,
        action="2fa_backup_codes_regenerated",
        resource_type="auth",
        resource_id=current_user.id,
        user_id=current_user.id,
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request),
        details={"email": current_user.email},
    )

    return two_factor_schema.TwoFactorSetupResponse(
        secret=current_user.otp_secret,
        qr_code_url=two_factor_service.get_qr_code_url(current_user.otp_secret, current_user.email),
        backup_codes=backup_codes,
    )


@router.get("/2fa/backup-codes-remaining")
async def get_backup_codes_remaining(
    current_user=Depends(security.get_current_active_user),
    db: AsyncSession = Depends(get_async_session),
):
    """Get the count of remaining unused backup codes."""
    count = await two_factor_service.get_remaining_backup_codes(db, current_user.id)
    return {"remaining": count}
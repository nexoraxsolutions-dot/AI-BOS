"""
Two-Factor Authentication (2FA) Service

Implements TOTP (Time-based One-Time Password) using the pyotp library.
Provides:
- Secret generation and QR code URL creation
- TOTP token verification
- Backup code generation and validation
- 2FA enable/disable logic
"""
import secrets
import logging
from datetime import datetime

import pyotp
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import pwd_context
from app.models.two_factor import TwoFactorBackupCode
from app.models.user import User

logger = logging.getLogger("ai_bos")

ISSUER_NAME = "AI-BOS"
BACKUP_CODE_COUNT = 8
BACKUP_CODE_LENGTH = 10


def generate_otp_secret() -> str:
    """Generate a new OTP secret key for a user."""
    return pyotp.random_base32()


def get_totp_uri(secret: str, email: str) -> str:
    """Get the TOTP URI for QR code generation."""
    totp = pyotp.TOTP(secret)
    return totp.provisioning_uri(name=email, issuer_name=ISSUER_NAME)


def get_qr_code_url(secret: str, email: str) -> str:
    """Generate a QR code URL via otpauth:// URI protocol."""
    uri = get_totp_uri(secret, email)
    return uri


def verify_totp_token(secret: str, token: str) -> bool:
    """Verify a TOTP token against the secret.

    Args:
        secret: The user's OTP secret
        token: The 6-digit token to verify

    Returns:
        True if the token is valid, False otherwise
    """
    if not secret or not token:
        return False
    try:
        totp = pyotp.TOTP(secret)
        return totp.verify(token, valid_window=1)
    except Exception as exc:
        logger.error("TOTP verification error: %s", exc)
        return False


def generate_backup_codes() -> list[str]:
    """Generate a set of backup codes.

    Returns:
        List of plaintext backup codes formatted as XXXX-XXXX-XXXX
    """
    codes = []
    for _ in range(BACKUP_CODE_COUNT):
        # Generate 12 hex characters (6 bytes) for 3 groups of 4
        code = secrets.token_hex(6).upper()
        # Format as XXXX-XXXX-XXXX
        formatted = "-".join([code[i:i+4] for i in range(0, len(code), 4)])
        codes.append(formatted)
    return codes


def hash_backup_code(code: str) -> str:
    """Hash a backup code for secure storage."""
    return pwd_context.hash(code)


def verify_backup_code(plain_code: str, hashed_code: str) -> bool:
    """Verify a plaintext backup code against a stored hash."""
    return pwd_context.verify(plain_code, hashed_code)


async def setup_2fa(db: AsyncSession, user: User) -> tuple[str, str, list[str]]:
    """Set up 2FA for a user.

    Args:
        db: Database session
        user: The user to set up 2FA for

    Returns:
        Tuple of (secret, qr_code_url, backup_codes)
    """
    # Generate OTP secret
    secret = generate_otp_secret()
    qr_code_url = get_qr_code_url(secret, user.email)

    # Generate backup codes
    plain_codes = generate_backup_codes()

    # Remove existing backup codes
    existing = await db.execute(
        select(TwoFactorBackupCode).where(TwoFactorBackupCode.user_id == user.id)
    )
    for code in existing.scalars().all():
        await db.delete(code)

    # Store hashed backup codes
    for code in plain_codes:
        backup_code = TwoFactorBackupCode(
            user_id=user.id,
            code_hash=hash_backup_code(code),
        )
        db.add(backup_code)

    # Store OTP secret (not enabled yet - must verify first)
    user.otp_secret = secret
    await db.commit()

    logger.info("2FA setup initiated for user %s", user.email)
    return secret, qr_code_url, plain_codes


async def enable_2fa(db: AsyncSession, user: User) -> None:
    """Enable 2FA after successful token verification."""
    user.is_2fa_enabled = True
    await db.commit()
    logger.info("2FA enabled for user %s", user.email)


async def disable_2fa(db: AsyncSession, user: User) -> None:
    """Disable 2FA and remove secrets."""
    user.is_2fa_enabled = False
    user.otp_secret = None

    # Remove backup codes
    existing = await db.execute(
        select(TwoFactorBackupCode).where(TwoFactorBackupCode.user_id == user.id)
    )
    for code in existing.scalars().all():
        await db.delete(code)

    await db.commit()
    logger.info("2FA disabled for user %s", user.email)


async def verify_2fa_token(db: AsyncSession, user: User, token: str) -> bool:
    """Verify a 2FA token for a user.

    First tries TOTP, then falls back to backup codes.
    """
    # Try TOTP
    if user.otp_secret and verify_totp_token(user.otp_secret, token):
        return True

    # Try backup codes
    result = await db.execute(
        select(TwoFactorBackupCode).where(
            TwoFactorBackupCode.user_id == user.id,
            TwoFactorBackupCode.is_used == False,
        )
    )
    for stored_code in result.scalars().all():
        if verify_backup_code(token, stored_code.code_hash):
            stored_code.is_used = True
            stored_code.used_at = datetime.utcnow()
            await db.commit()
            return True

    return False


async def get_remaining_backup_codes(db: AsyncSession, user_id: int) -> int:
    """Get the count of remaining unused backup codes."""
    result = await db.execute(
        select(TwoFactorBackupCode).where(
            TwoFactorBackupCode.user_id == user_id,
            TwoFactorBackupCode.is_used == False,
        )
    )
    return len(result.scalars().all())


async def regenerate_backup_codes(db: AsyncSession, user: User) -> list[str]:
    """Regenerate backup codes for a user."""
    plain_codes = generate_backup_codes()

    # Remove existing codes
    existing = await db.execute(
        select(TwoFactorBackupCode).where(TwoFactorBackupCode.user_id == user.id)
    )
    for code in existing.scalars().all():
        await db.delete(code)

    # Store new hashed codes
    for code in plain_codes:
        backup_code = TwoFactorBackupCode(
            user_id=user.id,
            code_hash=hash_backup_code(code),
        )
        db.add(backup_code)

    await db.commit()
    logger.info("Backup codes regenerated for user %s", user.email)
    return plain_codes
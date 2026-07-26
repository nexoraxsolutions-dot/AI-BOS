import secrets
import logging
from datetime import datetime, timedelta

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import pwd_context, get_password_hash
from app.core.password_policy import validate_password_strength, validate_password_not_reused
from app.models.password_reset import PasswordResetToken
from app.models.user import User
from app.services.email import send_password_reset_email
from app.services.audit_log import create_audit_log
from app.services import token as token_service

logger = logging.getLogger("ai_bos")


async def _revoke_existing_tokens(db: AsyncSession, user_id: int) -> None:
    """Revoke any unexpired, non-revoked password reset tokens for a user."""
    stmt = select(PasswordResetToken).where(
        and_(
            PasswordResetToken.user_id == user_id,
            PasswordResetToken.is_revoked == False,
            PasswordResetToken.expires_at > datetime.utcnow(),
        )
    )
    result = await db.execute(stmt)
    tokens = result.scalars().all()
    now = datetime.utcnow()
    for token_record in tokens:
        token_record.is_revoked = True
        token_record.revoked_at = now
    await db.commit()


async def validate_reset_token(db: AsyncSession, raw_token: str) -> User | None:
    """
    Validate a raw password reset token.

    Iterates over non-expired, non-revoked tokens and finds the one
    whose bcrypt hash matches the raw token. Returns the User if valid.
    """
    stmt = select(PasswordResetToken).where(
        and_(
            PasswordResetToken.is_revoked == False,
            PasswordResetToken.expires_at > datetime.utcnow(),
        )
    )
    result = await db.execute(stmt)
    tokens = result.scalars().all()

    for token_record in tokens:
        if pwd_context.verify(raw_token, token_record.hashed_token):
            # Fetch the user
            user_stmt = select(User).where(User.id == token_record.user_id)
            user_result = await db.execute(user_stmt)
            user = user_result.scalar_one_or_none()
            if user and user.is_active:
                return user
            break

    return None


async def reset_password(
    db: AsyncSession,
    raw_token: str,
    new_password: str,
    client_ip: str | None = None,
    user_agent: str | None = None,
) -> None:
    """
    Reset a user's password using a validated reset token.

    Steps:
    1. Validate the token exists, is not expired, and is not revoked
    2. Hash the new password
    3. Update user's hashed_password
    4. Mark the reset token as used (revoked)
    5. Revoke all remaining reset tokens for this user
    6. Invalidate all refresh tokens (force re-login)
    7. Log security audit event
    """
    # Validate the token
    user = await validate_reset_token(db, raw_token)
    if not user:
        raise ValueError("Invalid or expired password reset token")

    # Validate password strength (enterprise policy)
    validate_password_strength(new_password)

    # Validate password not reused
    await validate_password_not_reused(new_password, user.id, db)

    # Hash the new password
    user.hashed_password = get_password_hash(new_password)
    await db.commit()

    # Save new password to history
    from app.models.password_history import PasswordHistory
    history_entry = PasswordHistory(
        user_id=user.id,
        hashed_password=user.hashed_password,
    )
    db.add(history_entry)
    await db.commit()

    # Mark the used token as revoked
    stmt = select(PasswordResetToken).where(
        and_(
            PasswordResetToken.user_id == user.id,
            PasswordResetToken.is_revoked == False,
        )
    )
    result = await db.execute(stmt)
    for token_record in result.scalars().all():
        token_record.is_revoked = True
        token_record.revoked_at = datetime.utcnow()

    # Revoke all remaining reset tokens for this user
    await _revoke_existing_tokens(db, user.id)

    # Invalidate all refresh tokens (force re-login)
    await token_service.revoke_user_tokens(db, user.id, token_type="refresh")

    await db.commit()

    # Log security audit event
    await create_audit_log(
        db,
        action="password_reset_completed",
        resource_type="auth",
        resource_id=user.id,
        user_id=user.id,
        ip_address=client_ip,
        user_agent=user_agent,
        details={"email": user.email},
    )

    logger.info("Password reset completed for user %s", user.email)


async def request_password_reset(
    db: AsyncSession,
    email: str,
    client_ip: str | None = None,
    user_agent: str | None = None,
) -> None:
    """
    Initiate a password reset flow.

    Always returns silently to prevent email enumeration.
    If the email exists:
      1. Generates a cryptographically secure random token
      2. Hashes the token with bcrypt before storing
      3. Stores the hashed token with an expiration timestamp
      4. Revokes any previous active reset tokens for this user
      5. Queues the password reset email (async via Redis)
      6. Logs a security audit event
    """
    stmt = select(User).where(User.email == email)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        # Silently return — don't reveal whether the email exists
        return

    # Revoke any existing unexpired reset tokens for this user
    await _revoke_existing_tokens(db, user.id)

    # Generate cryptographically secure raw token (256-bit entropy)
    raw_token = secrets.token_urlsafe(32)

    # Hash the token with bcrypt before storing
    hashed_token = pwd_context.hash(raw_token)

    # Store the hashed token with expiration
    reset_token = PasswordResetToken(
        user_id=user.id,
        hashed_token=hashed_token,
        expires_at=datetime.utcnow() + timedelta(hours=settings.reset_token_expire_hours),
    )
    db.add(reset_token)
    await db.commit()
    await db.refresh(reset_token)

    # Determine company branding (if user belongs to a company)
    company_name = "AI-BOS"
    company_logo_url = None
    support_email = settings.email_from_address

    if user.company:
        company_name = user.company.name or company_name
        # company_logo_url could be added here if Company model has logo_url
        support_email = user.company.email or support_email

    # Queue the email with professional template and company branding
    queued = await send_password_reset_email(
        to_email=user.email,
        token=raw_token,
        frontend_url=settings.frontend_url,
        company_name=company_name,
        company_logo_url=company_logo_url,
        support_email=support_email,
        expiry_hours=settings.reset_token_expire_hours,
    )

    # Log security audit event (never log the raw token)
    await create_audit_log(
        db,
        action="password_reset_requested",
        resource_type="auth",
        resource_id=user.id,
        user_id=user.id,
        ip_address=client_ip,
        user_agent=user_agent,
        details={
            "email": user.email,
            "email_queued": queued,
            "token_expires_hours": settings.reset_token_expire_hours,
            "company_name": company_name,
        },
    )

    logger.info(
        "Password reset requested for %s (email_queued=%s, token_expires=%sh)",
        user.email,
        queued,
        settings.reset_token_expire_hours,
    )

import secrets
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import verify_password
from app.schemas.auth import RegisterRequest
from app.schemas.user import UserCreate


async def authenticate_user(db: AsyncSession, email: str, password: str):
    from app.services.user import get_user_by_email

    user = await get_user_by_email(db, email)

    if not user or not verify_password(password, user.hashed_password):
        return None

    return user


def generate_email_verification_token() -> str:
    """Generate a secure random token for email verification."""
    return secrets.token_urlsafe(48)


async def register_user(db: AsyncSession, payload: RegisterRequest):
    """Register a new user account.

    Returns the created user on success.
    Raises ValueError with a descriptive message on conflict.
    """
    from app.services.user import (
        create_user,
        get_user_by_email,
        get_user_by_username,
    )

    existing_email = await get_user_by_email(db, payload.email)
    if existing_email:
        raise ValueError("A user with this email already exists")

    if payload.username:
        existing_username = await get_user_by_username(db, payload.username)
        if existing_username:
            raise ValueError("A user with this username already exists")

    user_payload = UserCreate(
        email=payload.email,
        password=payload.password,
        full_name=payload.full_name,
        username=payload.username,
    )
    user = await create_user(db, user_payload)

    # Generate and store email verification token
    verification_token = generate_email_verification_token()
    user.email_verification_token = verification_token
    await db.commit()
    await db.refresh(user)

    # Send verification email (non-blocking in dev, logs to console)
    from app.services.email import send_verification_email
    await send_verification_email(user.email, verification_token)

    return user


async def verify_email(db: AsyncSession, token: str):
    """Verify a user's email address using a verification token.

    Returns the verified user on success.
    Raises ValueError if the token is invalid or expired.
    """
    from app.models.user import User
    from sqlalchemy import select

    result = await db.execute(
        select(User).where(User.email_verification_token == token)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise ValueError("Invalid or expired verification token")

    if user.is_email_verified:
        raise ValueError("Email is already verified")

    # Check token expiration (tokens are valid for configured hours)
    if user.created_at:
        expiration = user.created_at + timedelta(
            hours=settings.email_verification_token_expire_hours
        )
        if datetime.utcnow() > expiration:
            raise ValueError("Verification token has expired")

    user.is_email_verified = True
    user.email_verification_token = None
    await db.commit()
    await db.refresh(user)

    return user


async def resend_verification_email(db: AsyncSession, email: str):
    """Resend the email verification link.

    Raises ValueError if the user is not found or already verified.
    """
    from app.services.user import get_user_by_email

    user = await get_user_by_email(db, email)
    if not user:
        raise ValueError("No user found with this email address")

    if user.is_email_verified:
        raise ValueError("Email is already verified")

    # Generate new token
    verification_token = generate_email_verification_token()
    user.email_verification_token = verification_token
    await db.commit()
    await db.refresh(user)

    # Send verification email
    from app.services.email import send_verification_email
    await send_verification_email(user.email, verification_token)

    return user

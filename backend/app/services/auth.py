from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import verify_password
from app.schemas.auth import RegisterRequest
from app.schemas.user import UserCreate


async def authenticate_user(db: AsyncSession, email: str, password: str):
    from app.services.user import get_user_by_email

    user = await get_user_by_email(db, email)

    if not user or not verify_password(password, user.hashed_password):
        return None

    return user


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
    return await create_user(db, user_payload)

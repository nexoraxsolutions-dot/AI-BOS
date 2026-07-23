from sqlalchemy.ext.asyncio import AsyncSession
from app.core.security import verify_password


async def authenticate_user(db: AsyncSession, email: str, password: str):
    from app.services.user import get_user_by_email

    user = await get_user_by_email(db, email)

    if not user or not verify_password(password, user.hashed_password):
        return None

    return user

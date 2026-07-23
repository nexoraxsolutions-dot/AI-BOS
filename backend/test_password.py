import asyncio

from app.db import AsyncSessionLocal
from app.core.security import verify_password
from app.services.user import get_user_by_email

async def main():
    async with AsyncSessionLocal() as db:
        user = await get_user_by_email(db, "admin@ai-bos.com")

        print("User:", user.email)
        print("Hash:", user.hashed_password)
        print("Password valid:", verify_password("SecurePass123!", user.hashed_password))

asyncio.run(main())
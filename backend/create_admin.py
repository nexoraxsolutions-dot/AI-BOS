import asyncio

from app.db import AsyncSessionLocal
from app.db.seed import seed_data


async def main():
    async with AsyncSessionLocal() as session:
        await seed_data(session)
        print("Admin user created successfully!")


if __name__ == "__main__":
    asyncio.run(main())
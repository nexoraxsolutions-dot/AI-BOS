import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from app.core.config import settings

async def main():
    engine = create_async_engine(str(settings.database_url))

    async with engine.connect() as conn:
        result = await conn.execute(
            text("SELECT current_database(), current_schema()")
        )
        print("Database:", result.fetchall())

        try:
            result = await conn.execute(
                text("SELECT * FROM alembic_version")
            )
            print("Alembic Version:", result.fetchall())
        except Exception as e:
            print("ERROR:", e)

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(main())
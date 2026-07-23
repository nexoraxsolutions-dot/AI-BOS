from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.company import Company
from app.models.user import User
from app.core.security import get_password_hash


async def seed_data(session: AsyncSession):
    # Check if company exists
    result = await session.execute(
        select(Company).where(Company.domain == "ai-bos.com")
    )
    company = result.scalar_one_or_none()

    if company is None:
        company = Company(
            name="AI BOS",
            domain="ai-bos.com"
        )
        session.add(company)
        await session.commit()
        await session.refresh(company)

    # Check if admin user exists
    result = await session.execute(
        select(User).where(User.email == "admin@ai-bos.com")
    )
    admin = result.scalar_one_or_none()

    if admin is None:
        admin = User(
            email="admin@ai-bos.com",
            hashed_password=get_password_hash("SecurePass123!"),
            full_name="AI BOS Administrator",
            is_active=True,
            is_superuser=True,
            company_id=company.id,
        )

        session.add(admin)
        await session.commit()

    print("Admin user ready!")
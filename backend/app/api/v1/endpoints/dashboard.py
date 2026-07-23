from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_active_user
from app.db.dependencies import get_async_session
from app.models.user import User
from app.services.dashboard import get_dashboard_summary
from app.schemas.dashboard import DashboardResponse, DashboardSummary

router = APIRouter()


@router.get("/summary", response_model=DashboardResponse)
async def summary(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_session),
):
    """Get a real-time dashboard summary with aggregated statistics."""
    data = await get_dashboard_summary(db)
    summary = DashboardSummary(**data)
    return DashboardResponse(
        summary=summary,
        message=f"Welcome back, {current_user.full_name or current_user.email}",
    )

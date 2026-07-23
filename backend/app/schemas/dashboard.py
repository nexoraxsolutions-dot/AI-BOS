from pydantic import BaseModel, ConfigDict
from typing import Optional


class DashboardSummary(BaseModel):
    total_users: int
    active_users: int
    total_companies: int
    total_sales_monthly: float
    total_tasks_pending: int
    recent_users_count: int
    recent_companies_count: int

    model_config = ConfigDict(from_attributes=True)


class DashboardResponse(BaseModel):
    summary: DashboardSummary
    message: str
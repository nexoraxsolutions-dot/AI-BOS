from pydantic import BaseModel, ConfigDict
from typing import List, Optional, Dict, Any


class SecurityDashboardResponse(BaseModel):
    security_score: int
    total_users: int
    users_with_2fa: int
    locked_accounts: int
    users_with_failed_logins: int
    active_sessions: int
    failed_logins_24h: int
    failed_logins_7d: int
    account_lockouts_30d: int
    password_changes_30d: int
    two_fa_enabled_30d: int
    suspicious_ips_count: int
    recent_events: List[Dict[str, Any]]

    model_config = ConfigDict(from_attributes=True)


class SecurityEvent(BaseModel):
    id: int
    action: str
    user_id: Optional[int]
    ip_address: Optional[str]
    created_at: str
    details: Optional[Dict[str, Any]]

    model_config = ConfigDict(from_attributes=True)


class SecurityMetricsResponse(BaseModel):
    """Response for specific security metrics."""
    metric_name: str
    value: int
    trend: Optional[str] = None  # "up", "down", "stable"
    change_percentage: Optional[float] = None

    model_config = ConfigDict(from_attributes=True)
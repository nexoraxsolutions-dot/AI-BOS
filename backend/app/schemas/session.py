from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime


class SessionBase(BaseModel):
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    device_name: Optional[str] = None
    device_type: Optional[str] = None
    browser: Optional[str] = None
    os: Optional[str] = None
    is_active: bool = True


class SessionCreate(SessionBase):
    user_id: int
    session_token: str
    expires_at: datetime


class SessionTerminateRequest(BaseModel):
    session_id: int


class SessionUpdate(BaseModel):
    is_active: Optional[bool] = None
    last_activity_at: Optional[datetime] = None
    terminated_at: Optional[datetime] = None


class SessionOut(SessionBase):
    id: int
    user_id: int
    session_token: str
    last_activity_at: Optional[datetime] = None
    expires_at: datetime
    created_at: Optional[datetime] = None
    terminated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class SessionListResponse(BaseModel):
    items: list[SessionOut]
    total: int
    page: int
    page_size: int


class SessionTerminateResponse(BaseModel):
    message: str
    session_id: int
    terminated: bool


class SessionCleanupResponse(BaseModel):
    message: str
    deleted_count: int
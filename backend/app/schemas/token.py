from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime


class TokenBase(BaseModel):
    token_type: str = "refresh"
    client_ip: Optional[str] = None
    user_agent: Optional[str] = None
    device_name: Optional[str] = None
    device_type: Optional[str] = None
    is_current: bool = False


class TokenCreate(TokenBase):
    token: str
    user_id: int
    expires_at: datetime


class TokenOut(TokenBase):
    id: int
    user_id: int
    token: str
    is_revoked: bool
    expires_at: datetime
    created_at: Optional[datetime] = None
    last_used_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class DeviceInfo(BaseModel):
    """Parsed device information from user-agent."""
    device_type: Optional[str] = None
    device_name: Optional[str] = None
    browser: Optional[str] = None
    os: Optional[str] = None
    is_mobile: bool = False
    is_tablet: bool = False
    is_desktop: bool = False


class DeviceOut(BaseModel):
    """Device/session information for the frontend."""
    id: int
    user_id: int
    device_name: Optional[str] = None
    device_type: Optional[str] = None
    browser: Optional[str] = None
    os: Optional[str] = None
    client_ip: Optional[str] = None
    is_current: bool = False
    is_revoked: bool = False
    expires_at: datetime
    created_at: Optional[datetime] = None
    last_used_at: Optional[datetime] = None
    user_agent: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class DeviceListResponse(BaseModel):
    items: list[DeviceOut]
    total: int
    page: int
    page_size: int


class DeviceRevokeResponse(BaseModel):
    message: str
    device_id: int
    revoked: bool


class TokenListResponse(BaseModel):
    items: list[TokenOut]
    total: int
    page: int
    page_size: int


class TokenRevokeRequest(BaseModel):
    token_id: int


class TokenRevokeResponse(BaseModel):
    message: str
    token_id: int
    revoked: bool


class TokenCleanupResponse(BaseModel):
    message: str
    deleted_count: int
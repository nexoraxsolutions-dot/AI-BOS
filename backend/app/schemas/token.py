from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime


class TokenBase(BaseModel):
    token_type: str = "refresh"
    client_ip: Optional[str] = None
    user_agent: Optional[str] = None


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

    model_config = ConfigDict(from_attributes=True)


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
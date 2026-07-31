from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from datetime import datetime


class ApiKeyBase(BaseModel):
    key_name: str = Field(..., min_length=1, max_length=255)
    permissions: Optional[str] = None
    is_active: bool = True
    expires_at: Optional[datetime] = None


class ApiKeyCreate(ApiKeyBase):
    pass


class ApiKeyUpdate(BaseModel):
    key_name: Optional[str] = Field(None, min_length=1, max_length=255)
    permissions: Optional[str] = None
    is_active: Optional[bool] = None
    expires_at: Optional[datetime] = None


class ApiKeyOut(ApiKeyBase):
    id: int
    user_id: int
    api_key: str
    last_used_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class ApiKeyListResponse(BaseModel):
    items: list[ApiKeyOut]
    total: int
    page: int
    page_size: int


class ApiKeyCreateResponse(BaseModel):
    id: int
    key_name: str
    api_key: str
    message: str
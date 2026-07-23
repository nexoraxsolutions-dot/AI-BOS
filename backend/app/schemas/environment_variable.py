from pydantic import BaseModel, field_validator, ConfigDict
from typing import Optional
from datetime import datetime
import re


class EnvironmentVariableBase(BaseModel):
    key: str
    value: str
    description: Optional[str] = None
    is_secret: bool = False

    @field_validator('key')
    @classmethod
    def validate_key(cls, v):
        # Environment variable keys should be uppercase with underscores
        if not re.match(r'^[A-Z][A-Z0-9_]*$', v):
            raise ValueError('Key must be uppercase letters, numbers, and underscores only (e.g., DATABASE_URL)')
        if len(v) < 2:
            raise ValueError('Key must be at least 2 characters long')
        if len(v) > 255:
            raise ValueError('Key must not exceed 255 characters')
        return v

    @field_validator('value')
    @classmethod
    def validate_value(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('Value cannot be empty')
        if len(v) > 10000:
            raise ValueError('Value must not exceed 10000 characters')
        return v

    @field_validator('description')
    @classmethod
    def validate_description(cls, v):
        if v is not None and len(v) > 500:
            raise ValueError('Description must not exceed 500 characters')
        return v


class EnvironmentVariableCreate(EnvironmentVariableBase):
    pass


class EnvironmentVariableUpdate(BaseModel):
    value: Optional[str] = None
    description: Optional[str] = None
    is_secret: Optional[bool] = None

    @field_validator('value')
    @classmethod
    def validate_value(cls, v):
        if v is not None:
            if not v or len(v.strip()) == 0:
                raise ValueError('Value cannot be empty')
            if len(v) > 10000:
                raise ValueError('Value must not exceed 10000 characters')
        return v

    @field_validator('description')
    @classmethod
    def validate_description(cls, v):
        if v is not None and len(v) > 500:
            raise ValueError('Description must not exceed 500 characters')
        return v


class EnvironmentVariableOut(BaseModel):
    id: int
    key: str
    value: Optional[str] = None
    masked_value: Optional[str] = None
    description: Optional[str] = None
    is_secret: bool = False
    created_at: str
    updated_at: str

    model_config = ConfigDict(from_attributes=True)

    @field_validator('created_at', 'updated_at', mode='before')
    @classmethod
    def serialize_datetime(cls, v):
        if isinstance(v, datetime):
            return v.isoformat()
        return v

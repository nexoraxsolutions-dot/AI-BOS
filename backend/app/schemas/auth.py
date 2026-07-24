from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional
from datetime import datetime


class Token(BaseModel):
    access_token: str
    token_type: str
    refresh_token: Optional[str] = None


class TokenData(BaseModel):
    email: str | None = None
    user_id: int | None = None


class RefreshToken(BaseModel):
    refresh_token: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None
    username: Optional[str] = None

    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v

    @field_validator('username')
    @classmethod
    def validate_username(cls, v):
        if v is not None:
            if len(v) < 3:
                raise ValueError('Username must be at least 3 characters long')
            if len(v) > 50:
                raise ValueError('Username must be at most 50 characters long')
            if not v.isalnum() and '_' not in v:
                raise ValueError('Username must contain only letters, numbers, and underscores')
        return v


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordReset(BaseModel):
    token: str
    new_password: str

    @field_validator('new_password')
    @classmethod
    def validate_new_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

    @field_validator('new_password')
    @classmethod
    def validate_new_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v


class TokenValidationResponse(BaseModel):
    valid: bool
    email: Optional[str] = None
    user_id: Optional[int] = None
    exp: Optional[datetime] = None


class MessageResponse(BaseModel):
    message: str


class RegisterResponse(BaseModel):
    """Response returned after successful self-service registration."""

    access_token: str
    token_type: str = "bearer"
    refresh_token: Optional[str] = None
    user: "UserOutLite"


class UserOutLite(BaseModel):
    """Minimal user payload embedded in registration response."""

    id: int
    email: EmailStr
    full_name: Optional[str] = None
    username: Optional[str] = None
    is_active: bool = True
    is_superuser: bool = False
    company_id: Optional[int] = None

    model_config = {"from_attributes": True}


# Resolve forward reference for RegisterResponse.user
RegisterResponse.model_rebuild()



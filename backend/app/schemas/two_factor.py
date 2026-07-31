from pydantic import BaseModel, field_validator
from typing import Optional


class TwoFactorSetupResponse(BaseModel):
    secret: str
    qr_code_url: str
    backup_codes: list[str]


class TwoFactorVerifyRequest(BaseModel):
    token: str

    @field_validator("token")
    @classmethod
    def validate_token(cls, v):
        if not v or not v.strip():
            raise ValueError("Token is required")
        if len(v.strip()) != 6:
            raise ValueError("Token must be 6 digits")
        if not v.strip().isdigit():
            raise ValueError("Token must contain only digits")
        return v.strip()


class TwoFactorVerifyResponse(BaseModel):
    verified: bool
    message: str


class TwoFactorLoginRequest(BaseModel):
    email: str
    password: str
    otp_token: Optional[str] = None
    backup_code: Optional[str] = None


class TwoFactorLoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    requires_2fa: bool = False
    temp_token: Optional[str] = None
    user: Optional[dict] = None


class TwoFactorStatusResponse(BaseModel):
    is_2fa_enabled: bool


class TwoFactorDisableRequest(BaseModel):
    password: str
from pydantic import BaseModel, field_validator, ConfigDict
from typing import Optional, Dict, Any, List


class PasswordRequirement(BaseModel):
    """Individual password requirement."""
    id: str
    label: str
    key: str
    value: Any
    met: bool = False


class PasswordPolicyResponse(BaseModel):
    """Password policy response."""
    min_length: int
    require_uppercase: bool
    require_lowercase: bool
    require_numbers: bool
    require_special_chars: bool
    expiry_days: int
    requirements: List[PasswordRequirement]


class PasswordValidationRequest(BaseModel):
    """Request to validate a password against policy."""
    password: str


class PasswordValidationResponse(BaseModel):
    """Response from password validation."""
    valid: bool
    errors: List[str] = []
    requirements: List[PasswordRequirement] = []


class PasswordPolicyUpdate(BaseModel):
    """Schema for updating password policy (all fields optional)."""
    min_length: Optional[int] = None
    require_uppercase: Optional[bool] = None
    require_lowercase: Optional[bool] = None
    require_numbers: Optional[bool] = None
    require_special_chars: Optional[bool] = None
    expiry_days: Optional[int] = None

    @field_validator('min_length')
    @classmethod
    def validate_min_length(cls, v):
        if v is not None:
            if v < 6 or v > 128:
                raise ValueError('Password minimum length must be between 6 and 128')
        return v

    @field_validator('expiry_days')
    @classmethod
    def validate_expiry_days(cls, v):
        if v is not None:
            if v < 0 or v > 365:
                raise ValueError('Password expiry days must be between 0 and 365 (0 means never expires)')
        return v


class PasswordPolicyOut(BaseModel):
    """Password policy output schema."""
    company_id: int
    min_length: int
    require_uppercase: bool
    require_lowercase: bool
    require_numbers: bool
    require_special_chars: bool
    expiry_days: int

    model_config = ConfigDict(from_attributes=True)
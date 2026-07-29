from pydantic import BaseModel, field_validator, ConfigDict
from typing import Optional, Dict, Any, List
from datetime import datetime


class OrganizationSettingsBase(BaseModel):
    """Base schema for organization settings."""
    timezone: Optional[str] = "UTC"
    date_format: Optional[str] = "YYYY-MM-DD"
    time_format: Optional[str] = "24h"
    language: Optional[str] = "en"
    currency: Optional[str] = "USD"
    
    # Security settings
    password_min_length: Optional[int] = 8
    password_require_uppercase: Optional[bool] = True
    password_require_lowercase: Optional[bool] = True
    password_require_numbers: Optional[bool] = True
    password_require_special_chars: Optional[bool] = True
    password_expiry_days: Optional[int] = 90
    session_timeout_minutes: Optional[int] = 60
    enforce_2fa: Optional[bool] = False
    max_login_attempts: Optional[int] = 5
    
    # Notification settings
    email_notifications_enabled: Optional[bool] = True
    notify_on_user_creation: Optional[bool] = True
    notify_on_user_deletion: Optional[bool] = True
    notify_on_password_reset: Optional[bool] = True
    notify_on_security_alerts: Optional[bool] = True
    notify_on_subscription_changes: Optional[bool] = True
    
    # Branding settings
    primary_color: Optional[str] = "#06b6d4"
    logo_url: Optional[str] = None
    custom_css: Optional[str] = None
    
    # Feature flags
    enable_user_registration: Optional[bool] = True
    enable_api_access: Optional[bool] = True
    enable_audit_logs: Optional[bool] = True
    enable_data_export: Optional[bool] = True
    
    # Custom settings (for extensibility)
    custom_settings: Optional[Dict[str, Any]] = None

    @field_validator('timezone')
    @classmethod
    def validate_timezone(cls, v):
        if v is not None:
            # Basic timezone validation (e.g., "UTC", "America/New_York")
            try:
                from zoneinfo import ZoneInfo
                ZoneInfo(v)
            except (ImportError, KeyError):
                # Fallback: accept common timezones without strict validation
                common_timezones = [
                    'UTC', 'America/New_York', 'America/Chicago', 'America/Denver', 
                    'America/Los_Angeles', 'Europe/London', 'Europe/Paris', 
                    'Asia/Tokyo', 'Asia/Shanghai', 'Asia/Karachi', 'Australia/Sydney'
                ]
                if v not in common_timezones:
                    raise ValueError(f'Invalid timezone: {v}')
        return v

    @field_validator('date_format')
    @classmethod
    def validate_date_format(cls, v):
        if v is not None:
            valid_formats = ['YYYY-MM-DD', 'DD/MM/YYYY', 'MM/DD/YYYY', 'DD-MM-YYYY']
            if v not in valid_formats:
                raise ValueError(f'Invalid date format. Must be one of: {", ".join(valid_formats)}')
        return v

    @field_validator('time_format')
    @classmethod
    def validate_time_format(cls, v):
        if v is not None:
            valid_formats = ['12h', '24h']
            if v not in valid_formats:
                raise ValueError(f'Invalid time format. Must be one of: {", ".join(valid_formats)}')
        return v

    @field_validator('language')
    @classmethod
    def validate_language(cls, v):
        if v is not None:
            valid_languages = ['en', 'es', 'fr', 'de', 'it', 'pt', 'zh', 'ja', 'ko']
            if v not in valid_languages:
                raise ValueError(f'Invalid language code. Must be one of: {", ".join(valid_languages)}')
        return v

    @field_validator('currency')
    @classmethod
    def validate_currency(cls, v):
        if v is not None:
            valid_currencies = ['USD', 'EUR', 'GBP', 'JPY', 'CAD', 'AUD', 'INR', 'BRL']
            if v not in valid_currencies:
                raise ValueError(f'Invalid currency code. Must be one of: {", ".join(valid_currencies)}')
        return v

    @field_validator('password_min_length')
    @classmethod
    def validate_password_min_length(cls, v):
        if v is not None:
            if v < 6 or v > 128:
                raise ValueError('Password minimum length must be between 6 and 128')
        return v

    @field_validator('password_expiry_days')
    @classmethod
    def validate_password_expiry_days(cls, v):
        if v is not None:
            if v < 0 or v > 365:
                raise ValueError('Password expiry days must be between 0 and 365 (0 means never expires)')
        return v

    @field_validator('session_timeout_minutes')
    @classmethod
    def validate_session_timeout(cls, v):
        if v is not None:
            if v < 5 or v > 1440:
                raise ValueError('Session timeout must be between 5 and 1440 minutes (24 hours)')
        return v

    @field_validator('max_login_attempts')
    @classmethod
    def validate_max_login_attempts(cls, v):
        if v is not None:
            if v < 1 or v > 20:
                raise ValueError('Max login attempts must be between 1 and 20')
        return v

    @field_validator('primary_color')
    @classmethod
    def validate_primary_color(cls, v):
        if v is not None:
            import re
            if not re.match(r'^#[0-9A-Fa-f]{6}$', v):
                raise ValueError('Primary color must be a valid hex color (e.g., #06b6d4)')
        return v


class OrganizationSettingsCreate(OrganizationSettingsBase):
    """Schema for creating organization settings."""
    company_id: int


class OrganizationSettingsUpdate(BaseModel):
    """Schema for updating organization settings (all fields optional)."""
    timezone: Optional[str] = None
    date_format: Optional[str] = None
    time_format: Optional[str] = None
    language: Optional[str] = None
    currency: Optional[str] = None
    
    password_min_length: Optional[int] = None
    password_require_uppercase: Optional[bool] = None
    password_require_lowercase: Optional[bool] = None
    password_require_numbers: Optional[bool] = None
    password_require_special_chars: Optional[bool] = None
    password_expiry_days: Optional[int] = None
    session_timeout_minutes: Optional[int] = None
    enforce_2fa: Optional[bool] = None
    max_login_attempts: Optional[int] = None
    
    email_notifications_enabled: Optional[bool] = None
    notify_on_user_creation: Optional[bool] = None
    notify_on_user_deletion: Optional[bool] = None
    notify_on_password_reset: Optional[bool] = None
    notify_on_security_alerts: Optional[bool] = None
    notify_on_subscription_changes: Optional[bool] = None
    
    primary_color: Optional[str] = None
    logo_url: Optional[str] = None
    custom_css: Optional[str] = None
    
    enable_user_registration: Optional[bool] = None
    enable_api_access: Optional[bool] = None
    enable_audit_logs: Optional[bool] = None
    enable_data_export: Optional[bool] = None
    
    custom_settings: Optional[Dict[str, Any]] = None

    @field_validator('timezone')
    @classmethod
    def validate_timezone(cls, v):
        if v is not None:
            # Basic timezone validation (e.g., "UTC", "America/New_York")
            try:
                from zoneinfo import ZoneInfo
                ZoneInfo(v)
            except (ImportError, KeyError):
                # Fallback: accept common timezones without strict validation
                common_timezones = [
                    'UTC', 'America/New_York', 'America/Chicago', 'America/Denver', 
                    'America/Los_Angeles', 'Europe/London', 'Europe/Paris', 
                    'Asia/Tokyo', 'Asia/Shanghai', 'Asia/Karachi', 'Australia/Sydney'
                ]
                if v not in common_timezones:
                    raise ValueError(f'Invalid timezone: {v}')
        return v

    @field_validator('date_format')
    @classmethod
    def validate_date_format(cls, v):
        if v is not None:
            valid_formats = ['YYYY-MM-DD', 'DD/MM/YYYY', 'MM/DD/YYYY', 'DD-MM-YYYY']
            if v not in valid_formats:
                raise ValueError(f'Invalid date format. Must be one of: {", ".join(valid_formats)}')
        return v

    @field_validator('time_format')
    @classmethod
    def validate_time_format(cls, v):
        if v is not None:
            valid_formats = ['12h', '24h']
            if v not in valid_formats:
                raise ValueError(f'Invalid time format. Must be one of: {", ".join(valid_formats)}')
        return v

    @field_validator('language')
    @classmethod
    def validate_language(cls, v):
        if v is not None:
            valid_languages = ['en', 'es', 'fr', 'de', 'it', 'pt', 'zh', 'ja', 'ko']
            if v not in valid_languages:
                raise ValueError(f'Invalid language code. Must be one of: {", ".join(valid_languages)}')
        return v

    @field_validator('currency')
    @classmethod
    def validate_currency(cls, v):
        if v is not None:
            valid_currencies = ['USD', 'EUR', 'GBP', 'JPY', 'CAD', 'AUD', 'INR', 'BRL']
            if v not in valid_currencies:
                raise ValueError(f'Invalid currency code. Must be one of: {", ".join(valid_currencies)}')
        return v

    @field_validator('password_min_length')
    @classmethod
    def validate_password_min_length(cls, v):
        if v is not None:
            if v < 6 or v > 128:
                raise ValueError('Password minimum length must be between 6 and 128')
        return v

    @field_validator('password_expiry_days')
    @classmethod
    def validate_password_expiry_days(cls, v):
        if v is not None:
            if v < 0 or v > 365:
                raise ValueError('Password expiry days must be between 0 and 365')
        return v

    @field_validator('session_timeout_minutes')
    @classmethod
    def validate_session_timeout(cls, v):
        if v is not None:
            if v < 5 or v > 1440:
                raise ValueError('Session timeout must be between 5 and 1440 minutes')
        return v

    @field_validator('max_login_attempts')
    @classmethod
    def validate_max_login_attempts(cls, v):
        if v is not None:
            if v < 1 or v > 20:
                raise ValueError('Max login attempts must be between 1 and 20')
        return v

    @field_validator('primary_color')
    @classmethod
    def validate_primary_color(cls, v):
        if v is not None:
            import re
            if not re.match(r'^#[0-9A-Fa-f]{6}$', v):
                raise ValueError('Primary color must be a valid hex color (e.g., #06b6d4)')
        return v


class OrganizationSettingsOut(OrganizationSettingsBase):
    """Schema for organization settings output."""
    id: int
    company_id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class OrganizationSettingsResponse(BaseModel):
    """Response schema for organization settings."""
    settings: OrganizationSettingsOut
    message: str
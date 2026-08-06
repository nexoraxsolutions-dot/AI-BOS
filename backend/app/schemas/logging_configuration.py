from pydantic import BaseModel, field_validator, ConfigDict
from typing import Optional
from datetime import datetime


class LoggingConfigurationBase(BaseModel):
    """Base schema for logging configuration."""
    log_level: Optional[str] = "INFO"
    enable_database_logging: Optional[bool] = True
    enable_console_logging: Optional[bool] = True
    log_format: Optional[str] = "text"
    retention_days: Optional[int] = 90

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level is one of the allowed values."""
        allowed = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if v.upper() not in allowed:
            raise ValueError(f"log_level must be one of {allowed}")
        return v.upper()

    @field_validator("log_format")
    @classmethod
    def validate_log_format(cls, v: str) -> str:
        """Validate log format is one of the allowed values."""
        allowed = {"text", "json"}
        if v.lower() not in allowed:
            raise ValueError(f"log_format must be one of {allowed}")
        return v.lower()

    @field_validator("retention_days")
    @classmethod
    def validate_retention_days(cls, v: int) -> int:
        """Validate retention days is within reasonable bounds."""
        if v < 1 or v > 3650:  # 1 day to 10 years
            raise ValueError("retention_days must be between 1 and 3650")
        return v


class LoggingConfigurationCreate(LoggingConfigurationBase):
    """Schema for creating logging configuration."""
    company_id: int


class LoggingConfigurationUpdate(BaseModel):
    """Schema for updating logging configuration (all fields optional)."""
    log_level: Optional[str] = None
    enable_database_logging: Optional[bool] = None
    enable_console_logging: Optional[bool] = None
    log_format: Optional[str] = None
    retention_days: Optional[int] = None

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: Optional[str]) -> Optional[str]:
        """Validate log level is one of the allowed values."""
        if v is None:
            return v
        allowed = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if v.upper() not in allowed:
            raise ValueError(f"log_level must be one of {allowed}")
        return v.upper()

    @field_validator("log_format")
    @classmethod
    def validate_log_format(cls, v: Optional[str]) -> Optional[str]:
        """Validate log format is one of the allowed values."""
        if v is None:
            return v
        allowed = {"text", "json"}
        if v.lower() not in allowed:
            raise ValueError(f"log_format must be one of {allowed}")
        return v.lower()

    @field_validator("retention_days")
    @classmethod
    def validate_retention_days(cls, v: Optional[int]) -> Optional[int]:
        """Validate retention days is within reasonable bounds."""
        if v is None:
            return v
        if v < 1 or v > 3650:
            raise ValueError("retention_days must be between 1 and 3650")
        return v


class LoggingConfigurationOut(LoggingConfigurationBase):
    """Schema for logging configuration output."""
    id: int
    company_id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class LoggingConfigurationResponse(BaseModel):
    """Response schema for logging configuration."""
    config: LoggingConfigurationOut
    message: str

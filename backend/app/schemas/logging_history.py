from pydantic import BaseModel, ConfigDict, field_validator
from typing import Optional, Any
from datetime import datetime


class LogEntryBase(BaseModel):
    level: str
    logger_name: str
    message: str
    module: Optional[str] = None
    func_name: Optional[str] = None
    line_no: Optional[int] = None
    pathname: Optional[str] = None
    thread_name: Optional[str] = None
    process: Optional[str] = None
    user_id: Optional[int] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    extra_data: Optional[dict[str, Any]] = None

    @field_validator("level")
    @classmethod
    def validate_level(cls, v: str) -> str:
        allowed = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if v.upper() not in allowed:
            raise ValueError(f"level must be one of {allowed}")
        return v.upper()


class LogEntryCreate(LogEntryBase):
    timestamp: Optional[datetime] = None


class LogEntryOut(LogEntryBase):
    id: int
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)


class LogEntryListResponse(BaseModel):
    items: list[LogEntryOut]
    total: int
    page: int
    page_size: int


class LogStats(BaseModel):
    total_entries: int
    by_level: dict[str, int]
    top_loggers: list[dict[str, Any]]
    oldest_entry: Optional[datetime] = None
    newest_entry: Optional[datetime] = None

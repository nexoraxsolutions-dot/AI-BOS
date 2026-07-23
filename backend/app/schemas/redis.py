from pydantic import BaseModel, ConfigDict
from typing import Optional, Dict, Any


class RedisHealthResponse(BaseModel):
    status: str
    version: Optional[str] = None
    connected_clients: Optional[int] = None
    used_memory_human: Optional[str] = None
    uptime_in_seconds: Optional[int] = None
    error: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class CacheStatsResponse(BaseModel):
    total_keys: int
    used_memory_human: str
    connected_clients: int
    hits: int
    misses: int
    hit_rate: float

    model_config = ConfigDict(from_attributes=True)


class FlushCacheResponse(BaseModel):
    message: str

    model_config = ConfigDict(from_attributes=True)
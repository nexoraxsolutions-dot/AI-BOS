"""Redis management endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status

from app.core.security import get_current_active_user, require_superuser
from app.core.redis import check_redis_health
from app.services.cache import cache_service
from app.schemas.redis import RedisHealthResponse, CacheStatsResponse, FlushCacheResponse

router = APIRouter()


@router.get("/health", response_model=RedisHealthResponse)
async def get_redis_health():
    """Get Redis health status."""
    health = await check_redis_health()
    if health.get("status") == "unhealthy":
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=health,
        )
    return RedisHealthResponse(**health)


@router.get("/stats", response_model=CacheStatsResponse)
async def get_cache_stats(
    current_user=Depends(get_current_active_user),
):
    """Get cache statistics (requires authentication)."""
    stats = await cache_service.get_stats()
    if "error" in stats:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=stats,
        )
    return CacheStatsResponse(**stats)


@router.delete("/flush", response_model=FlushCacheResponse)
async def flush_cache(
    current_user=Depends(get_current_active_user),
):
    """Flush all cache data (requires superuser authentication)."""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only superusers can flush cache",
        )
    success = await cache_service.flush_all()
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to flush cache",
        )
    return FlushCacheResponse(message="Cache flushed successfully")

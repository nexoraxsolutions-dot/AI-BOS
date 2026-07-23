"""Tests for Redis functionality."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import HTTPException

from app.services.cache import CacheService
from app.api.v1.endpoints.redis import get_redis_health, get_cache_stats, flush_cache
from app.schemas.redis import RedisHealthResponse, CacheStatsResponse, FlushCacheResponse


@pytest.fixture
def cache_service():
    """Create a cache service instance for testing."""
    return CacheService(default_ttl=60)


@pytest.mark.asyncio
async def test_cache_service_get_set(cache_service):
    """Test cache get and set operations."""
    with patch('app.services.cache.get_redis_client') as mock_get_client:
        mock_client = AsyncMock()
        mock_get_client.return_value = mock_client
        mock_client.get.return_value = '{"key": "value"}'
        mock_client.setex.return_value = True
        
        # Test set
        result = await cache_service.set("test_key", {"key": "value"}, ttl=120)
        assert result is True
        mock_client.setex.assert_called_once()
        
        # Test get
        result = await cache_service.get("test_key")
        assert result == {"key": "value"}
        mock_client.get.assert_called_once_with("test_key")


@pytest.mark.asyncio
async def test_cache_service_delete(cache_service):
    """Test cache delete operation."""
    with patch('app.services.cache.get_redis_client') as mock_get_client:
        mock_client = AsyncMock()
        mock_get_client.return_value = mock_client
        mock_client.delete.return_value = 1
        
        result = await cache_service.delete("test_key")
        assert result is True
        mock_client.delete.assert_called_once_with("test_key")


@pytest.mark.asyncio
async def test_cache_service_delete_pattern(cache_service):
    """Test cache delete pattern operation."""
    with patch('app.services.cache.get_redis_client') as mock_get_client:
        mock_client = AsyncMock()
        mock_get_client.return_value = mock_client
        mock_client.keys.return_value = ["key1", "key2", "key3"]
        mock_client.delete.return_value = 3
        
        result = await cache_service.delete_pattern("test:*")
        assert result == 3
        mock_client.keys.assert_called_once_with("test:*")
        mock_client.delete.assert_called_once_with("key1", "key2", "key3")


@pytest.mark.asyncio
async def test_cache_service_exists(cache_service):
    """Test cache exists operation."""
    with patch('app.services.cache.get_redis_client') as mock_get_client:
        mock_client = AsyncMock()
        mock_get_client.return_value = mock_client
        mock_client.exists.return_value = 1
        
        result = await cache_service.exists("test_key")
        assert result is True
        mock_client.exists.assert_called_once_with("test_key")


@pytest.mark.asyncio
async def test_cache_service_get_ttl(cache_service):
    """Test cache get TTL operation."""
    with patch('app.services.cache.get_redis_client') as mock_get_client:
        mock_client = AsyncMock()
        mock_get_client.return_value = mock_client
        mock_client.ttl.return_value = 300
        
        result = await cache_service.get_ttl("test_key")
        assert result == 300
        mock_client.ttl.assert_called_once_with("test_key")


@pytest.mark.asyncio
async def test_cache_service_flush_all(cache_service):
    """Test cache flush all operation."""
    with patch('app.services.cache.get_redis_client') as mock_get_client:
        mock_client = AsyncMock()
        mock_get_client.return_value = mock_client
        mock_client.flushdb.return_value = True
        
        result = await cache_service.flush_all()
        assert result is True
        mock_client.flushdb.assert_called_once()


@pytest.mark.asyncio
async def test_cache_service_get_stats(cache_service):
    """Test cache get stats operation."""
    with patch('app.services.cache.get_redis_client') as mock_get_client:
        mock_client = AsyncMock()
        mock_get_client.return_value = mock_client
        mock_client.info.return_value = {
            "redis_version": "7.0.0",
            "connected_clients": 10,
            "used_memory_human": "1.5M",
            "uptime_in_seconds": 3600,
            "keyspace_hits": 100,
            "keyspace_misses": 20,
        }
        mock_client.dbsize.return_value = 50
        
        result = await cache_service.get_stats()
        assert result["total_keys"] == 50
        assert result["used_memory_human"] == "1.5M"
        assert result["connected_clients"] == 10
        assert result["hits"] == 100
        assert result["misses"] == 20
        assert result["hit_rate"] == 83.33


@pytest.mark.asyncio
async def test_cache_service_get_stats_error(cache_service):
    """Test cache get stats with error."""
    with patch('app.services.cache.get_redis_client') as mock_get_client:
        mock_get_client.side_effect = Exception("Redis connection error")
        
        result = await cache_service.get_stats()
        assert "error" in result
        assert "Redis connection error" in result["error"]


@pytest.mark.asyncio
async def test_redis_health_endpoint():
    """Test Redis health endpoint."""
    mock_health = {
        "status": "healthy",
        "version": "7.0.0",
        "connected_clients": 10,
        "used_memory_human": "1.5M",
        "uptime_in_seconds": 3600,
    }
    
    with patch('app.api.v1.endpoints.redis.check_redis_health', new_callable=AsyncMock) as mock_check:
        mock_check.return_value = mock_health
        
        result = await get_redis_health()
        assert result.status == "healthy"
        assert result.version == "7.0.0"
        assert result.connected_clients == 10


@pytest.mark.asyncio
async def test_redis_health_endpoint_unhealthy():
    """Test Redis health endpoint when unhealthy."""
    mock_health = {
        "status": "unhealthy",
        "error": "Connection refused",
    }
    
    with patch('app.api.v1.endpoints.redis.check_redis_health', new_callable=AsyncMock) as mock_check:
        mock_check.return_value = mock_health
        
        with pytest.raises(HTTPException) as exc_info:
            await get_redis_health()
        
        assert exc_info.value.status_code == 503


@pytest.mark.asyncio
async def test_cache_stats_endpoint():
    """Test cache stats endpoint."""
    mock_stats = {
        "total_keys": 50,
        "used_memory_human": "1.5M",
        "connected_clients": 10,
        "hits": 100,
        "misses": 20,
        "hit_rate": 83.33,
    }
    
    mock_user = MagicMock()
    mock_user.is_superuser = True
    
    with patch('app.api.v1.endpoints.redis.cache_service.get_stats', new_callable=AsyncMock) as mock_get_stats:
        mock_get_stats.return_value = mock_stats
        
        result = await get_cache_stats(current_user=mock_user)
        assert result.total_keys == 50
        assert result.hit_rate == 83.33


@pytest.mark.asyncio
async def test_cache_stats_endpoint_error():
    """Test cache stats endpoint with error."""
    mock_user = MagicMock()
    mock_user.is_superuser = True
    
    with patch('app.api.v1.endpoints.redis.cache_service.get_stats', new_callable=AsyncMock) as mock_get_stats:
        mock_get_stats.return_value = {"error": "Redis connection error"}
        
        with pytest.raises(HTTPException) as exc_info:
            await get_cache_stats(current_user=mock_user)
        
        assert exc_info.value.status_code == 500


@pytest.mark.asyncio
async def test_flush_cache_endpoint_success():
    """Test flush cache endpoint with superuser."""
    mock_user = MagicMock()
    mock_user.is_superuser = True
    
    with patch('app.api.v1.endpoints.redis.cache_service.flush_all', new_callable=AsyncMock) as mock_flush:
        mock_flush.return_value = True
        
        result = await flush_cache(current_user=mock_user)
        assert result.message == "Cache flushed successfully"
        mock_flush.assert_called_once()


@pytest.mark.asyncio
async def test_flush_cache_endpoint_not_superuser():
    """Test flush cache endpoint without superuser privileges."""
    mock_user = MagicMock()
    mock_user.is_superuser = False
    
    with patch('app.api.v1.endpoints.redis.cache_service.flush_all', new_callable=AsyncMock) as mock_flush:
        mock_flush.return_value = True
        
        with pytest.raises(HTTPException) as exc_info:
            await flush_cache(current_user=mock_user)
        
        assert exc_info.value.status_code == 403
        assert "Only superusers can flush cache" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_flush_cache_endpoint_failure():
    """Test flush cache endpoint when operation fails."""
    mock_user = MagicMock()
    mock_user.is_superuser = True
    
    with patch('app.api.v1.endpoints.redis.cache_service.flush_all', new_callable=AsyncMock) as mock_flush:
        mock_flush.return_value = False
        
        with pytest.raises(HTTPException) as exc_info:
            await flush_cache(current_user=mock_user)
        
        assert exc_info.value.status_code == 500
        assert "Failed to flush cache" in str(exc_info.value.detail)
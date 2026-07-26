"""
Rate limiting and brute-force protection for authentication endpoints.

Implements:
- IP-based rate limiting
- Email-based rate limiting
- User-based rate limiting
- Temporary lockout after excessive requests
- Suspicious behavior logging
- Brute-force attack prevention
"""
import logging
from datetime import datetime, timedelta
from typing import Optional

from app.core.redis import get_redis_client
from app.services.audit_log import create_audit_log
from app.core.config import settings

logger = logging.getLogger("ai_bos")


class RateLimitExceeded(Exception):
    """Raised when rate limit is exceeded."""
    def __init__(self, message: str, retry_after: int):
        self.message = message
        self.retry_after = retry_after
        super().__init__(self.message)


class TemporaryLockout(Exception):
    """Raised when account is temporarily locked due to excessive requests."""
    def __init__(self, message: str, unlock_at: datetime):
        self.message = message
        self.unlock_at = unlock_at
        super().__init__(self.message)


async def check_rate_limit(
    db,
    identifier: str,
    limit_type: str,
    max_requests: int = 5,
    window_seconds: int = 300,
    lockout_seconds: int = 900,
) -> None:
    """
    Check if request is within rate limits.
    
    Args:
        db: Database session
        identifier: Unique identifier (IP, email, or user_id)
        limit_type: Type of rate limit ('ip', 'email', 'user')
        max_requests: Maximum requests allowed in window
        window_seconds: Time window in seconds (default: 5 minutes)
        lockout_seconds: Lockout duration after exceeding limit (default: 15 minutes)
    
    Raises:
        RateLimitExceeded: If rate limit is exceeded
        TemporaryLockout: If account is locked
    """
    try:
        client = await get_redis_client()
        now = datetime.utcnow()
        
        # Redis keys
        request_key = f"rate_limit:{limit_type}:{identifier}:requests"
        lockout_key = f"rate_limit:{limit_type}:{identifier}:lockout"
        
        # Check if locked out
        lockout_until = await client.get(lockout_key)
        if lockout_until:
            unlock_time = datetime.fromisoformat(lockout_until)
            if now < unlock_time:
                remaining = int((unlock_time - now).total_seconds())
                raise TemporaryLockout(
                    f"Too many requests. Account locked until {unlock_time.isoformat()}",
                    unlock_time
                )
            else:
                # Lockout expired, clear it
                await client.delete(lockout_key)
        
        # Get current request count
        request_count = await client.get(request_key)
        
        if request_count is None:
            # First request in window
            await client.setex(
                request_key,
                window_seconds,
                1
            )
        else:
            count = int(request_count)
            
            if count >= max_requests:
                # Exceeded rate limit - apply lockout
                unlock_time = now + timedelta(seconds=lockout_seconds)
                await client.setex(
                    lockout_key,
                    lockout_seconds,
                    unlock_time.isoformat()
                )
                
                # Log suspicious behavior
                await log_suspicious_activity(
                    db,
                    identifier=identifier,
                    limit_type=limit_type,
                    action="rate_limit_exceeded",
                    details={
                        "request_count": count,
                        "max_requests": max_requests,
                        "window_seconds": window_seconds,
                        "lockout_seconds": lockout_seconds,
                    }
                )
                
                raise RateLimitExceeded(
                    f"Rate limit exceeded. Try again in {lockout_seconds} seconds.",
                    retry_after=lockout_seconds
                )
            else:
                # Increment counter
                await client.incr(request_key)
        
    except (RateLimitExceeded, TemporaryLockout):
        raise
    except Exception as e:
        logger.error(f"Rate limit check failed: {e}")
        # Fail open - allow request if Redis is down
        pass


async def log_suspicious_activity(
    db,
    identifier: str,
    limit_type: str,
    action: str,
    details: dict,
) -> None:
    """
    Log suspicious activity for security monitoring.
    
    Args:
        db: Database session
        identifier: IP, email, or user_id
        limit_type: Type of identifier ('ip', 'email', 'user')
        action: Type of suspicious activity
        details: Additional details
    """
    try:
        await create_audit_log(
            db,
            action=f"suspicious_{action}",
            resource_type="security",
            resource_id=None,
            user_id=None,
            ip_address=identifier if limit_type == "ip" else None,
            user_agent=None,
            details={
                "identifier": identifier,
                "identifier_type": limit_type,
                "alert": True,
                **details
            },
        )
        logger.warning(
            "Suspicious activity detected: %s for %s (%s)",
            action,
            identifier,
            limit_type
        )
    except Exception as e:
        logger.error(f"Failed to log suspicious activity: {e}")


async def check_password_reset_rate_limit(
    db,
    ip_address: str,
    email: str,
    user_id: Optional[int] = None,
) -> None:
    """
    Check rate limits for password reset endpoint.
    
    Args:
        db: Database session
        ip_address: Client IP address
        email: Email address
        user_id: User ID (if user exists)
    
    Raises:
        RateLimitExceeded: If rate limit is exceeded
        TemporaryLockout: If account is locked
    """
    # Check IP-based rate limit (most strict)
    await check_rate_limit(
        db,
        identifier=ip_address,
        limit_type="ip",
        max_requests=5,
        window_seconds=300,  # 5 minutes
        lockout_seconds=900,  # 15 minutes
    )
    
    # Check email-based rate limit
    await check_rate_limit(
        db,
        identifier=email.lower(),
        limit_type="email",
        max_requests=3,
        window_seconds=600,  # 10 minutes
        lockout_seconds=1800,  # 30 minutes
    )
    
    # Check user-based rate limit (if user exists)
    if user_id:
        await check_rate_limit(
            db,
            identifier=str(user_id),
            limit_type="user",
            max_requests=3,
            window_seconds=600,  # 10 minutes
            lockout_seconds=1800,  # 30 minutes
        )


async def check_reset_password_rate_limit(
    db,
    ip_address: str,
    user_id: Optional[int] = None,
) -> None:
    """
    Check rate limits for reset password endpoint (using token).
    
    Args:
        db: Database session
        ip_address: Client IP address
        user_id: User ID (if user exists)
    
    Raises:
        RateLimitExceeded: If rate limit is exceeded
        TemporaryLockout: If account is locked
    """
    # Check IP-based rate limit
    await check_rate_limit(
        db,
        identifier=ip_address,
        limit_type="ip",
        max_requests=10,
        window_seconds=300,  # 5 minutes
        lockout_seconds=600,  # 10 minutes
    )
    
    # Check user-based rate limit (if user exists)
    if user_id:
        await check_rate_limit(
            db,
            identifier=str(user_id),
            limit_type="user",
            max_requests=5,
            window_seconds=300,  # 5 minutes
            lockout_seconds=600,  # 10 minutes
        )


async def record_failed_reset_attempt(
    db,
    ip_address: str,
    user_id: Optional[int] = None,
) -> None:
    """
    Record a failed password reset attempt for brute-force detection.
    
    Args:
        db: Database session
        ip_address: Client IP address
        user_id: User ID (if user exists)
    """
    try:
        client = await get_redis_client()
        
        # Track failed attempts by IP
        ip_key = f"failed_reset:ip:{ip_address}"
        await client.incr(ip_key)
        await client.expire(ip_key, 3600)  # 1 hour
        
        ip_count = int(await client.get(ip_key) or 0)
        
        # Track failed attempts by user
        if user_id:
            user_key = f"failed_reset:user:{user_id}"
            await client.incr(user_key)
            await client.expire(user_key, 3600)  # 1 hour
            
            user_count = int(await client.get(user_key) or 0)
        else:
            user_count = 0
        
        # Log if threshold exceeded
        if ip_count >= 10 or user_count >= 10:
            await log_suspicious_activity(
                db,
                identifier=ip_address,
                limit_type="ip",
                action="brute_force_attempt",
                details={
                    "failed_attempts_ip": ip_count,
                    "failed_attempts_user": user_count,
                    "threshold": 10,
                }
            )
            
    except Exception as e:
        logger.error(f"Failed to record failed attempt: {e}")


async def clear_failed_reset_attempts(
    ip_address: str,
    user_id: Optional[int] = None,
) -> None:
    """
    Clear failed reset attempts after successful reset.
    
    Args:
        ip_address: Client IP address
        user_id: User ID (if user exists)
    """
    try:
        client = await get_redis_client()
        
        # Clear IP-based counter
        ip_key = f"failed_reset:ip:{ip_address}"
        await client.delete(ip_key)
        
        # Clear user-based counter
        if user_id:
            user_key = f"failed_reset:user:{user_id}"
            await client.delete(user_key)
            
    except Exception as e:
        logger.error(f"Failed to clear failed attempts: {e}")
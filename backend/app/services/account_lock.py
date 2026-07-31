"""Account lock service for managing failed login attempts and account locking."""
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.models.user import User
from app.core.config import settings
from app.services.audit_log import create_audit_log
from app.core.request import get_client_ip, get_user_agent


# Configuration for account lock
MAX_FAILED_LOGIN_ATTEMPTS = 5
LOCK_DURATION_MINUTES = 30


class AccountLockService:
    """Service for managing account lock functionality."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def record_failed_login(self, user: User, request) -> None:
        """Record a failed login attempt and lock account if threshold reached."""
        user.failed_login_attempts += 1
        
        # Check if account should be locked
        if user.failed_login_attempts >= MAX_FAILED_LOGIN_ATTEMPTS:
            user.locked_until = datetime.utcnow() + timedelta(minutes=LOCK_DURATION_MINUTES)
            user.lock_reason = f"Account locked due to {MAX_FAILED_LOGIN_ATTEMPTS} failed login attempts"
            
            # Log account lock event
            await create_audit_log(
                self.db,
                action="account_locked",
                resource_type="user",
                resource_id=user.id,
                user_id=user.id,
                ip_address=get_client_ip(request),
                user_agent=get_user_agent(request),
                details={
                    "reason": user.lock_reason,
                    "failed_attempts": user.failed_login_attempts,
                    "locked_until": user.locked_until.isoformat(),
                },
            )
        
        await self.db.commit()
        await self.db.refresh(user)

    async def reset_failed_attempts(self, user: User) -> None:
        """Reset failed login attempts after successful login."""
        if user.failed_login_attempts > 0 or user.locked_until:
            user.failed_login_attempts = 0
            user.locked_until = None
            user.lock_reason = None
            await self.db.commit()
            await self.db.refresh(user)

    async def is_account_locked(self, user: User) -> tuple[bool, Optional[str]]:
        """Check if account is currently locked.
        
        Returns:
            tuple: (is_locked, reason)
        """
        if not user.locked_until:
            return False, None
        
        # Check if lock has expired
        if datetime.utcnow() > user.locked_until:
            # Auto-unlock expired accounts
            await self.reset_failed_attempts(user)
            return False, None
        
        return True, user.lock_reason

    async def unlock_account(self, user_id: int, request, unlocked_by: Optional[int] = None) -> User:
        """Manually unlock a user account (admin action)."""
        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        
        if not user:
            raise ValueError("User not found")
        
        if not user.locked_until:
            raise ValueError("Account is not locked")
        
        await self.reset_failed_attempts(user)
        
        # Log manual unlock
        await create_audit_log(
            self.db,
            action="account_unlocked",
            resource_type="user",
            resource_id=user_id,
            user_id=unlocked_by or user.id,
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request),
            details={
                "unlocked_by": unlocked_by,
                "previous_failed_attempts": user.failed_login_attempts,
            },
        )
        
        return user

    async def get_locked_accounts(self, skip: int = 0, limit: int = 20) -> list[User]:
        """Get list of currently locked accounts."""
        now = datetime.utcnow()
        result = await self.db.execute(
            select(User)
            .where(User.locked_until > now)
            .where(User.locked_until != None)
            .order_by(User.locked_until.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())
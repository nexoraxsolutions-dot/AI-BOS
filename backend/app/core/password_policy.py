"""
Enterprise password policy validation.

Enforces strong password requirements:
- Minimum 12 characters
- At least one uppercase letter
- At least one lowercase letter
- At least one digit
- At least one special character
- Not in common passwords list
- Not recently used (checked via password history)
"""
import re
import logging
from typing import Optional
from sqlalchemy import select

logger = logging.getLogger("ai_bos")

# Common weak passwords to reject
COMMON_PASSWORDS = {
    "password", "12345678", "qwerty123", "admin123", "letmein",
    "welcome1", "password1", "1234567890", "iloveyou", "sunshine",
    "princess", "football", "charlie", "access123", "master123",
    "monkey123", "dragon123", "login123", "passw0rd", "hello123",
    "password123", "123456789", "qwerty", "abc123", "password!",
    "1q2w3e4r", "qwertyuiop", "123456", "password12", "welcome",
    "admin", "letmein1", "123123", "welcome123", "monkey",
    "password123!", "Password123!",  # Added for testing common password detection
}

# Regex patterns for password complexity
PATTERNS = {
    "uppercase": re.compile(r'[A-Z]'),
    "lowercase": re.compile(r'[a-z]'),
    "digit": re.compile(r'[0-9]'),
    "special": re.compile(r'[!@#$%^&*()_+\-=\[\]{};\':"\\|,.<>\/?`~]'),
}


class PasswordValidationError(ValueError):
    """Raised when password validation fails."""
    def __init__(self, errors: list[str]):
        self.errors = errors
        super().__init__(self.format_errors())

    def format_errors(self) -> str:
        return "; ".join(self.errors)


def validate_password_strength(password: str) -> None:
    """
    Validate password meets enterprise strength requirements.

    Args:
        password: The password to validate

    Raises:
        PasswordValidationError: If password doesn't meet requirements
    """
    errors = []

    # Length check
    if len(password) < 12:
        errors.append(f"Password must be at least 12 characters long (currently {len(password)})")

    # Character type checks
    if not PATTERNS["uppercase"].search(password):
        errors.append("Password must contain at least one uppercase letter")

    if not PATTERNS["lowercase"].search(password):
        errors.append("Password must contain at least one lowercase letter")

    if not PATTERNS["digit"].search(password):
        errors.append("Password must contain at least one digit")

    if not PATTERNS["special"].search(password):
        errors.append("Password must contain at least one special character (!@#$%^&*()_+-=[]{}|;':\",./<>?)")

    # Common password check
    if password.lower() in COMMON_PASSWORDS:
        errors.append("Password is too common. Please choose a more unique password")

    if errors:
        raise PasswordValidationError(errors)


def is_common_password(password: str) -> bool:
    """Check if password is in the common passwords list."""
    return password.lower() in COMMON_PASSWORDS


async def validate_password_not_reused(
    password: str,
    user_id: int,
    db_session,
    history_limit: int = 5,
) -> None:
    """
    Validate that the password has not been used recently.

    Args:
        password: The new password to check
        user_id: The user's ID
        db_session: Database session (async)
        history_limit: Number of recent passwords to check (default: 5)

    Raises:
        PasswordValidationError: If password was used recently
    """
    from app.models.password_history import PasswordHistory
    from app.core.security import pwd_context

    # Get recent password history
    stmt = select(PasswordHistory).where(
        PasswordHistory.user_id == user_id
    ).order_by(PasswordHistory.created_at.desc()).limit(history_limit)

    result = await db_session.execute(stmt)
    recent_passwords = result.scalars().all()

    # Check if new password matches any recent password
    for history_entry in recent_passwords:
        if pwd_context.verify(password, history_entry.hashed_password):
            raise PasswordValidationError(
                [f"Password was used recently. Please choose a different password (cannot reuse last {history_limit} passwords)"]
            )


def get_password_requirements() -> dict:
    """Return password requirements for frontend display."""
    return {
        "min_length": 12,
        "require_uppercase": True,
        "require_lowercase": True,
        "require_digit": True,
        "require_special": True,
        "reject_common": True,
        "reject_recent": True,
    }

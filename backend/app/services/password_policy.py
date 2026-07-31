from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.organization_settings import OrganizationSettings
from app.core.password_policy import (
    validate_password_strength,
    is_common_password,
    validate_password_not_reused,
    PasswordValidationError,
)


class PasswordPolicyService:
    """Service for managing and enforcing password policies."""

    @staticmethod
    async def get_organization_policy(db: AsyncSession, company_id: int) -> Optional[Dict[str, Any]]:
        """Get password policy for an organization."""
        from app.services.organization_settings import get_organization_settings
        
        settings = await get_organization_settings(db, company_id)
        if not settings:
            return None
        
        return {
            "min_length": settings.password_min_length,
            "require_uppercase": settings.password_require_uppercase,
            "require_lowercase": settings.password_require_lowercase,
            "require_numbers": settings.password_require_numbers,
            "require_special_chars": settings.password_require_special_chars,
            "expiry_days": settings.password_expiry_days,
        }

    @staticmethod
    def get_default_policy() -> Dict[str, Any]:
        """Get default password policy."""
        return {
            "min_length": 12,
            "require_uppercase": True,
            "require_lowercase": True,
            "require_numbers": True,
            "require_special_chars": True,
            "expiry_days": 90,
        }

    @staticmethod
    async def validate_password(
        db: AsyncSession,
        user_id: int,
        password: str,
        company_id: int,
        check_history: bool = True,
        history_limit: int = 5,
    ) -> None:
        """
        Validate password against organization policy.
        
        Args:
            db: Database session
            user_id: User ID for history check
            password: Password to validate
            company_id: Company ID for policy lookup
            check_history: Whether to check password history
            history_limit: Number of recent passwords to check
            
        Raises:
            PasswordValidationError: If password doesn't meet policy requirements
        """
        # Get organization policy
        policy = await PasswordPolicyService.get_organization_policy(db, company_id)
        if not policy:
            # Use default policy if no organization settings found
            policy = PasswordPolicyService.get_default_policy()
        
        # Validate against policy
        PasswordPolicyService.validate_password_against_policy(password, policy)
        
        # Check password history if enabled
        if check_history:
            await validate_password_not_reused(
                password=password,
                user_id=user_id,
                db_session=db,
                history_limit=history_limit,
            )

    @staticmethod
    def validate_password_against_policy(password: str, policy: Dict[str, Any]) -> None:
        """
        Validate password against a specific policy.
        
        Args:
            password: Password to validate
            policy: Policy dictionary with requirements
            
        Raises:
            PasswordValidationError: If password doesn't meet policy requirements
        """
        errors = []
        
        # Length check
        min_length = policy.get("min_length", 12)
        if len(password) < min_length:
            errors.append(f"Password must be at least {min_length} characters long (currently {len(password)})")
        
        # Character type checks
        if policy.get("require_uppercase", True):
            import re
            if not re.search(r'[A-Z]', password):
                errors.append("Password must contain at least one uppercase letter")
        
        if policy.get("require_lowercase", True):
            import re
            if not re.search(r'[a-z]', password):
                errors.append("Password must contain at least one lowercase letter")
        
        if policy.get("require_numbers", True):
            import re
            if not re.search(r'[0-9]', password):
                errors.append("Password must contain at least one digit")
        
        if policy.get("require_special_chars", True):
            import re
            if not re.search(r'[!@#$%^&*()_+\-=\[\]{};\':"\\|,.<>\/?`~]', password):
                errors.append("Password must contain at least one special character (!@#$%^&*()_+-=[]{}|;':\",./<>?)")
        
        # Common password check
        if is_common_password(password):
            errors.append("Password is too common. Please choose a more unique password")
        
        if errors:
            raise PasswordValidationError(errors)

    @staticmethod
    def get_password_requirements_display(company_id: int, policy: Optional[Dict[str, Any]] = None) -> list[Dict[str, Any]]:
        """
        Get password requirements for frontend display.
        
        Args:
            company_id: Company ID (used if policy not provided)
            policy: Optional policy dictionary
            
        Returns:
            List of requirement dictionaries for UI display
        """
        if policy is None:
            policy = PasswordPolicyService.get_default_policy()
        
        requirements = [
            {
                "id": "length",
                "label": f"At least {policy.get('min_length', 12)} characters",
                "key": "min_length",
                "value": policy.get("min_length", 12),
            },
            {
                "id": "uppercase",
                "label": "At least one uppercase letter (A-Z)",
                "key": "require_uppercase",
                "value": policy.get("require_uppercase", True),
            },
            {
                "id": "lowercase",
                "label": "At least one lowercase letter (a-z)",
                "key": "require_lowercase",
                "value": policy.get("require_lowercase", True),
            },
            {
                "id": "numbers",
                "label": "At least one number (0-9)",
                "key": "require_numbers",
                "value": policy.get("require_numbers", True),
            },
            {
                "id": "special",
                "label": "At least one special character (!@#$%^&*)",
                "key": "require_special_chars",
                "value": policy.get("require_special_chars", True),
            },
        ]
        
        return requirements

    @staticmethod
    def check_password_against_requirements(password: str, requirements: list[Dict[str, Any]]) -> Dict[str, bool]:
        """
        Check password against requirements and return status of each.
        
        Args:
            password: Password to check
            requirements: List of requirement dictionaries
            
        Returns:
            Dictionary mapping requirement ID to boolean (met or not)
        """
        import re
        
        results = {}
        
        for req in requirements:
            req_id = req["id"]
            req_value = req["value"]
            
            if req_id == "length":
                results[req_id] = len(password) >= req_value
            elif req_id == "uppercase":
                results[req_id] = bool(re.search(r'[A-Z]', password)) if req_value else True
            elif req_id == "lowercase":
                results[req_id] = bool(re.search(r'[a-z]', password)) if req_value else True
            elif req_id == "numbers":
                results[req_id] = bool(re.search(r'[0-9]', password)) if req_value else True
            elif req_id == "special":
                results[req_id] = bool(re.search(r'[!@#$%^&*()_+\-=\[\]{};\':"\\|,.<>\/?`~]', password)) if req_value else True
            else:
                results[req_id] = True
        
        return results
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_active_user, require_superuser
from app.db.dependencies import get_async_session
from app.models.user import User
from app.schemas.security_dashboard import SecurityDashboardResponse
from app.services.security_dashboard import get_security_dashboard_data

router = APIRouter()


@router.get("/summary", response_model=SecurityDashboardResponse)
async def get_security_summary(
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(require_superuser),
):
    """Get comprehensive security dashboard summary. Superuser only."""
    try:
        data = await get_security_dashboard_data(db)
        return SecurityDashboardResponse(**data)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve security dashboard data: {str(e)}"
        )


@router.get("/score", response_model=dict)
async def get_security_score(
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(require_superuser),
):
    """Get current security score. Superuser only."""
    try:
        data = await get_security_dashboard_data(db)
        return {
            "security_score": data["security_score"],
            "recommendations": _generate_security_recommendations(data)
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve security score: {str(e)}"
        )


def _generate_security_recommendations(data: dict) -> list[str]:
    """Generate security recommendations based on current metrics."""
    recommendations = []
    
    # Check 2FA adoption
    if data["total_users"] > 0:
        two_fa_rate = (data["users_with_2fa"] / data["total_users"]) * 100
        if two_fa_rate < 50:
            recommendations.append(
                f"Enable 2FA for more users. Current adoption rate: {two_fa_rate:.1f}%"
            )
    
    # Check for locked accounts
    if data["locked_accounts"] > 0:
        recommendations.append(
            f"Review {data['locked_accounts']} locked accounts and unlock if appropriate"
        )
    
    # Check for suspicious activities
    if data["suspicious_ips_count"] > 0:
        recommendations.append(
            f"Investigate {data['suspicious_ips_count']} IP addresses with suspicious activity"
        )
    
    # Check failed login rate
    if data["failed_logins_24h"] > 10:
        recommendations.append(
            f"High number of failed login attempts in last 24h: {data['failed_logins_24h']}"
        )
    
    if not recommendations:
        recommendations.append("Security posture looks good. Continue monitoring.")
    
    return recommendations
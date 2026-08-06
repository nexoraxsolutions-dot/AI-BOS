"""Company invitation service.

Implements the full invitation lifecycle:
- Generating a secure, single-use invitation token (stored hashed)
- Creating pending invitations with an expiration
- Looking up invitations by token
- Accepting invitations (creates a company membership)
- Rejecting invitations
"""
import secrets
from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import pwd_context
from app.models.company import Company
from app.models.membership import CompanyInvitation, CompanyMembership
from app.models.user import User
from app.services.cache import cache_service
from app.services.onboarding import is_company_member

INVITE_STATUS_PENDING = "pending"
INVITE_STATUS_ACCEPTED = "accepted"
INVITE_STATUS_REJECTED = "rejected"
INVITE_STATUS_EXPIRED = "expired"


def generate_invitation_token() -> str:
    """Generate a secure, random invitation token."""
    return secrets.token_urlsafe(32)


def hash_invitation_token(token: str) -> str:
    """Hash an invitation token for secure storage."""
    return pwd_context.hash(token)


async def get_invitation_by_token(db: AsyncSession, token: str):
    """Retrieve an invitation by its plaintext token.

    The token is stored hashed, so pending invitations are scanned and their
    hashes compared. For very large invitation volumes you can instead store a
    deterministic SHA-256 digest of the token for direct lookup.
    """
    result = await db.execute(
        select(CompanyInvitation).where(
            CompanyInvitation.status == INVITE_STATUS_PENDING
        )
    )
    invitation = None
    for candidate in result.scalars().all():
        if pwd_context.verify(token, candidate.token_hash):
            invitation = candidate
            break
    return invitation


async def invite_user_to_company(
    db: AsyncSession,
    company_id: int,
    inviter: User,
    email: str,
    role: str = "member",
) -> tuple:
    """Create a pending invitation for ``email`` to join ``company_id``.

    Returns (invitation, plaintext_token).
    """
    email = email.strip().lower()

    company_result = await db.execute(select(Company).where(Company.id == company_id))
    company = company_result.scalar_one_or_none()
    if not company or not company.is_active:
        raise ValueError("Company not found or inactive")

    if not await is_company_member(db, inviter, company_id):
        raise ValueError("You are not a member of this company")

    # Check invitee is not already a member
    user_result = await db.execute(select(User).where(User.email == email))
    existing = user_result.scalar_one_or_none()
    if existing and await is_company_member(db, existing, company_id):
        raise ValueError("This user is already a member of the company")

    # Reject an already-active pending invitation for same email+company
    dup = await db.execute(
        select(CompanyInvitation).where(
            CompanyInvitation.company_id == company_id,
            CompanyInvitation.email == email,
            CompanyInvitation.status == INVITE_STATUS_PENDING,
        )
    )
    if dup.scalar_one_or_none():
        raise ValueError("An invitation is already pending for this email")

    token = generate_invitation_token()
    invitation = CompanyInvitation(
        company_id=company_id,
        email=email,
        token_hash=hash_invitation_token(token),
        role=role or "member",
        invited_by_id=inviter.id,
        status=INVITE_STATUS_PENDING,
        expires_at=datetime.utcnow()
        + timedelta(hours=settings.company_invitation_expire_hours),
    )
    db.add(invitation)
    await db.commit()
    await db.refresh(invitation)

    await cache_service.delete(f"tenant:{company_id}:details")
    return invitation, token


async def accept_invitation(db: AsyncSession, user: User, invitation: CompanyInvitation):
    """Accept an invitation and add the user as a member of the company."""
    if invitation.status != INVITE_STATUS_PENDING:
        raise ValueError("Invitation is no longer pending")

    if invitation.expires_at and datetime.utcnow() > invitation.expires_at:
        invitation.status = INVITE_STATUS_EXPIRED
        await db.commit()
        raise ValueError("Invitation has expired")

    if invitation.email.lower() != user.email.lower():
        raise ValueError("Invitation was not issued to this email address")

    try:
        existing = await db.execute(
            select(CompanyMembership).where(
                CompanyMembership.user_id == user.id,
                CompanyMembership.company_id == invitation.company_id,
            )
        )
        if not existing.scalar_one_or_none():
            membership = CompanyMembership(
                user_id=user.id,
                company_id=invitation.company_id,
                role=invitation.role or "member",
                is_active=True,
            )
            db.add(membership)

        # Make it the user's primary/active company if they had none.
        if user.company_id is None:
            user.company_id = invitation.company_id
        user.active_company_id = invitation.company_id

        invitation.status = INVITE_STATUS_ACCEPTED
        invitation.accepted_at = datetime.utcnow()
        await db.commit()
        await db.refresh(invitation)
    except Exception:
        await db.rollback()
        raise

    await cache_service.delete(f"user:{user.id}")
    await cache_service.delete(f"tenant:{invitation.company_id}:details")
    await cache_service.delete_pattern("users:list:*")
    return invitation


async def reject_invitation(db: AsyncSession, user: User, invitation: CompanyInvitation):
    """Reject an invitation."""
    if invitation.status != INVITE_STATUS_PENDING:
        raise ValueError("Invitation is no longer pending")

    invitation.status = INVITE_STATUS_REJECTED
    invitation.rejected_at = datetime.utcnow()
    await db.commit()
    await db.refresh(invitation)
    await cache_service.delete(f"tenant:{invitation.company_id}:details")
    return invitation

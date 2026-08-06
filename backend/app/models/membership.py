"""Multi-company membership and invitation models.

Implements:
- CompanyMembership: Many-to-many relationship between users and companies,
  allowing a user to belong to (and switch between) multiple companies.
- CompanyInvitation: Tokenized invitations that let users join a company.

These models power company onboarding, invites, and company switching without
breaking the existing single ``user.company_id`` primary company reference —
``company_id`` remains the user's primary/initial company while memberships
track additional/active companies.
"""
from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.db import Base


class CompanyMembership(Base):
    """Association between a user and a company they belong to."""

    __tablename__ = "company_memberships"
    __table_args__ = (
        UniqueConstraint("user_id", "company_id", name="uq_user_company_membership"),
    )

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(String(50), default="member", nullable=False)
    is_active = Column(Boolean, default=True)
    joined_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="memberships")
    company = relationship("Company", back_populates="memberships")


class CompanyInvitation(Base):
    """An invitation for a user to join a company."""

    __tablename__ = "company_invitations"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    email = Column(String, nullable=False, index=True)
    token_hash = Column(String, nullable=False, index=True)
    role = Column(String(50), default="member", nullable=False)
    invited_by_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    status = Column(String(20), default="pending", nullable=False, index=True)  # pending/accepted/rejected/expired
    expires_at = Column(DateTime, nullable=False, index=True)
    accepted_at = Column(DateTime, nullable=True)
    rejected_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    company = relationship("Company", back_populates="invitations")
    invited_by = relationship("User", foreign_keys=[invited_by_id])
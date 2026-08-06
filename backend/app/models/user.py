from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Integer
from sqlalchemy.orm import relationship

from app.db import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    username = Column(String(50), unique=True, nullable=True, index=True)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    is_email_verified = Column(Boolean, default=False)
    email_verification_token = Column(String, nullable=True)
    is_2fa_enabled = Column(Boolean, default=False)
    otp_secret = Column(String, nullable=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Account lock fields
    failed_login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime, nullable=True)
    lock_reason = Column(String, nullable=True)

    company = relationship("Company", back_populates="users")
    
    tokens = relationship(
        "Token",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    sessions = relationship(
        "UserSession",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    password_reset_tokens = relationship(
        "PasswordResetToken",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    password_history = relationship(
        "PasswordHistory",
        back_populates="user",
        cascade="all, delete-orphan",
        order_by="desc(PasswordHistory.created_at)",
    )
    backup_codes = relationship(
        "TwoFactorBackupCode",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    user_roles = relationship(
    "UserRole",
    back_populates="user",
    cascade="all, delete-orphan",
    foreign_keys="UserRole.user_id",
    )
    
    managed_departments = relationship(
    "Department",
    back_populates="manager",
    foreign_keys="Department.manager_id",
    )

    api_keys = relationship(
        "ApiKey",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    
    created_test_suites = relationship(
        "TestSuite",
        back_populates="created_by",
        cascade="all, delete-orphan",
    )
    
    test_runs = relationship(
        "TestRun",
        back_populates="triggered_by_user",
        cascade="all, delete-orphan",
    )


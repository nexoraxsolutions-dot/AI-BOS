from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON
from sqlalchemy.orm import relationship
from sqlalchemy import ForeignKey

from app.db import Base


class OrganizationSettings(Base):
    __tablename__ = "organization_settings"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), unique=True, nullable=False, index=True)
    
    # Localization
    timezone = Column(String, default="UTC")
    date_format = Column(String, default="YYYY-MM-DD")
    time_format = Column(String, default="24h")
    language = Column(String, default="en")
    currency = Column(String, default="USD")
    
    # Security settings
    password_min_length = Column(Integer, default=8)
    password_require_uppercase = Column(Boolean, default=True)
    password_require_lowercase = Column(Boolean, default=True)
    password_require_numbers = Column(Boolean, default=True)
    password_require_special_chars = Column(Boolean, default=True)
    password_expiry_days = Column(Integer, default=90)
    session_timeout_minutes = Column(Integer, default=60)
    enforce_2fa = Column(Boolean, default=False)
    max_login_attempts = Column(Integer, default=5)
    
    # Notification settings
    email_notifications_enabled = Column(Boolean, default=True)
    notify_on_user_creation = Column(Boolean, default=True)
    notify_on_user_deletion = Column(Boolean, default=True)
    notify_on_password_reset = Column(Boolean, default=True)
    notify_on_security_alerts = Column(Boolean, default=True)
    notify_on_subscription_changes = Column(Boolean, default=True)
    
    # Branding settings
    primary_color = Column(String, default="#06b6d4")
    logo_url = Column(String, nullable=True)
    custom_css = Column(Text, nullable=True)
    
    # Feature flags
    enable_user_registration = Column(Boolean, default=True)
    enable_api_access = Column(Boolean, default=True)
    enable_audit_logs = Column(Boolean, default=True)
    enable_data_export = Column(Boolean, default=True)
    
    # Custom settings (JSON for extensibility)
    custom_settings = Column(JSON, nullable=True, default=dict)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship
    company = relationship("Company", backref="organization_settings")
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship

from app.db import Base


class LoggingConfiguration(Base):
    """Model for logging configuration settings.

    Stores organization-level logging configuration including
    log level, enabled handlers, format, and retention settings.
    """

    __tablename__ = "logging_configurations"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, nullable=False, unique=True, index=True)

    # Log level configuration
    log_level = Column(String(20), nullable=False, default="INFO")  # DEBUG, INFO, WARNING, ERROR, CRITICAL

    # Handler configuration
    enable_database_logging = Column(Boolean, nullable=False, default=True)
    enable_console_logging = Column(Boolean, nullable=False, default=True)

    # Format configuration
    log_format = Column(String(50), nullable=False, default="text")  # text, json

    # Retention configuration
    retention_days = Column(Integer, nullable=False, default=90)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

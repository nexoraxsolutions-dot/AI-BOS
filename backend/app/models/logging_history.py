from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship

from app.db import Base


class LogEntry(Base):
    """Model for persisted application/system log entries.

    Stores structured log records captured by the DatabaseLogHandler
    so that administrators can review historical application logs
    (errors, warnings, info, etc.) through the REST API and frontend UI.
    """

    __tablename__ = "log_entries"

    id = Column(Integer, primary_key=True, index=True)
    level = Column(String(20), nullable=False, index=True)
    logger_name = Column(String(255), nullable=False, index=True)
    message = Column(Text, nullable=False)
    module = Column(String(255), nullable=True)
    func_name = Column(String(255), nullable=True)
    line_no = Column(Integer, nullable=True)
    pathname = Column(String(500), nullable=True)
    thread_name = Column(String(255), nullable=True)
    process = Column(String(50), nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    extra_data = Column(JSON, nullable=True)

    user = relationship("User", backref="log_entries")

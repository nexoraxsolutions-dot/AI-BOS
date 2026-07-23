from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship

from app.db import Base


class EnvironmentVariable(Base):
    __tablename__ = "environment_variables"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(255), nullable=False, index=True)
    value = Column(Text, nullable=False)
    description = Column(String(500), nullable=True)
    is_secret = Column(Boolean, default=False)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    company = relationship("Company", backref="environment_variables")

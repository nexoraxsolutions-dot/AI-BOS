from datetime import datetime

from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship

from app.db import Base


class Document(Base):
    """A documentation / knowledge-base article.

    Belongs to a company (multi-tenant) and an author, supports versioning and
    lifecycle states (draft -> published -> archived).
    """

    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False, index=True)
    slug = Column(String(255), nullable=True, index=True)
    summary = Column(Text, nullable=True)
    content = Column(Text, nullable=True)
    category = Column(String(100), default="general", index=True)
    tags = Column(Text, nullable=True)  # Comma-separated tags
    status = Column(String(50), default="draft", index=True)
    version = Column(Integer, default=1)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=True, index=True)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    company = relationship("Company", back_populates="documents")
    author = relationship("User", foreign_keys=[author_id])

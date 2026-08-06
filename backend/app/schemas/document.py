from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator
from typing import Optional, Dict, List

VALID_STATUSES = {"draft", "published", "archived"}


class DocumentBase(BaseModel):
    title: str
    slug: Optional[str] = None
    summary: Optional[str] = None
    content: Optional[str] = None
    category: Optional[str] = "general"
    tags: Optional[str] = None
    status: Optional[str] = "draft"
    company_id: Optional[int] = None

    @field_validator("title")
    @classmethod
    def validate_title(cls, v):
        if not v or len(v.strip()) < 3:
            raise ValueError("Document title must be at least 3 characters long")
        if len(v) > 255:
            raise ValueError("Document title must not exceed 255 characters")
        return v.strip()

    @field_validator("category")
    @classmethod
    def validate_category(cls, v):
        if v is None:
            return v
        v = v.strip()
        if len(v) > 100:
            raise ValueError("Category must not exceed 100 characters")
        return v

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, v):
        if v is not None and v.strip():
            import re
            v = v.strip().lower()
            if not re.match(r"^[a-z0-9]+(?:-[a-z0-9]+)*$", v):
                raise ValueError(
                    "Slug must contain only lowercase letters, numbers, and hyphens"
                )
            if len(v) > 255:
                raise ValueError("Slug must not exceed 255 characters")
            return v
        return v

    @field_validator("status")
    @classmethod
    def validate_status(cls, v):
        if v is not None:
            v = v.strip().lower()
            if v not in VALID_STATUSES:
                raise ValueError(f"Status must be one of: {', '.join(sorted(VALID_STATUSES))}")
            return v
        return v


class DocumentCreate(DocumentBase):
    pass


class DocumentUpdate(BaseModel):
    title: Optional[str] = None
    slug: Optional[str] = None
    summary: Optional[str] = None
    content: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[str] = None
    status: Optional[str] = None
    company_id: Optional[int] = None
    is_active: Optional[bool] = None

    @field_validator("title")
    @classmethod
    def validate_title(cls, v):
        if v is not None:
            v = v.strip()
            if len(v) < 3:
                raise ValueError("Document title must be at least 3 characters long")
            if len(v) > 255:
                raise ValueError("Document title must not exceed 255 characters")
            return v
        return v

    @field_validator("category")
    @classmethod
    def validate_category(cls, v):
        if v is not None and v.strip():
            v = v.strip()
            if len(v) > 100:
                raise ValueError("Category must not exceed 100 characters")
            return v
        return v

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, v):
        if v is not None and v.strip():
            import re
            v = v.strip().lower()
            if not re.match(r"^[a-z0-9]+(?:-[a-z0-9]+)*$", v):
                raise ValueError(
                    "Slug must contain only lowercase letters, numbers, and hyphens"
                )
            if len(v) > 255:
                raise ValueError("Slug must not exceed 255 characters")
            return v
        return v

    @field_validator("status")
    @classmethod
    def validate_status(cls, v):
        if v is not None:
            v = v.strip().lower()
            if v not in VALID_STATUSES:
                raise ValueError(f"Status must be one of: {', '.join(sorted(VALID_STATUSES))}")
            return v
        return v


class DocumentOut(DocumentBase):
    id: int
    version: Optional[int] = None
    author_id: Optional[int] = None
    is_active: Optional[bool] = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    author_name: Optional[str] = None
    company_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class DocumentListResponse(BaseModel):
    items: List[DocumentOut]
    total: int
    page: int
    page_size: int


class DocumentStats(BaseModel):
    total_documents: int
    published_documents: int
    draft_documents: int
    archived_documents: int
    total_companies_with_documents: int
    avg_documents_per_company: Optional[float] = None
    documents_by_category: Dict[str, int]
    documents_by_status: Dict[str, int]

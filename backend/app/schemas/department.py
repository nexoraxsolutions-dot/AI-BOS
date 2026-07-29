from pydantic import BaseModel, field_validator, ConfigDict
from typing import Optional, Dict, Any, List
from datetime import datetime
import re


class DepartmentBase(BaseModel):
    name: str
    description: Optional[str] = None
    company_id: int
    manager_id: Optional[int] = None
    budget: Optional[str] = None
    location: Optional[str] = None
    is_active: Optional[bool] = True

    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        if not v or len(v.strip()) < 2:
            raise ValueError('Department name must be at least 2 characters long')
        if len(v) > 100:
            raise ValueError('Department name must not exceed 100 characters')
        return v.strip()

    @field_validator('budget')
    @classmethod
    def validate_budget(cls, v):
        if v is not None and v.strip():
            # Allow formats like: $100,000, 100000, $100K, etc.
            if not re.match(r'^[\$]?[\d,]+(\.\d{2})?(\s*[KMB])?$', v.strip()):
                raise ValueError('Invalid budget format. Use formats like $100,000 or 100K')
            return v.strip()
        return v

    @field_validator('location')
    @classmethod
    def validate_location(cls, v):
        if v is not None and v.strip():
            if len(v.strip()) > 255:
                raise ValueError('Location must not exceed 255 characters')
            return v.strip()
        return v


class DepartmentCreate(DepartmentBase):
    pass


class DepartmentUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    manager_id: Optional[int] = None
    budget: Optional[str] = None
    location: Optional[str] = None
    is_active: Optional[bool] = None

    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        if v is not None:
            if len(v.strip()) < 2:
                raise ValueError('Department name must be at least 2 characters long')
            if len(v) > 100:
                raise ValueError('Department name must not exceed 100 characters')
            return v.strip()
        return v

    @field_validator('budget')
    @classmethod
    def validate_budget(cls, v):
        if v is not None and v.strip():
            if not re.match(r'^[\$]?[\d,]+(\.\d{2})?(\s*[KMB])?$', v.strip()):
                raise ValueError('Invalid budget format. Use formats like $100,000 or 100K')
            return v.strip()
        return v

    @field_validator('location')
    @classmethod
    def validate_location(cls, v):
        if v is not None and v.strip():
            if len(v.strip()) > 255:
                raise ValueError('Location must not exceed 255 characters')
            return v.strip()
        return v


class DepartmentOut(DepartmentBase):
    id: int
    company_id: int
    manager_id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    manager_name: Optional[str] = None
    company_name: Optional[str] = None
    employee_count: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


class DepartmentStats(BaseModel):
    total_departments: int
    active_departments: int
    inactive_departments: int
    total_companies_with_departments: int
    avg_departments_per_company: Optional[float] = None
    departments_by_company: Dict[str, int]


class DepartmentListResponse(BaseModel):
    items: List[DepartmentOut]
    total: int
    page: int
    page_size: int
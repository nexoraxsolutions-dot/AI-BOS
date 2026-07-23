from pydantic import BaseModel, field_validator, ConfigDict
from typing import Optional, Dict, Any
from datetime import datetime
import re


class CompanyBase(BaseModel):
    name: str
    domain: str
    description: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    logo_url: Optional[str] = None
    tax_id: Optional[str] = None
    industry: Optional[str] = None
    employee_count: Optional[int] = None
    subscription_plan: Optional[str] = "free"
    subscription_status: Optional[str] = "active"
    subscription_expires_at: Optional[datetime] = None
    settings: Optional[Dict[str, Any]] = None

    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        if not v or len(v.strip()) < 2:
            raise ValueError('Company name must be at least 2 characters long')
        return v.strip()

    @field_validator('domain')
    @classmethod
    def validate_domain(cls, v):
        # Allow domains like example.com, test-company.com, etc.
        if not re.match(r'^[a-zA-Z0-9][a-zA-Z0-9-]*[a-zA-Z0-9](\.[a-zA-Z0-9][a-zA-Z0-9-]*[a-zA-Z0-9])*$', v):
            raise ValueError('Invalid domain format')
        return v.lower()

    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v):
        if v is not None and v.strip():
            if not re.match(r'^\+?[\d\s\-\(\)]{7,20}$', v):
                raise ValueError('Invalid phone number format')
            return v.strip()
        return v

    @field_validator('email')
    @classmethod
    def validate_company_email(cls, v):
        if v is not None and v.strip():
            if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', v):
                raise ValueError('Invalid email format')
            return v.strip()
        return v

    @field_validator('website')
    @classmethod
    def validate_website(cls, v):
        if v is not None and v.strip():
            if not re.match(r'^https?://[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', v):
                raise ValueError('Invalid website URL format (must start with http:// or https://)')
            return v.strip()
        return v

    @field_validator('employee_count')
    @classmethod
    def validate_employee_count(cls, v):
        if v is not None and v < 0:
            raise ValueError('Employee count cannot be negative')
        return v

    @field_validator('subscription_plan')
    @classmethod
    def validate_subscription_plan(cls, v):
        if v is not None:
            valid_plans = ['free', 'starter', 'professional', 'enterprise', 'custom']
            if v.lower() not in valid_plans:
                raise ValueError(f'Invalid subscription plan. Must be one of: {", ".join(valid_plans)}')
            return v.lower()
        return v

    @field_validator('subscription_status')
    @classmethod
    def validate_subscription_status(cls, v):
        if v is not None:
            valid_statuses = ['active', 'inactive', 'trialing', 'canceled', 'past_due', 'expired']
            if v.lower() not in valid_statuses:
                raise ValueError(f'Invalid subscription status. Must be one of: {", ".join(valid_statuses)}')
            return v.lower()
        return v


class CompanyCreate(CompanyBase):
    pass


class CompanyUpdate(BaseModel):
    name: Optional[str] = None
    domain: Optional[str] = None
    description: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    logo_url: Optional[str] = None
    tax_id: Optional[str] = None
    industry: Optional[str] = None
    employee_count: Optional[int] = None
    is_active: Optional[bool] = None
    subscription_plan: Optional[str] = None
    subscription_status: Optional[str] = None
    subscription_expires_at: Optional[datetime] = None
    settings: Optional[Dict[str, Any]] = None

    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        if v is not None and (len(v.strip()) < 2):
            raise ValueError('Company name must be at least 2 characters long')
        return v.strip() if v else v

    @field_validator('domain')
    @classmethod
    def validate_domain(cls, v):
        if v is not None:
            if not re.match(r'^[a-zA-Z0-9][a-zA-Z0-9-]*[a-zA-Z0-9](\.[a-zA-Z0-9][a-zA-Z0-9-]*[a-zA-Z0-9])*$', v):
                raise ValueError('Invalid domain format')
            return v.lower()
        return v

    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v):
        if v is not None and v.strip():
            if not re.match(r'^\+?[\d\s\-\(\)]{7,20}$', v):
                raise ValueError('Invalid phone number format')
            return v.strip()
        return v

    @field_validator('email')
    @classmethod
    def validate_company_email(cls, v):
        if v is not None and v.strip():
            if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', v):
                raise ValueError('Invalid email format')
            return v.strip()
        return v

    @field_validator('website')
    @classmethod
    def validate_website(cls, v):
        if v is not None and v.strip():
            if not re.match(r'^https?://[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', v):
                raise ValueError('Invalid website URL format (must start with http:// or https://)')
            return v.strip()
        return v

    @field_validator('employee_count')
    @classmethod
    def validate_employee_count(cls, v):
        if v is not None and v < 0:
            raise ValueError('Employee count cannot be negative')
        return v

    @field_validator('subscription_plan')
    @classmethod
    def validate_subscription_plan(cls, v):
        if v is not None:
            valid_plans = ['free', 'starter', 'professional', 'enterprise', 'custom']
            if v.lower() not in valid_plans:
                raise ValueError(f'Invalid subscription plan. Must be one of: {", ".join(valid_plans)}')
            return v.lower()
        return v

    @field_validator('subscription_status')
    @classmethod
    def validate_subscription_status(cls, v):
        if v is not None:
            valid_statuses = ['active', 'inactive', 'trialing', 'canceled', 'past_due', 'expired']
            if v.lower() not in valid_statuses:
                raise ValueError(f'Invalid subscription status. Must be one of: {", ".join(valid_statuses)}')
            return v.lower()
        return v


class CompanyOut(CompanyBase):
    id: int
    is_active: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    user_count: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


class CompanyStats(BaseModel):
    total_companies: int
    active_companies: int
    inactive_companies: int
    total_users_across_companies: int
    avg_employees: Optional[float] = None
    plan_distribution: Dict[str, int]


class CompanyListResponse(BaseModel):
    items: list[CompanyOut]
    total: int
    page: int
    page_size: int
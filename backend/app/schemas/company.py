from pydantic import BaseModel, field_validator, ConfigDict
from typing import Optional
import re


class CompanyBase(BaseModel):
    name: str
    domain: str

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


class CompanyCreate(CompanyBase):
    pass


class CompanyUpdate(BaseModel):
    name: Optional[str] = None
    domain: Optional[str] = None
    is_active: Optional[bool] = None

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


class CompanyOut(CompanyBase):
    id: int
    is_active: bool

    model_config = ConfigDict(from_attributes=True)
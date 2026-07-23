from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app.db.dependencies import get_async_session
from app.schemas import environment_variable as env_var_schema
from app.services import environment_variable as env_var_service
from app.core.security import get_current_active_user, require_superuser
from app.core.tenant import TenantContext, get_tenant_context

def _mask_secret_value(value: str) -> str:
    """Mask a secret value, showing first 4 and last 4 characters."""
    if len(value) <= 8:
        return "*" * 8
    return value[:4] + "*" * (len(value) - 8) + value[-4:]

router = APIRouter()


def _get_company_id_for_env_vars(tenant: TenantContext) -> Optional[int]:
    """Get the company_id to scope environment variable queries.
    
    Superusers (without company) can see all. Regular users see only their company's.
    """
    if tenant.is_superuser and not tenant.company_id:
        return None  # Superuser can see all
    return tenant.company_id


@router.post("/", response_model=env_var_schema.EnvironmentVariableOut, status_code=status.HTTP_201_CREATED)
async def create_environment_variable(
    payload: env_var_schema.EnvironmentVariableCreate,
    db: AsyncSession = Depends(get_async_session),
    current_user=Depends(require_superuser),
):
    """Create a new environment variable."""
    # Check if key already exists
    existing = await env_var_service.get_environment_variable_by_key(db, payload.key)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Environment variable with key '{payload.key}' already exists"
        )
    return await env_var_service.create_environment_variable(db, payload)


@router.get("/", response_model=List[env_var_schema.EnvironmentVariableOut])
async def list_environment_variables(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=500, description="Number of records to return"),
    search: Optional[str] = Query(None, description="Search by key or description"),
    db: AsyncSession = Depends(get_async_session),
    tenant: TenantContext = Depends(get_tenant_context),
):
    """List environment variables, scoped to user's company."""
    company_id = _get_company_id_for_env_vars(tenant)
    env_vars, total = await env_var_service.get_environment_variables(
        db, skip=skip, limit=limit, search=search, company_id=company_id
    )
    
    # Build response with masked secrets
    result = []
    for env_var in env_vars:
        masked_value = _mask_secret_value(env_var.value) if env_var.is_secret else None
        env_dict = {
            "id": env_var.id,
            "key": env_var.key,
            "value": env_var.value if not env_var.is_secret else None,
            "masked_value": masked_value,
            "description": env_var.description,
            "is_secret": env_var.is_secret,
            "company_id": env_var.company_id,
            "created_at": env_var.created_at,
            "updated_at": env_var.updated_at,
        }
        result.append(env_dict)
    
    return result


@router.get("/{env_var_id}", response_model=env_var_schema.EnvironmentVariableOut)
async def get_environment_variable(
    env_var_id: int,
    db: AsyncSession = Depends(get_async_session),
    tenant: TenantContext = Depends(get_tenant_context),
):
    """Get a specific environment variable by ID, scoped to company."""
    company_id = _get_company_id_for_env_vars(tenant)
    env_var = await env_var_service.get_environment_variable(db, env_var_id, company_id=company_id)
    if not env_var:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Environment variable not found"
        )
    
    masked_value = _mask_secret_value(env_var.value) if env_var.is_secret else None
    return {
        "id": env_var.id,
        "key": env_var.key,
        "value": env_var.value if not env_var.is_secret else None,
        "masked_value": masked_value,
        "description": env_var.description,
        "is_secret": env_var.is_secret,
        "company_id": env_var.company_id,
        "created_at": env_var.created_at,
        "updated_at": env_var.updated_at,
    }


@router.get("/key/{key}", response_model=env_var_schema.EnvironmentVariableOut)
async def get_environment_variable_by_key(
    key: str,
    db: AsyncSession = Depends(get_async_session),
    tenant: TenantContext = Depends(get_tenant_context),
):
    """Get a specific environment variable by key, scoped to company."""
    company_id = _get_company_id_for_env_vars(tenant)
    env_var = await env_var_service.get_environment_variable_by_key(db, key, company_id=company_id)
    if not env_var:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Environment variable not found"
        )
    
    return {
        "id": env_var.id,
        "key": env_var.key,
        "value": env_var.value if not env_var.is_secret else None,
        "masked_value": env_var.masked_value if env_var.is_secret else None,
        "description": env_var.description,
        "is_secret": env_var.is_secret,
        "company_id": env_var.company_id,
        "created_at": env_var.created_at,
        "updated_at": env_var.updated_at,
    }


@router.put("/{env_var_id}", response_model=env_var_schema.EnvironmentVariableOut)
async def update_environment_variable(
    env_var_id: int,
    payload: env_var_schema.EnvironmentVariableUpdate,
    db: AsyncSession = Depends(get_async_session),
    tenant: TenantContext = Depends(get_tenant_context),
):
    """Update an environment variable, scoped to company."""
    company_id = _get_company_id_for_env_vars(tenant)
    env_var = await env_var_service.update_environment_variable(db, env_var_id, payload, company_id=company_id)
    if not env_var:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Environment variable not found or access denied"
        )
    
    masked_value = _mask_secret_value(env_var.value) if env_var.is_secret else None
    return {
        "id": env_var.id,
        "key": env_var.key,
        "value": env_var.value if not env_var.is_secret else None,
        "masked_value": masked_value,
        "description": env_var.description,
        "is_secret": env_var.is_secret,
        "company_id": env_var.company_id,
        "created_at": env_var.created_at,
        "updated_at": env_var.updated_at,
    }


@router.delete("/{env_var_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_environment_variable(
    env_var_id: int,
    db: AsyncSession = Depends(get_async_session),
    tenant: TenantContext = Depends(get_tenant_context),
):
    """Delete an environment variable, scoped to company."""
    company_id = _get_company_id_for_env_vars(tenant)
    deleted = await env_var_service.delete_environment_variable(db, env_var_id, company_id=company_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Environment variable not found or access denied"
        )
    return None


@router.get("/export/.env", response_model=dict)
async def export_environment_variables(
    db: AsyncSession = Depends(get_async_session),
    tenant: TenantContext = Depends(get_tenant_context),
):
    """Export environment variables as a dictionary, scoped to company."""
    company_id = _get_company_id_for_env_vars(tenant)
    return await env_var_service.get_all_environment_variables_dict(db, company_id=company_id)
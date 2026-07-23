from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.db.dependencies import get_async_session
from app.schemas import environment_variable as env_var_schema
from app.services import environment_variable as env_var_service
from app.core.security import get_current_active_user, require_superuser

router = APIRouter()


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
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_async_session),
    current_user=Depends(get_current_active_user),
):
    """List all environment variables."""
    env_vars = await env_var_service.get_environment_variables(db, skip=skip, limit=limit)
    
    # Mask secret values
    result = []
    for env_var in env_vars:
        env_dict = {
            "id": env_var.id,
            "key": env_var.key,
            "value": env_var.value if not env_var.is_secret else None,
            "masked_value": env_var_service.mask_secret_value(env_var.value) if env_var.is_secret else None,
            "description": env_var.description,
            "is_secret": env_var.is_secret,
            "created_at": env_var.created_at,
            "updated_at": env_var.updated_at,
        }
        result.append(env_dict)
    
    return result


@router.get("/{env_var_id}", response_model=env_var_schema.EnvironmentVariableOut)
async def get_environment_variable(
    env_var_id: int,
    db: AsyncSession = Depends(get_async_session),
    current_user=Depends(get_current_active_user),
):
    """Get a specific environment variable by ID."""
    env_var = await env_var_service.get_environment_variable(db, env_var_id)
    if not env_var:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Environment variable not found"
        )
    
    return {
        "id": env_var.id,
        "key": env_var.key,
        "value": env_var.value if not env_var.is_secret else None,
        "masked_value": env_var_service.mask_secret_value(env_var.value) if env_var.is_secret else None,
        "description": env_var.description,
        "is_secret": env_var.is_secret,
        "created_at": env_var.created_at,
        "updated_at": env_var.updated_at,
    }


@router.get("/key/{key}", response_model=env_var_schema.EnvironmentVariableOut)
async def get_environment_variable_by_key(
    key: str,
    db: AsyncSession = Depends(get_async_session),
    current_user=Depends(get_current_active_user),
):
    """Get a specific environment variable by key."""
    env_var = await env_var_service.get_environment_variable_by_key(db, key)
    if not env_var:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Environment variable not found"
        )
    
    return {
        "id": env_var.id,
        "key": env_var.key,
        "value": env_var.value if not env_var.is_secret else None,
        "masked_value": env_var_service.mask_secret_value(env_var.value) if env_var.is_secret else None,
        "description": env_var.description,
        "is_secret": env_var.is_secret,
        "created_at": env_var.created_at,
        "updated_at": env_var.updated_at,
    }


@router.put("/{env_var_id}", response_model=env_var_schema.EnvironmentVariableOut)
async def update_environment_variable(
    env_var_id: int,
    payload: env_var_schema.EnvironmentVariableUpdate,
    db: AsyncSession = Depends(get_async_session),
    current_user=Depends(require_superuser),
):
    """Update an environment variable."""
    env_var = await env_var_service.update_environment_variable(db, env_var_id, payload)
    if not env_var:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Environment variable not found"
        )
    
    return {
        "id": env_var.id,
        "key": env_var.key,
        "value": env_var.value if not env_var.is_secret else None,
        "masked_value": env_var_service.mask_secret_value(env_var.value) if env_var.is_secret else None,
        "description": env_var.description,
        "is_secret": env_var.is_secret,
        "created_at": env_var.created_at,
        "updated_at": env_var.updated_at,
    }


@router.delete("/{env_var_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_environment_variable(
    env_var_id: int,
    db: AsyncSession = Depends(get_async_session),
    current_user=Depends(require_superuser),
):
    """Delete an environment variable."""
    deleted = await env_var_service.delete_environment_variable(db, env_var_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Environment variable not found"
        )
    return None


@router.get("/export/.env", response_model=dict)
async def export_environment_variables(
    db: AsyncSession = Depends(get_async_session),
    current_user=Depends(require_superuser),
):
    """Export all environment variables as a dictionary (for .env file generation)."""
    return await env_var_service.get_all_environment_variables_dict(db)
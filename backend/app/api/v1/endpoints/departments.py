from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app.core.request import get_client_ip, get_user_agent
from app.db.dependencies import get_async_session
from app.schemas import department as department_schema
from app.services import department as department_service
from app.services.audit_log import create_audit_log
from app.core.security import get_current_active_user, require_superuser

router = APIRouter()


@router.post("/", response_model=department_schema.DepartmentOut, status_code=status.HTTP_201_CREATED)
async def create_department(
    request: Request,
    payload: department_schema.DepartmentCreate,
    db: AsyncSession = Depends(get_async_session),
    current_user=Depends(require_superuser),
):
    department = await department_service.create_department(db, payload)
    # Log department creation
    await create_audit_log(
        db,
        action="create",
        resource_type="department",
        resource_id=department.id,
        user_id=current_user.id,
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request),
        details={"department_name": department.name, "company_id": department.company_id, "created_by": current_user.email},
    )
    return department


@router.get("/", response_model=department_schema.DepartmentListResponse)
async def list_departments(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=100, description="Number of records to return"),
    search: Optional[str] = Query(None, description="Search by name, description, or location"),
    company_id: Optional[int] = Query(None, description="Filter by company ID"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    manager_id: Optional[int] = Query(None, description="Filter by manager ID"),
    sort_by: str = Query("name", description="Sort field (name, created_at, company_id)"),
    sort_order: str = Query("asc", description="Sort order (asc or desc)"),
    db: AsyncSession = Depends(get_async_session),
    current_user=Depends(get_current_active_user),
):
    departments, total = await department_service.get_departments(
        db,
        skip=skip,
        limit=limit,
        search=search,
        company_id=company_id,
        is_active=is_active,
        manager_id=manager_id,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    return department_schema.DepartmentListResponse(
        items=departments,
        total=total,
        page=(skip // limit) + 1,
        page_size=limit,
    )


@router.get("/stats", response_model=department_schema.DepartmentStats)
async def get_department_stats(
    db: AsyncSession = Depends(get_async_session),
    current_user=Depends(get_current_active_user),
):
    """Get department statistics including counts and company distribution."""
    return await department_service.get_department_stats(db)


@router.get("/{department_id}", response_model=department_schema.DepartmentOut)
async def get_department(
    department_id: int,
    db: AsyncSession = Depends(get_async_session),
    current_user=Depends(get_current_active_user),
):
    department = await department_service.get_department_with_details(db, department_id)
    if not department:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Department not found")
    return department


@router.put("/{department_id}", response_model=department_schema.DepartmentOut)
async def update_department(
    request: Request,
    department_id: int,
    payload: department_schema.DepartmentUpdate,
    db: AsyncSession = Depends(get_async_session),
    current_user=Depends(require_superuser),
):
    department = await department_service.update_department(db, department_id, payload)
    if not department:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Department not found")
    # Log department update
    await create_audit_log(
        db,
        action="update",
        resource_type="department",
        resource_id=department_id,
        user_id=current_user.id,
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request),
        details={"department_name": department.name, "updated_by": current_user.email, "updated_fields": payload.model_dump(exclude_none=True)},
    )
    return department


@router.delete("/{department_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_department(
    request: Request,
    department_id: int,
    db: AsyncSession = Depends(get_async_session),
    current_user=Depends(require_superuser),
):
    # Fetch department before deletion for audit log
    department_to_delete = await department_service.get_department(db, department_id)
    deleted = await department_service.delete_department(db, department_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Department not found")
    # Log department deletion
    await create_audit_log(
        db,
        action="delete",
        resource_type="department",
        resource_id=department_id,
        user_id=current_user.id,
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request),
        details={"department_name": department_to_delete.name if department_to_delete else "unknown", "deleted_by": current_user.email},
    )
    return None
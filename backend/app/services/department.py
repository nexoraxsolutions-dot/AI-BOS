from typing import Optional, List, Dict, Any
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.department import Department
from app.models.user import User
from app.services.cache import cache_service


async def create_department(db: AsyncSession, payload):
    department = Department(**payload.model_dump())
    db.add(department)
    await db.commit()
    await db.refresh(department)
    
    # Invalidate departments list cache
    await cache_service.delete_pattern("departments:list:*")
    await cache_service.delete("departments:stats")
    
    return department


async def get_department(db: AsyncSession, department_id: int):
    # Try cache first
    cache_key = f"department:{department_id}"
    cached_department = await cache_service.get(cache_key)
    if cached_department:
        return cached_department
    
    result = await db.execute(select(Department).where(Department.id == department_id))
    department = result.scalar_one_or_none()
    
    # Cache department data
    if department:
        await cache_service.set(cache_key, department.__dict__, ttl=600)
    
    return department


async def get_departments(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 20,
    search: Optional[str] = None,
    company_id: Optional[int] = None,
    is_active: Optional[bool] = None,
    manager_id: Optional[int] = None,
    sort_by: str = "name",
    sort_order: str = "asc",
):
    # Build query
    query = select(Department)
    
    # Apply filters
    if search:
        search_filter = or_(
            Department.name.ilike(f"%{search}%"),
            Department.description.ilike(f"%{search}%"),
            Department.location.ilike(f"%{search}%"),
        )
        query = query.where(search_filter)
    
    if company_id is not None:
        query = query.where(Department.company_id == company_id)
    
    if is_active is not None:
        query = query.where(Department.is_active == is_active)
    
    if manager_id is not None:
        query = query.where(Department.manager_id == manager_id)
    
    # Apply sorting
    sort_column = getattr(Department, sort_by, Department.name)
    if sort_order == "desc":
        sort_column = sort_column.desc()
    else:
        sort_column = sort_column.asc()
    query = query.order_by(sort_column)
    
    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    # Apply pagination
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    departments = result.scalars().all()
    
    return departments, total


async def update_department(db: AsyncSession, department_id: int, payload):
    department = await get_department(db, department_id)
    if not department:
        return None
    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(department, field, value)
    await db.commit()
    await db.refresh(department)
    
    # Invalidate caches
    await cache_service.delete(f"department:{department_id}")
    await cache_service.delete_pattern("departments:list:*")
    await cache_service.delete("departments:stats")
    
    return department


async def delete_department(db: AsyncSession, department_id: int) -> bool:
    department = await get_department(db, department_id)
    if not department:
        return False
    await db.delete(department)
    await db.commit()
    
    # Invalidate caches
    await cache_service.delete(f"department:{department_id}")
    await cache_service.delete_pattern("departments:list:*")
    await cache_service.delete("departments:stats")
    
    return True


async def get_department_stats(db: AsyncSession) -> Dict[str, Any]:
    # Try cache first
    cache_key = "departments:stats"
    cached_stats = await cache_service.get(cache_key)
    if cached_stats:
        return cached_stats
    
    # Total departments
    total_result = await db.execute(select(func.count(Department.id)))
    total_departments = total_result.scalar() or 0
    
    # Active departments
    active_result = await db.execute(
        select(func.count(Department.id)).where(Department.is_active == True)
    )
    active_departments = active_result.scalar() or 0
    
    # Inactive departments
    inactive_departments = total_departments - active_departments
    
    # Total companies with departments
    companies_with_depts_result = await db.execute(
        select(func.count(func.distinct(Department.company_id)))
    )
    total_companies_with_departments = companies_with_depts_result.scalar() or 0
    
    # Average departments per company - calculate in Python to avoid SQLite limitation
    if total_companies_with_departments > 0:
        avg_departments = total_departments / total_companies_with_departments
    else:
        avg_departments = None
    
    # Departments by company
    depts_by_company_result = await db.execute(
        select(Department.company_id, func.count(Department.id))
        .group_by(Department.company_id)
    )
    depts_by_company = {str(company_id): count for company_id, count in depts_by_company_result.all()}
    
    stats = {
        "total_departments": total_departments,
        "active_departments": active_departments,
        "inactive_departments": inactive_departments,
        "total_companies_with_departments": total_companies_with_departments,
        "avg_departments_per_company": float(avg_departments) if avg_departments else None,
        "departments_by_company": depts_by_company,
    }
    
    # Cache for 5 minutes
    await cache_service.set(cache_key, stats, ttl=300)
    
    return stats


async def get_department_with_details(db: AsyncSession, department_id: int):
    """Get a department with manager and company details."""
    department = await get_department(db, department_id)
    if not department:
        return None
    
    # Get manager name if exists
    manager_name = None
    if department.manager_id:
        manager_result = await db.execute(
            select(User.full_name, User.email).where(User.id == department.manager_id)
        )
        manager = manager_result.first()
        if manager:
            manager_name = manager.full_name or manager.email
    
    # Get company name
    from app.models.company import Company
    company_result = await db.execute(
        select(Company.name).where(Company.id == department.company_id)
    )
    company_name = company_result.scalar()
    
    # Get employee count (users in this department - assuming users can be linked to departments)
    # For now, we'll return 0 as we don't have a direct user-department relationship
    employee_count = 0
    
    # Build response dict
    dept_dict = department.__dict__.copy()
    dept_dict["manager_name"] = manager_name
    dept_dict["company_name"] = company_name
    dept_dict["employee_count"] = employee_count
    
    return dept_dict
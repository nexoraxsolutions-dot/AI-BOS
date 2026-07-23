from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.db.dependencies import get_async_session
from app.schemas import company as company_schema
from app.services import company as company_service
from app.core.security import get_current_active_user, require_superuser

router = APIRouter()


@router.post("/", response_model=company_schema.CompanyOut, status_code=status.HTTP_201_CREATED)
async def create_company(
    payload: company_schema.CompanyCreate,
    db: AsyncSession = Depends(get_async_session),
    current_user=Depends(require_superuser),
):
    return await company_service.create_company(db, payload)


@router.get("/", response_model=List[company_schema.CompanyOut])
async def list_companies(
    skip: int = 0,
    limit: int = 20,
    db: AsyncSession = Depends(get_async_session),
    current_user=Depends(get_current_active_user),
):
    return await company_service.get_companies(db, skip=skip, limit=limit)


@router.get("/{company_id}", response_model=company_schema.CompanyOut)
async def get_company(
    company_id: int,
    db: AsyncSession = Depends(get_async_session),
    current_user=Depends(get_current_active_user),
):
    company = await company_service.get_company(db, company_id)
    if not company:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
    return company


@router.put("/{company_id}", response_model=company_schema.CompanyOut)
async def update_company(
    company_id: int,
    payload: company_schema.CompanyUpdate,
    db: AsyncSession = Depends(get_async_session),
    current_user=Depends(require_superuser),
):
    company = await company_service.update_company(db, company_id, payload)
    if not company:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
    return company


@router.delete("/{company_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_company(
    company_id: int,
    db: AsyncSession = Depends(get_async_session),
    current_user=Depends(require_superuser),
):
    deleted = await company_service.delete_company(db, company_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
    return None
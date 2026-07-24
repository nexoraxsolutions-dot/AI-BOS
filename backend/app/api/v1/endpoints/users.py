from fastapi import APIRouter, Depends, HTTPException, Request, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app.core.request import get_client_ip, get_user_agent
from app.db.dependencies import get_async_session
from app.schemas import user as user_schema
from app.services import user as user_service
from app.services.audit_log import create_audit_log
from app.core.security import get_current_active_user, require_superuser, get_current_user

router = APIRouter()


@router.post("/", response_model=user_schema.UserOut, status_code=status.HTTP_201_CREATED)
async def create_user(
    request: Request,
    payload: user_schema.UserCreate,
    db: AsyncSession = Depends(get_async_session),
    current_user=Depends(require_superuser),
):
    # Check for duplicate email
    existing = await user_service.get_user_by_email(db, payload.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email already exists",
        )
    # Check for duplicate username
    if payload.username:
        existing_username = await user_service.get_user_by_username(db, payload.username)
        if existing_username:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A user with this username already exists",
            )
    user = await user_service.create_user(db, payload)
    # Log user creation
    await create_audit_log(
        db,
        action="create",
        resource_type="user",
        resource_id=user.id,
        user_id=current_user.id,
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request),
        details={"email": user.email, "created_by": current_user.email},
    )
    return user


@router.get("/", response_model=List[user_schema.UserOut])
async def list_users(
    skip: int = 0,
    limit: int = 20,
    search: Optional[str] = Query(None, description="Search by email, name, or username"),
    db: AsyncSession = Depends(get_async_session),
    current_user=Depends(get_current_active_user),
):
    if search:
        return await user_service.search_users(db, search, skip=skip, limit=limit)
    return await user_service.get_users(db, skip=skip, limit=limit)


@router.get("/me", response_model=user_schema.UserOut)
async def get_current_user_profile(
    db: AsyncSession = Depends(get_async_session),
    current_user=Depends(get_current_active_user),
):
    return current_user


@router.put("/me/profile", response_model=user_schema.UserOut)
async def update_my_profile(
    request: Request,
    payload: user_schema.UserProfileUpdate,
    db: AsyncSession = Depends(get_async_session),
    current_user=Depends(get_current_active_user),
):
    # Check username uniqueness if changing
    if payload.username and payload.username != current_user.username:
        existing = await user_service.get_user_by_username(db, payload.username)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username is already taken",
            )
    # Check email uniqueness if changing
    if payload.email and payload.email != current_user.email:
        existing = await user_service.get_user_by_email(db, payload.email)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email is already in use",
            )
    updated = await user_service.update_profile(db, current_user.id, payload)
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    # Log profile update
    await create_audit_log(
        db,
        action="update_profile",
        resource_type="user",
        resource_id=current_user.id,
        user_id=current_user.id,
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request),
        details={"updated_fields": payload.model_dump(exclude_none=True)},
    )
    return updated


@router.post("/me/change-password", status_code=status.HTTP_200_OK)
async def change_my_password(
    request: Request,
    payload: user_schema.PasswordChange,
    db: AsyncSession = Depends(get_async_session),
    current_user=Depends(get_current_active_user),
):
    success = await user_service.change_password(
        db, current_user.id, payload.current_password, payload.new_password
    )
    if not success:
        # Log failed password change attempt
        await create_audit_log(
            db,
            action="change_password_failed",
            resource_type="user",
            resource_id=current_user.id,
            user_id=current_user.id,
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request),
            details={"reason": "incorrect_current_password"},
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )
    # Log successful password change
    await create_audit_log(
        db,
        action="change_password",
        resource_type="user",
        resource_id=current_user.id,
        user_id=current_user.id,
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request),
        details={"email": current_user.email},
    )
    return {"message": "Password changed successfully"}


@router.get("/{user_id}", response_model=user_schema.UserOut)
async def get_user(
    user_id: int,
    db: AsyncSession = Depends(get_async_session),
    current_user=Depends(get_current_active_user),
):
    user = await user_service.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


@router.put("/{user_id}", response_model=user_schema.UserOut)
async def update_user(
    request: Request,
    user_id: int,
    payload: user_schema.UserUpdate,
    db: AsyncSession = Depends(get_async_session),
    current_user=Depends(require_superuser),
):
    user = await user_service.update_user(db, user_id, payload)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    # Log user update
    await create_audit_log(
        db,
        action="update",
        resource_type="user",
        resource_id=user_id,
        user_id=current_user.id,
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request),
        details={"updated_by": current_user.email, "updated_fields": payload.model_dump(exclude_none=True)},
    )
    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    request: Request,
    user_id: int,
    db: AsyncSession = Depends(get_async_session),
    current_user=Depends(require_superuser),
):
    # Fetch user before deletion for audit log
    user_to_delete = await user_service.get_user(db, user_id)
    deleted = await user_service.delete_user(db, user_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    # Log user deletion
    await create_audit_log(
        db,
        action="delete",
        resource_type="user",
        resource_id=user_id,
        user_id=current_user.id,
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request),
        details={"deleted_user_email": user_to_delete.email if user_to_delete else "unknown", "deleted_by": current_user.email},
    )
    return None

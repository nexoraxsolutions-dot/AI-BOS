from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import security, token
from app.core.request import get_client_ip, get_user_agent
from app.db.dependencies import get_async_session
from app.schemas import auth as auth_schema
from app.schemas import user as user_schema
from app.services import auth as auth_service
from app.services.audit_log import create_audit_log
from app.services.user import get_user_by_email

router = APIRouter()


@router.post(
    "/register",
    response_model=auth_schema.RegisterResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register(
    request: Request,
    payload: auth_schema.RegisterRequest,
    db: AsyncSession = Depends(get_async_session),
):
    """Public self-service registration. Creates a non-superuser account and returns tokens."""
    try:
        user = await auth_service.register_user(db, payload)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    access_token_expires = timedelta(minutes=security.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = token.create_access_token(
        data={"sub": user.email},
        expires_delta=access_token_expires,
    )
    refresh_token = token.create_refresh_token(data={"sub": user.email})

    await token.store_refresh_token(
        db,
        token_str=refresh_token,
        user_id=user.id,
        client_ip=get_client_ip(request),
        user_agent=get_user_agent(request),
    )

    await create_audit_log(
        db,
        action="register",
        resource_type="auth",
        resource_id=user.id,
        user_id=user.id,
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request),
        details={"email": user.email, "username": user.username},
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": user_schema.UserOut.model_validate(user),
    }


@router.post("/login", response_model=auth_schema.Token)
async def login(

    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_async_session),
):
    user = await auth_service.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        # Log failed login attempt
        await create_audit_log(
            db,
            action="login_failed",
            resource_type="auth",
            resource_id=None,
            user_id=None,
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request),
            details={"email": form_data.username},
        )
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or password")
    
    access_token_expires = timedelta(minutes=security.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = token.create_access_token(data={"sub": user.email}, expires_delta=access_token_expires)
    refresh_token = token.create_refresh_token(data={"sub": user.email})
    
    # Store refresh token in database
    await token.store_refresh_token(
        db,
        token_str=refresh_token,
        user_id=user.id,
        client_ip=get_client_ip(request),
        user_agent=get_user_agent(request),
    )
    
    # Log successful login
    await create_audit_log(
        db,
        action="login",
        resource_type="auth",
        resource_id=user.id,
        user_id=user.id,
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request),
        details={"email": user.email},
    )
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@router.post("/refresh", response_model=auth_schema.Token)
async def refresh_token(
    request: Request,
    refresh_token_data: auth_schema.RefreshToken,
    db: AsyncSession = Depends(get_async_session),
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # Verify refresh token is valid in database (not revoked, not expired)
    stored_token = await token.verify_refresh_token(db, refresh_token_data.refresh_token)
    if not stored_token:
        raise credentials_exception
    
    try:
        payload = security.jwt.decode(refresh_token_data.refresh_token, security.SECRET_KEY, algorithms=[security.ALGORITHM])
        email: str | None = payload.get("sub")
        token_type: str | None = payload.get("type")
        
        if email is None or token_type != "refresh":
            raise credentials_exception
    except security.JWTError:
        raise credentials_exception
    
    user = await get_user_by_email(db, email)
    if not user:
        raise credentials_exception
    
    access_token_expires = timedelta(minutes=security.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = token.create_access_token(data={"sub": user.email}, expires_delta=access_token_expires)
    new_refresh_token = token.create_refresh_token(data={"sub": user.email})
    
    # Revoke old refresh token and store new one
    if stored_token:
        await token.revoke_token(db, stored_token.id, user.id)
    await token.store_refresh_token(
        db,
        token_str=new_refresh_token,
        user_id=user.id,
        client_ip=get_client_ip(request),
        user_agent=get_user_agent(request),
    )
    
    # Log token refresh
    await create_audit_log(
        db,
        action="token_refresh",
        resource_type="auth",
        resource_id=user.id,
        user_id=user.id,
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request),
        details={"email": user.email},
    )
    
    return {
        "access_token": access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer",
    }


@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(
    request: Request,
    current_user=Depends(security.get_current_active_user),
    db: AsyncSession = Depends(get_async_session),
):
    """Logout endpoint - revokes all refresh tokens and client should remove tokens from storage."""
    # Revoke all refresh tokens for the user
    revoked_count = await token.revoke_all_user_tokens(db, current_user.id, token_type="refresh")

    # Log logout
    await create_audit_log(
        db,
        action="logout",
        resource_type="auth",
        resource_id=current_user.id,
        user_id=current_user.id,
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request),
        details={"email": current_user.email, "revoked_tokens": revoked_count},
    )
    return {"message": "Successfully logged out", "revoked_tokens": revoked_count}


@router.get("/validate", response_model=auth_schema.TokenValidationResponse)
async def validate_token(current_user=Depends(security.get_current_active_user)):
    """Validate the current access token and return user info."""
    return {
        "valid": True,
        "email": current_user.email,
        "user_id": current_user.id,
    }

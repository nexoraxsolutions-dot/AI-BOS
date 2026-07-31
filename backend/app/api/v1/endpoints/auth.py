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
from app.services.password_reset import request_password_reset, reset_password as password_reset_service
from app.services.rate_limiter import check_password_reset_rate_limit, check_reset_password_rate_limit, record_failed_reset_attempt
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
        "user": auth_schema.UserOutLite.model_validate(user),
    }


@router.post("/login", response_model=auth_schema.LoginResponse)
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_async_session),
):
    """User login with email/password (form-based, OAuth2 compatible)."""
    user = await auth_service.authenticate_user(db, form_data.username, form_data.password, request)
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
        "user": user_schema.UserOut.model_validate(user),
    }


@router.post("/login-json", response_model=auth_schema.LoginResponse)
async def login_json(
    request: Request,
    payload: auth_schema.LoginRequest,
    db: AsyncSession = Depends(get_async_session),
):
    """User login with email/password (JSON body, REST-compatible)."""
    user = await auth_service.authenticate_user(db, payload.email, payload.password, request)
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
            details={"email": payload.email},
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
        "user": user_schema.UserOut.model_validate(user),
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


@router.get("/verify-email/{token}", response_model=auth_schema.VerifyEmailResponse)
async def verify_email(
    token: str,
    db: AsyncSession = Depends(get_async_session),
):
    """Verify a user's email address using a verification token."""
    try:
        user = await auth_service.verify_email(db, token)
        return {
            "message": "Email verified successfully",
            "email_verified": True,
        }
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.post("/resend-verification", response_model=auth_schema.MessageResponse)
async def resend_verification(
    request: Request,
    payload: auth_schema.EmailVerificationRequest,
    db: AsyncSession = Depends(get_async_session),
):
    """Resend the email verification link."""
    try:
        await auth_service.resend_verification_email(db, payload.email)
        return {"message": "Verification email sent successfully"}
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.post("/forgot-password", response_model=auth_schema.ForgotPasswordResponse)
async def forgot_password(
    request: Request,
    payload: auth_schema.PasswordResetRequest,
    db: AsyncSession = Depends(get_async_session),
):
    """Request a password reset email. Always returns the same response regardless of whether the email exists."""
    client_ip = get_client_ip(request)
    email = payload.email.lower()
    
    # Check if user exists (for rate limiting by user_id)
    user = await get_user_by_email(db, email)
    user_id = user.id if user else None
    
    # Check rate limits (IP, email, and user-based)
    try:
        await check_password_reset_rate_limit(
            db,
            ip_address=client_ip,
            email=email,
            user_id=user_id,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=str(exc),
        ) from exc
    
    await request_password_reset(
        db,
        email=email,
        client_ip=client_ip,
        user_agent=get_user_agent(request),
    )
    return {"message": "If an account with that email exists, a password reset link has been sent."}


@router.post("/reset-password", response_model=auth_schema.MessageResponse)
async def reset_password(
    request: Request,
    payload: auth_schema.PasswordReset,
    db: AsyncSession = Depends(get_async_session),
):
    """Reset password using a token from the password reset email."""
    client_ip = get_client_ip(request)
    
    # Validate token first to get user_id for rate limiting
    from app.services.password_reset import validate_reset_token
    user = await validate_reset_token(db, payload.token)
    user_id = user.id if user else None
    
    # Check rate limits (IP and user-based)
    try:
        await check_reset_password_rate_limit(
            db,
            ip_address=client_ip,
            user_id=user_id,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=str(exc),
        ) from exc
    
    try:
        await password_reset_service(
            db,
            raw_token=payload.token,
            new_password=payload.new_password,
            client_ip=client_ip,
            user_agent=get_user_agent(request),
        )
        return {"message": "Password has been reset successfully. You can now log in with your new password."}
    except ValueError as exc:
        # Record failed attempt for brute-force detection
        await record_failed_reset_attempt(db, client_ip, user_id)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import security, token
from app.db.dependencies import get_async_session
from app.schemas import auth as auth_schema
from app.services import auth as auth_service
from app.services.user import get_user_by_email

router = APIRouter()


@router.post("/login", response_model=auth_schema.Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_async_session)):
    user = await auth_service.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or password")
    
    access_token_expires = timedelta(minutes=security.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = token.create_access_token(data={"sub": user.email}, expires_delta=access_token_expires)
    refresh_token = token.create_refresh_token(data={"sub": user.email})
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@router.post("/refresh", response_model=auth_schema.Token)
async def refresh_token(refresh_token_data: auth_schema.RefreshToken, db: AsyncSession = Depends(get_async_session)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
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
    
    return {
        "access_token": access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer",
    }


@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout():
    """Logout endpoint - client should remove tokens from storage."""
    return {"message": "Successfully logged out"}


@router.get("/validate", response_model=auth_schema.TokenValidationResponse)
async def validate_token(current_user=Depends(security.get_current_active_user)):
    """Validate the current access token and return user info."""
    return {
        "valid": True,
        "email": current_user.email,
        "user_id": current_user.id,
    }

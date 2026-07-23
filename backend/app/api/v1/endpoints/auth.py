from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import security, token
from app.db.dependencies import get_async_session
from app.schemas import auth as auth_schema
from app.services import auth as auth_service

router = APIRouter()

@router.post("/login", response_model=auth_schema.Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_async_session)):
    user = await auth_service.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or password")
    access_token_expires = timedelta(minutes=security.ACCESS_TOKEN_EXPIRE_MINUTES)
    token_data = token.create_access_token(data={"sub": user.email}, expires_delta=access_token_expires)
    return {"access_token": token_data, "token_type": "bearer"}

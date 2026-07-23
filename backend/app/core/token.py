from datetime import timedelta

from app.core.security import create_access_token as create_security_access_token
from app.core.security import create_refresh_token as create_security_refresh_token


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    return create_security_access_token(data=data, expires_delta=expires_delta)


def create_refresh_token(data: dict) -> str:
    return create_security_refresh_token(data=data)

from datetime import timedelta

from app.core.security import create_access_token as create_security_access_token


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    return create_security_access_token(data=data, expires_delta=expires_delta)

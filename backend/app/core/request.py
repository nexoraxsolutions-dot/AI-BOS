"""Request utilities for extracting client information."""


def get_client_ip(request) -> str | None:
    """Extract client IP address from request.
    
    Supports X-Forwarded-For headers for reverse proxy setups.
    """
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        # Take the first IP in the chain
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else None


def get_user_agent(request) -> str | None:
    """Extract User-Agent header from request."""
    return request.headers.get("User-Agent")
"""API dependency injection functions."""

from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.core.security import get_current_user
from app.core.config import get_settings
from app.models.user import CurrentUser

settings = get_settings()


# Optional security scheme (for endpoints that can work with or without auth)
optional_security = HTTPBearer(auto_error=False)


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(optional_security)
) -> Optional[CurrentUser]:
    """
    Get current user if authenticated, otherwise return None.
    
    This is useful for endpoints that support both authenticated
    and unauthenticated access.
    """
    if not credentials:
        return None
    
    try:
        from app.core.security import verify_token
        payload = await verify_token(credentials)
        return CurrentUser(
            sub=payload.get("sub", ""),
            email=payload.get("email"),
            email_verified=payload.get("email_verified", False),
        )
    except HTTPException:
        return None


async def get_current_active_user(
    current_user: CurrentUser = Depends(get_current_user)
) -> CurrentUser:
    """
    Get current authenticated user.
    
    Raises 401 if not authenticated.
    """
    return current_user


def require_auth() -> CurrentUser:
    """
    Dependency that requires authentication.
    
    Usage in routes:
        @router.post("/endpoint")
        async def endpoint(user: CurrentUser = Depends(require_auth())):
            ...
    """
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required"
    )

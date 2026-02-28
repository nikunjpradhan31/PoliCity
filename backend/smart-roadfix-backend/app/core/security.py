"""Security module for Auth0 JWT authentication."""

from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
import httpx

from app.core.config import get_settings

settings = get_settings()
security = HTTPBearer()

# Cache for JWKS
_jwks: Optional[dict] = None


async def get_jwks() -> dict:
    """Fetch JWKS from Auth0 domain."""
    global _jwks
    if _jwks is not None:
        return _jwks
    
    jwks_url = f"https://{settings.AUTH0_DOMAIN}/.well-known/jwks.json"
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(jwks_url)
            response.raise_for_status()
            _jwks = response.json()
            return _jwks
        except httpx.HTTPError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to fetch JWKS: {str(e)}"
            )


def get_signing_key(token: str, jwks: dict) -> str:
    """Extract the signing key from JWKS based on token header."""
    try:
        unverified_header = jwt.get_unverified_header(token)
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token header"
        )
    
    kid = unverified_header.get("kid")
    if not kid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing key ID"
        )
    
    for key in jwks.get("keys", []):
        if key.get("kid") == kid:
            return key
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Unable to find appropriate key"
    )


async def verify_token(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    """Verify and decode JWT token from Auth0."""
    token = credentials.credentials
    
    try:
        jwks = await get_jwks()
        signing_key = get_signing_key(token, jwks)
        
        payload = jwt.decode(
            token,
            signing_key,
            algorithms=settings.AUTH0_ALGORITHMS,
            audience=settings.AUTH0_AUDIENCE,
            issuer=f"https://{settings.AUTH0_DOMAIN}/"
        )
        return payload
        
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token validation failed: {str(e)}"
        )


async def get_current_user(
    payload: dict = Depends(verify_token)
) -> dict:
    """Get current authenticated user from token payload."""
    return {
        "sub": payload.get("sub"),
        "email": payload.get("email"),
        "email_verified": payload.get("email_verified", False),
    }

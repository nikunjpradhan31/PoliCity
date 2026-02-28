"""Health check routes."""

from datetime import datetime

from fastapi import APIRouter, status

router = APIRouter(tags=["health"])


@router.get(
    "/health",
    status_code=status.HTTP_200_OK,
    summary="Health check endpoint",
)
async def health_check() -> dict:
    """
    Health check endpoint.
    
    Returns the current status of the API.
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get(
    "/health/ready",
    status_code=status.HTTP_200_OK,
    summary="Readiness check endpoint",
)
async def readiness_check() -> dict:
    """
    Readiness check endpoint.
    
    Returns whether the API is ready to serve requests.
    """
    # In production, check database connectivity
    return {
        "status": "ready",
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get(
    "/health/live",
    status_code=status.HTTP_200_OK,
    summary="Liveness check endpoint",
)
async def liveness_check() -> dict:
    """
    Liveness check endpoint.
    
    Used by Kubernetes to determine if the container is running.
    """
    return {
        "status": "alive",
        "timestamp": datetime.utcnow().isoformat(),
    }

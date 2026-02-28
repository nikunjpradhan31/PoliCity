"""
API routes for PoliCity API.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any

from app.models import MessageResponse, User
from app.db import get_database

# Create API router
router = APIRouter()


@router.get("/", response_model=MessageResponse)
async def root():
    """
    Root endpoint - returns welcome message.
    
    Returns:
        MessageResponse: Welcome message.
    """
    return MessageResponse(message="Welcome to PoliCity")


@router.get("/health", response_model=Dict[str, str])
async def health_check():
    """
    Health check endpoint.
    
    Returns:
        Dict: Health status.
    """
    try:
        # Test MongoDB connection
        db = get_database()
        db.command("ping")
        db_status = "connected"
    except Exception:
        db_status = "disconnected"
    
    return {
        "status": "healthy" if db_status == "connected" else "unhealthy",
        "database": db_status
    }

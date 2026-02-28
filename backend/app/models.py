"""
Pydantic models for PoliCity API requests and responses.
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional


class User(BaseModel):
    """
    User model representing authenticated user info from Auth0.
    """
    sub: str = Field(..., description="Auth0 subject identifier")
    email: Optional[EmailStr] = Field(None, description="User email address")
    name: Optional[str] = Field(None, description="User display name")
    picture: Optional[str] = Field(None, description="User profile picture URL")


class MessageResponse(BaseModel):
    """
    Standard message response model.
    """
    message: str = Field(..., description="Response message")


class HealthResponse(BaseModel):
    """
    Health check response model.
    """
    status: str = Field(..., description="Service status")
    database: str = Field(..., description="Database connection status")

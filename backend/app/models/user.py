"""User data models."""

from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class UserBase(BaseModel):
    """Base user model."""
    sub: str = Field(..., description="Auth0 subject identifier")
    email: Optional[EmailStr] = Field(None, description="User email")
    email_verified: bool = Field(default=False)


class UserResponse(UserBase):
    """Model for user API response."""
    id: str = Field(..., alias="_id")

    class Config:
        populate_by_name = True


class CurrentUser(BaseModel):
    """Model for currently authenticated user."""
    sub: str
    email: Optional[str] = None
    email_verified: bool = False

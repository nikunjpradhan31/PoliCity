"""Budget data models."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class BudgetItem(BaseModel):
    """Individual budget item."""
    category: str = Field(..., description="Budget category")
    amount: float = Field(..., ge=0.0, description="Budget amount")
    description: Optional[str] = None


class BudgetBase(BaseModel):
    """Base budget model."""
    city: str = Field(..., description="City name")
    year: int = Field(..., ge=2000, le=2100, description="Budget year")
    total_budget: float = Field(..., ge=0.0, description="Total budget")
    items: list[BudgetItem] = Field(default_factory=list)


class BudgetCreate(BudgetBase):
    """Model for creating a budget."""
    uploaded_by: str = Field(..., description="User who uploaded the budget")


class BudgetUpdate(BaseModel):
    """Model for updating a budget."""
    total_budget: Optional[float] = Field(None, ge=0.0)
    items: Optional[list[BudgetItem]] = None


class BudgetInDB(BudgetBase):
    """Model for budget stored in database."""
    uploaded_by: str
    created_at: datetime
    updated_at: datetime


class BudgetResponse(BudgetBase):
    """Model for budget API response."""
    id: str = Field(..., alias="_id")
    uploaded_by: str
    created_at: datetime
    updated_at: datetime

    class Config:
        populate_by_name = True


class BudgetListResponse(BaseModel):
    """Model for list of budgets response."""
    budgets: list[BudgetResponse]
    total: int

"""
Pydantic models for PoliCity API requests and responses.
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional


"""
Pydantic models for PoliCity API requests and responses.
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

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

# ============================================
# Infrastructure Reporting Workflow Models
# ============================================

class InfrastructureReportRequest(BaseModel):
    incident_id: Optional[str] = Field(None, description="Unique incident identifier. If provided and a prior run exists in MongoDB, saved results are returned without re-running agents")
    issue_type: str = Field(..., description="Type of infrastructure issue")
    location: str = Field(..., description="City and state")
    fiscal_year: int = Field(..., description="Fiscal year for budget analysis")
    image_url: Optional[str] = Field(None, description="Optional image URL for severity assessment")
    image_base64: Optional[str] = Field(None, description="Optional base64-encoded image")
    force_refresh: Optional[List[str]] = Field(None, description="List of agent names to re-run even if saved data exists")

class MultiInfrastructureReportRequest(BaseModel):
    incident_ids: List[str] = Field(..., description="List of unique incident identifiers to compile into a single report.")
    fiscal_year: int = Field(..., description="Fiscal year for budget analysis")
    force_refresh: Optional[List[str]] = Field(None, description="List of agent names to re-run even if saved data exists")

class InfrastructureReportResponse(BaseModel):
    report_id: str
    incident_id: Optional[str] = None
    status: str
    progress: int
    cache_hit: bool
    agents_skipped: List[str]
    result: Optional[dict] = None

class ReportStatusResponse(BaseModel):
    report_id: str
    incident_id: Optional[str] = None
    status: str
    progress: int
    current_agent: str
    cache_hit: bool
    agents_completed: List[str]
    agents_skipped: List[str]
    agents_failed: List[str]
    result: Optional[dict] = None
    error: Optional[str] = None

class IncidentDetailResponse(BaseModel):
    incident_id: str
    status: str
    inputs: dict
    pipeline_run: dict
    agent_outputs: dict
    report_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime


"""Pothole data models."""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class PotholeStatus(str, Enum):
    """Pothole status enumeration."""
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CLOSED = "closed"


class GeoJSONPoint(BaseModel):
    """GeoJSON Point geometry."""
    type: str = Field(default="Point", description="GeoJSON type")
    coordinates: list[float] = Field(
        description="[longitude, latitude] coordinates"
    )


class PotholeBase(BaseModel):
    """Base pothole model."""
    external_id: str = Field(..., description="External ID from Open311")
    description: Optional[str] = Field(None, description="Pothole description")
    severity_score: float = Field(default=0.0, ge=0.0, le=100.0)
    status: PotholeStatus = Field(default=PotholeStatus.OPEN)
    city: Optional[str] = Field(None, description="City name")


class PotholeCreate(PotholeBase):
    """Model for creating a pothole."""
    location: GeoJSONPoint


class PotholeUpdate(BaseModel):
    """Model for updating a pothole."""
    description: Optional[str] = None
    severity_score: Optional[float] = Field(None, ge=0.0, le=100.0)
    status: Optional[PotholeStatus] = None


class PotholeInDB(PotholeBase):
    """Model for pothole stored in database."""
    location: GeoJSONPoint
    reported_at: datetime
    created_at: datetime
    updated_at: datetime


class PotholeResponse(PotholeBase):
    """Model for pothole API response."""
    id: str = Field(..., alias="_id")
    location: GeoJSONPoint
    reported_at: datetime
    created_at: datetime
    updated_at: datetime

    class Config:
        populate_by_name = True


class PotholeListResponse(BaseModel):
    """Model for list of potholes response."""
    potholes: list[PotholeResponse]
    total: int


class Open311Request(BaseModel):
    """Open311 service request model."""
    service_request_id: str
    service_code: str
    service_name: str
    description: Optional[str] = None
    status: str
    status_notes: Optional[str] = None
    requested_datetime: Optional[str] = None
    updated_datetime: Optional[str] = None
    address: Optional[str] = None
    address_id: Optional[str] = None
    zipcode: Optional[str] = None
    lat: Optional[float] = None
    long: Optional[float] = None
    media_url: Optional[str] = None

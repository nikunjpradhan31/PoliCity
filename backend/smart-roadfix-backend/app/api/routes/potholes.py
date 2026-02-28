"""Pothole management routes."""

from typing import Optional

from fastapi import APIRouter, HTTPException, Query, status

from app.services.pothole_service import pothole_service
from app.models.pothole import (
    PotholeCreate,
    PotholeUpdate,
    PotholeResponse,
    PotholeListResponse,
)

router = APIRouter(prefix="/potholes", tags=["potholes"])


@router.get(
    "/sync",
    response_model=dict,
    summary="Sync potholes from Open311",
)
async def sync_potholes(
    city: str = Query(..., description="City name"),
) -> dict:
    """
    Fetch potholes from Open311 API and store in MongoDB.
    
    This endpoint retrieves pothole data from the configured Open311
    API endpoint and stores it in the local database.
    """
    try:
        result = await pothole_service.sync_from_open311(city)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to sync potholes: {str(e)}"
        )


@router.get(
    "",
    response_model=PotholeListResponse,
    summary="Get potholes",
)
async def get_potholes(
    city: Optional[str] = Query(None, description="Filter by city"),
    status: Optional[str] = Query(None, description="Filter by status"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum records to return"),
) -> PotholeListResponse:
    """
    Get stored potholes with optional filters.
    
    Returns a paginated list of potholes from the database.
    """
    potholes, total = await pothole_service.get_potholes(
        city=city,
        status=status,
        skip=skip,
        limit=limit,
    )
    
    # Convert ObjectId to string for response
    formatted_potholes = []
    for p in potholes:
        p["_id"] = str(p["_id"])
        formatted_potholes.append(p)
    
    return PotholeListResponse(
        potholes=formatted_potholes,  # type: ignore
        total=total,
    )


@router.get(
    "/{pothole_id}",
    response_model=PotholeResponse,
    summary="Get pothole by ID",
)
async def get_pothole(
    pothole_id: str = Query(..., description="Pothole ID"),
) -> PotholeResponse:
    """
    Get a specific pothole by ID.
    """
    pothole = await pothole_service.get_pothole_by_id(pothole_id)
    
    if not pothole:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pothole {pothole_id} not found"
        )
    
    pothole["_id"] = str(pothole["_id"])
    return pothole  # type: ignore


@router.post(
    "",
    response_model=PotholeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new pothole",
)
async def create_pothole(
    pothole: PotholeCreate,
) -> PotholeResponse:
    """
    Create a new pothole entry in the database.
    """
    try:
        result = await pothole_service.create_pothole(pothole)
        return result  # type: ignore
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create pothole: {str(e)}"
        )


@router.patch(
    "/{pothole_id}",
    response_model=PotholeResponse,
    summary="Update a pothole",
)
async def update_pothole(
    pothole_id: str,
    pothole_update: PotholeUpdate,
) -> PotholeResponse:
    """
    Update an existing poth PotholeResponseole.
    """
    pothole = await pothole_service.update_pothole(
        pothole_id,
        pothole_update,
    )
    
    if not pothole:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pothole {pothole_id} not found"
        )
    
    pothole["_id"] = str(pothole["_id"])
    return pothole  # type: ignore


@router.delete(
    "/{pothole_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a pothole",
)
async def delete_pothole(
    pothole_id: str,
) -> None:
    """
    Delete a pothole from the database.
    """
    success = await pothole_service.delete_pothole(pothole_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pothole {pothole_id} not found"
        )

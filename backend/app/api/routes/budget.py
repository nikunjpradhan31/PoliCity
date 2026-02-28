"""Budget management routes."""

from typing import Optional

from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import PlainTextResponse

from app.api.deps import get_current_active_user
from app.models.user import CurrentUser
from app.models.budget import (
    BudgetCreate,
    BudgetUpdate,
    BudgetResponse,
    BudgetListResponse,
)
from app.services.budget_service import budget_service
from app.utils.csv_parser import (
    parse_budget_csv,
    CSVParseError,
    validate_budget_csv_format,
)

router = APIRouter(prefix="/budget", tags=["budget"])


@router.get(
    "",
    response_model=BudgetListResponse,
    summary="Get budgets",
)
async def get_budgets(
    city: Optional[str] = Query(None, description="Filter by city"),
    year: Optional[int] = Query(None, description="Filter by year"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum records to return"),
) -> BudgetListResponse:
    """
    Get budgets with optional filters.
    
    Returns a paginated list of budgets.
    """
    budgets, total = await budget_service.get_budgets(
        city=city,
        year=year,
        skip=skip,
        limit=limit,
    )
    
    # Convert ObjectId to string for response
    formatted_budgets = []
    for b in budgets:
        b["_id"] = str(b["_id"])
        formatted_budgets.append(b)
    
    return BudgetListResponse(
        budgets=formatted_budgets,  # type: ignore
        total=total,
    )


@router.get(
    "/{budget_id}",
    response_model=BudgetResponse,
    summary="Get budget by ID",
)
async def get_budget(
    budget_id: str = Query(..., description="Budget ID"),
) -> BudgetResponse:
    """
    Get a specific budget by ID.
    """
    budget = await budget_service.get_budget_by_id(budget_id)
    
    if not budget:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Budget {budget_id} not found"
        )
    
    budget["_id"] = str(budget["_id"])
    return budget  # type: ignore


@router.post(
    "",
    response_model=BudgetResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new budget (requires auth)",
)
async def create_budget(
    budget: BudgetCreate,
    current_user: CurrentUser = Depends(get_current_active_user),
) -> BudgetResponse:
    """
    Create a new budget entry.
    
    Requires authentication.
    """
    try:
        result = await budget_service.create_budget(
            budget,
            uploaded_by=current_user.sub,
        )
        return result  # type: ignore
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create budget: {str(e)}"
        )


@router.post(
    "/upload-csv",
    response_model=BudgetResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload budget from CSV (requires auth)",
)
async def upload_budget_csv(
    csv_content: str,
    city: str = Query(..., description="City name"),
    year: int = Query(..., ge=2000, le=2100, description="Budget year"),
    current_user: CurrentUser = Depends(get_current_active_user),
) -> BudgetResponse:
    """
    Upload a budget from CSV content.
    
    Requires authentication.
    
    CSV format:
    ```csv
    category,amount,description
    Road Repair,50000,Annual road maintenance
    Pothole Fixing,25000,Priority pothole repairs
    ```
    """
    # Validate CSV format
    if not validate_budget_csv_format(csv_content):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid CSV format. Required columns: category, amount"
        )
    
    try:
        parsed = parse_budget_csv(csv_content, city, year)
        
        from app.models.budget import BudgetCreate
        budget = BudgetCreate(
            city=parsed["city"],
            year=parsed["year"],
            total_budget=parsed["total_budget"],
            items=parsed["items"],
        )
        
        result = await budget_service.create_budget(
            budget,
            uploaded_by=current_user.sub,
        )
        
        return result  # type: ignore
        
    except CSVParseError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload budget: {str(e)}"
        )


@router.patch(
    "/{budget_id}",
    response_model=BudgetResponse,
    summary="Update a budget",
)
async def update_budget(
    budget_id: str,
    budget_update: BudgetUpdate,
    current_user: CurrentUser = Depends(get_current_active_user),
) -> BudgetResponse:
    """
    Update an existing budget.
    
    Requires authentication.
    """
    budget = await budget_service.update_budget(
        budget_id,
        budget_update,
    )
    
    if not budget:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Budget {budget_id} not found"
        )
    
    budget["_id"] = str(budget["_id"])
    return budget  # type: ignore


@router.delete(
    "/{budget_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a budget",
)
async def delete_budget(
    budget_id: str,
    current_user: CurrentUser = Depends(get_current_active_user),
) -> None:
    """
    Delete a budget from the database.
    
    Requires authentication.
    """
    success = await budget_service.delete_budget(budget_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Budget {budget_id} not found"
        )

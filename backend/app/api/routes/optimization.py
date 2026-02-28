"""Optimization routes."""

from typing import Optional

from fastapi import APIRouter, HTTPException, Query, status

from app.api.deps import get_current_active_user
from app.models.user import CurrentUser
from app.services.optimization_service import (
    OptimizationService,
    OptimizationStrategy,
)
from app.services.report_service import report_service

router = APIRouter(prefix="/optimize", tags=["optimization"])


class OptimizationRequest:
    """Request model for optimization."""
    
    def __init__(
        self,
        budget: float,
        strategy: str = "severity",
        city: Optional[str] = None,
        year: Optional[int] = None,
    ):
        self.budget = budget
        self.strategy = strategy
        self.city = city
        self.year = year


@router.post(
    "",
    response_model=dict,
    status_code=status.HTTP_201_CREATED,
    summary="Run optimization (requires auth)",
)
async def run_optimization(
    budget: float = Query(..., ge=0, description="Available budget"),
    strategy: str = Query("severity", description="Optimization strategy"),
    city: Optional[str] = Query(None, description="City name"),
    year: Optional[int] = Query(None, description="Budget year"),
    current_user: CurrentUser = Depends(get_current_active_user),
) -> dict:
    """
    Run optimization to select potholes for repair within budget.
    
    Requires authentication.
    
    Strategies:
    - **cost**: Prioritize lowest cost repairs
    - **severity**: Prioritize highest severity potholes
    - **coverage**: Maximize number of repairs within budget
    """
    # Validate strategy
    try:
        strategy_enum = OptimizationStrategy(strategy)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid strategy. Must be one of: {[s.value for s in OptimizationStrategy]}"
        )
    
    # If no city provided, try to get from budget
    if not city:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="City parameter is required"
        )
    
    try:
        service = OptimizationService()
        result = await service.run_optimization(
            city=city,
            budget=budget,
            strategy=strategy_enum,
            year=year,
        )
        
        # Generate report for the optimization
        await report_service.generate_report(
            run_id=result["run_id"],
            optimization_result=result,
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Optimization failed: {str(e)}"
        )


@router.get(
    "/history",
    response_model=dict,
    summary="Get optimization history",
)
async def get_optimization_history(
    city: Optional[str] = Query(None, description="Filter by city"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum records to return"),
) -> dict:
    """
    Get optimization history.
    
    Returns a list of past optimization runs.
    """
    service = OptimizationService()
    results, total = await service.get_optimizations(
        city=city,
        skip=skip,
        limit=limit,
    )
    
    # Convert ObjectId to string
    formatted_results = []
    for r in results:
        r["_id"] = str(r["_id"])
        formatted_results.append(r)
    
    return {
        "optimizations": formatted_results,
        "total": total,
    }

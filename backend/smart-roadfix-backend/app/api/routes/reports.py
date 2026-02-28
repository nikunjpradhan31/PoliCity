"""Report generation routes."""

from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import JSONResponse

from app.api.deps import get_current_active_user
from app.models.user import CurrentUser
from app.services.report_service import report_service

router = APIRouter(prefix="/report", tags=["reports"])


@router.get(
    "/{run_id}",
    response_model=dict,
    summary="Get report by optimization run ID",
)
async def get_report(
    run_id: str = Query(..., description="Optimization run ID"),
    current_user: CurrentUser = Depends(get_current_active_user),
) -> dict:
    """
    Get a report for an optimization run.
    
    Requires authentication.
    """
    report = await report_service.get_report_by_run_id(run_id)
    
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report for run {run_id} not found"
        )
    
    report["_id"] = str(report["_id"])
    return report


@router.get(
    "/{run_id}/download",
    response_model=dict,
    summary="Download report",
)
async def download_report(
    run_id: str = Query(..., description="Optimization run ID"),
    current_user: CurrentUser = Depends(get_current_active_user),
) -> JSONResponse:
    """
    Download report data (stub).
    
    Requires authentication.
    
    In production, this would return CSV or PDF file.
    """
    download_data = await report_service.get_report_download(run_id)
    
    if not download_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report for run {run_id} not found"
        )
    
    return JSONResponse(
        content=download_data["data"],
        headers={
            "Content-Disposition": f"attachment; filename={download_data['filename']}"
        }
    )


@router.get(
    "",
    response_model=dict,
    summary="Get all reports",
)
async def get_reports(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum records to return"),
    current_user: CurrentUser = Depends(get_current_active_user),
) -> dict:
    """
    Get all generated reports.
    
    Requires authentication.
    """
    reports, total = await report_service.get_reports(
        skip=skip,
        limit=limit,
    )
    
    # Convert ObjectId to string
    formatted_reports = []
    for r in reports:
        r["_id"] = str(r["_id"])
        formatted_reports.append(r)
    
    return {
        "reports": formatted_reports,
        "total": total,
    }

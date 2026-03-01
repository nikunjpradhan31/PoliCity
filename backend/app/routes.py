"""
API routes for PoliCity API.
"""
from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
import joblib
import os

from app.models import (
    MessageResponse, 
    User,
    InfrastructureReportRequest,
    MultiInfrastructureReportRequest,
    InfrastructureReportResponse,
    ReportStatusResponse,
    IncidentDetailResponse
)
from app.db import get_database, get_collection
from app.workflows.infrastructure import workflow
from app.workflows.multi_infrastructure import multi_workflow

from fastapi.responses import Response
# Create API router
router = APIRouter()

# Get the base directory for model loading
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Load ML models
try:
    vectorizer = joblib.load(os.path.join(BASE_DIR, "tfidf_vectorizer.pkl"))
    clf = joblib.load(os.path.join(BASE_DIR, "issue_classifier.pkl"))
except Exception as e:
    print(f"Warning: Could not load ML models: {e}")
    vectorizer = None
    clf = None


def predict_issue(text: str) -> str:
    """
    Predict the issue class using the loaded ML models.
    
    Args:
        text: The summary text to classify.
    
    Returns:
        The predicted class label.
    """
    if vectorizer is None or clf is None or not text:
        return "Unknown"
    
    try:
        vec = vectorizer.transform([text])
        return clf.predict(vec)[0]
    except Exception as e:
        print(f"Error predicting issue: {e}")
        return "Unknown"


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


class IssueDataPoint(BaseModel):
    """
    Data point model for SeeClickFix issues.
    """
    longitude: float = Field(..., description="Longitude coordinate")
    latitude: float = Field(..., description="Latitude coordinate")
    address: Optional[str] = Field(None, description="Issue address")
    description: Optional[str] = Field(None, description="Issue description")
    id: str = Field(..., description="MongoDB document ID")
    scf_id: int = Field(..., description="SeeClickFix issue ID")
    classification: str = Field(..., description="ML-predicted issue class")


@router.get("/issues/bounds", response_model=List[IssueDataPoint])
async def get_issues_by_bounds(
    long_1: float = Query(..., description="Minimum longitude"),
    lat_1: float = Query(..., description="Minimum latitude"),
    long_2: float = Query(..., description="Maximum longitude"),
    lat_2: float = Query(..., description="Maximum latitude"),
    count: int = Query(50, description="Maximum number of results", ge=1, le=1000)
):
    """
    Get SeeClickFix issues within a bounding box.
    
    Retrieves issues with status='Open' within the specified geographic bounds
    and classifies each issue's summary using ML models.
    
    Args:
        long_1: Minimum longitude (west boundary)
        lat_1: Minimum latitude (south boundary)
        long_2: Maximum longitude (east boundary)
        lat_2: Maximum latitude (north boundary)
        count: Maximum number of results (default 50, max 1000)
    
    Returns:
        List of IssueDataPoint with classified issues.
    """
    collection = get_collection("seeclickfix_issues")
    
    # Determine min/max for longitude and latitude
    min_long = min(long_1, long_2)
    max_long = max(long_1, long_2)
    min_lat = min(lat_1, lat_2)
    max_lat = max(lat_1, lat_2)
    
    # Build query for bounding box and status
    query = {
        "status": "Open",
        "longitude": {"$gte": min_long, "$lte": max_long},
        "latitude": {"$gte": min_lat, "$lte": max_lat}
    }
    
    # Fetch issues from MongoDB
    issues = list(collection.find(query).limit(count))
    
    # Process and classify each issue
    result = []
    for issue in issues:
        # Get the summary for classification
        summary = issue.get("summary", "")
        
        # Classify the issue using ML models
        classification = predict_issue(summary) if summary else "Unknown"
        
        data_point = IssueDataPoint(
            longitude=issue.get("longitude", 0.0),
            latitude=issue.get("latitude", 0.0),
            address=issue.get("address"),
            description=issue.get("description"),
            id=str(issue.get("_id", "")),
            scf_id=issue.get("scf_id", 0),
            classification=classification
        )
        result.append(data_point)
    
    return result


# ============================================
# Infrastructure Reporting Workflow Endpoints
# ============================================
from datetime import datetime
from fastapi import BackgroundTasks

@router.post("/workflow/infrastructure-report", response_model=InfrastructureReportResponse)
async def generate_infrastructure_report(request: InfrastructureReportRequest, background_tasks: BackgroundTasks):
    """
    Initiates a new report generation job.
    """
    try:
        # Start the workflow in background or return immediately if cached
        response = await workflow.start_pipeline(request.model_dump())
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Workflow initiation failed: {str(e)}")

@router.post("/workflow/infrastructure-report/bulk", response_model=InfrastructureReportResponse)
async def generate_multi_infrastructure_report(request: MultiInfrastructureReportRequest, background_tasks: BackgroundTasks):
    """
    Initiates a new multi-incident report generation job.
    """
    try:
        response = await multi_workflow.start_pipeline(request.model_dump())
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Multi-workflow initiation failed: {str(e)}")

@router.get("/workflow/infrastructure-report/{report_id}", response_model=ReportStatusResponse)
async def get_report_status(report_id: str):
    """
    Poll for the status of an in-progress report.
    """
    try:
        if report_id.startswith("MULTI-INC-"):
            status = await multi_workflow.get_status(report_id)
        else:
            status = await workflow.get_status(report_id)
            
        if not status:
            raise HTTPException(status_code=404, detail="Report not found")
        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get status: {str(e)}")

@router.get("/workflow/infrastructure-report/incident/{incident_id}", response_model=IncidentDetailResponse)
async def get_incident_details(incident_id: str):
    """
    Retrieve the full saved record for a known incident directly from MongoDB.
    """
    try:
        if incident_id.startswith("MULTI-INC-"):
            details = await multi_workflow.get_incident(incident_id)
        else:
            details = await workflow.get_incident(incident_id)
            
        if not details:
            raise HTTPException(status_code=404, detail="Incident not found")
        return details
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get incident: {str(e)}")



@router.get("/workflow/infrastructure-report/incident/{incident_id}/pdf")
async def download_incident_pdf(incident_id: str):
    """
    Generate and download the infrastructure incident PDF.
    """
    try:
        if incident_id.startswith("MULTI-INC-"):
            pdf_bytes = await multi_workflow.get_incident_pdf(incident_id)
        else:
            pdf_bytes = await workflow.get_incident_pdf(incident_id)

        if not pdf_bytes:
            raise HTTPException(status_code=404, detail="Incident or PDF data not found")

        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename={incident_id}.pdf"
            }
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate PDF: {str(e)}")

import asyncio

@router.websocket("/workflow/infrastructure-report/{report_id}/ws")
async def websocket_endpoint(websocket: WebSocket, report_id: str):
    await websocket.accept()
    try:
        while True:
            # Poll status every 2 seconds and push to client
            if report_id.startswith("MULTI-INC-"):
                status = await multi_workflow.get_status(report_id)
            else:
                status = await workflow.get_status(report_id)
                
            if status:
                await websocket.send_json(status)
                if status.get("status") in ["complete", "failed"]:
                    break
            else:
                await websocket.send_json({"error": "Report not found"})
                break
            await asyncio.sleep(2)
    except WebSocketDisconnect:
        print(f"Client disconnected from report {report_id}")
    except Exception as e:
        await websocket.close(code=1011, reason=str(e))


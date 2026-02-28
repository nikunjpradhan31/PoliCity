"""Open311 API service for fetching pothole data."""

from typing import Optional

import httpx

from app.core.config import get_settings
from app.core.logging import logger

settings = get_settings()


class Open311Service:
    """Service for interacting with Open311 API."""
    
    def __init__(self) -> None:
        self.base_url = settings.OPEN311_BASE_URL
        self.api_key = settings.OPEN311_API_KEY
        self.service_code = settings.OPEN311_SERVICE_CODE
    
    async def fetch_service_requests(
        self,
        city: str,
        service_code: Optional[str] = None,
        status: Optional[str] = None,
    ) -> list[dict]:
        """
        Fetch service requests from Open311 API.
        
        Args:
            city: City name
            service_code: Open311 service code (defaults to POTHOLE)
            status: Filter by status
            
        Returns:
            List of service requests
        """
        params = {
            "service_code": service_code or self.service_code,
        }
        
        if status:
            params["status"] = status
        
        headers = {}
        if self.api_key:
            headers["X-API-Key"] = self.api_key
        
        url = f"{self.base_url}/requests.json"
        
        logger.info(f"Fetching Open311 requests for city: {city}")
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.get(url, params=params, headers=headers)
                response.raise_for_status()
                requests = response.json()
                
                logger.info(f"Fetched {len(requests)} requests from Open311")
                return requests
                
            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP error fetching Open311 data: {e}")
                raise
            except httpx.RequestError as e:
                logger.error(f"Request error fetching Open311 data: {e}")
                raise
    
    def normalize_request(self, request: dict, city: str) -> dict:
        """
        Normalize Open311 request to internal schema.
        
        Args:
            request: Raw Open311 request
            city: City name
            
        Returns:
            Normalized pothole data
        """
        lat = request.get("lat")
        long_val = request.get("long")
        
        # Calculate severity score based on available data
        severity_score = self._calculate_severity(request)
        
        # Map Open311 status to internal status
        status = self._map_status(request.get("status", ""))
        
        # Parse datetime
        reported_at = request.get("requested_datetime")
        
        return {
            "external_id": request.get("service_request_id", ""),
            "description": request.get("description"),
            "latitude": lat,
            "longitude": long_val,
            "severity_score": severity_score,
            "status": status,
            "city": city,
            "reported_at": reported_at,
        }
    
    def _calculate_severity(self, request: dict) -> float:
        """Calculate severity score based on request data."""
        # Default severity calculation
        # In production, this would analyze description, images, etc.
        score = 50.0
        
        # Check for priority indicators in description
        description = request.get("description", "").lower()
        
        if any(word in description for word in ["urgent", "dangerous", "hazard"]):
            score = 90.0
        elif any(word in description for word in ["large", "big", "deep"]):
            score = 70.0
        elif any(word in description for word in ["small", "minor"]):
            score = 30.0
        
        return score
    
    def _map_status(self, open311_status: str) -> str:
        """Map Open311 status to internal status."""
        status_mapping = {
            "open": "open",
            "acknowledged": "in_progress",
            "closed": "completed",
            "completed": "completed",
        }
        
        return status_mapping.get(open311_status.lower(), "open")


# Singleton instance
open311_service = Open311Service()

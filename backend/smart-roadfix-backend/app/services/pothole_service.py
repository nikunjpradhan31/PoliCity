"""Pothole service for database operations."""

from datetime import datetime
from typing import Optional

from bson import ObjectId

from app.core.database import get_potholes_collection
from app.core.logging import logger
from app.models.pothole import (
    PotholeCreate,
    PotholeUpdate,
    PotholeInDB,
    GeoJSONPoint,
    PotholeStatus,
)
from app.services.open311_service import open311_service


class PotholeService:
    """Service for pothole database operations."""
    
    async def sync_from_open311(self, city: str) -> dict:
        """
        Fetch potholes from Open311 and store in MongoDB.
        
        Args:
            city: City name
            
        Returns:
            Sync result with counts
        """
        collection = get_potholes_collection()
        
        # Fetch from Open311
        raw_requests = await open311_service.fetch_service_requests(city)
        
        new_count = 0
        update_count = 0
        
        for request in raw_requests:
            normalized = open311_service.normalize_request(request, city)
            
            # Skip if missing required fields
            if not normalized.get("external_id") or not normalized.get("latitude"):
                continue
            
            # Create GeoJSON location
            location = {
                "type": "Point",
                "coordinates": [
                    normalized["longitude"],
                    normalized["latitude"]
                ]
            }
            
            # Parse reported_at
            reported_at = datetime.utcnow()
            if normalized.get("reported_at"):
                try:
                    reported_at = datetime.fromisoformat(
                        normalized["reported_at"].replace("Z", "+00:00")
                    )
                except (ValueError, AttributeError):
                    pass
            
            # Upsert pothole (prevent duplicates by external_id)
            now = datetime.utcnow()
            
            result = await collection.update_one(
                {"external_id": normalized["external_id"]},
                {
                    "$set": {
                        "external_id": normalized["external_id"],
                        "description": normalized.get("description"),
                        "location": location,
                        "severity_score": normalized.get("severity_score", 0.0),
                        "status": normalized.get("status", "open"),
                        "city": city,
                        "reported_at": reported_at,
                        "updated_at": now,
                    },
                    "$setOnInsert": {
                        "created_at": now,
                    }
                },
                upsert=True
            )
            
            if result.upserted_id:
                new_count += 1
            elif result.modified_count > 0:
                update_count += 1
        
        logger.info(
            f"Synced potholes for {city}: {new_count} new, {update_count} updated"
        )
        
        return {
            "city": city,
            "fetched": len(raw_requests),
            "new": new_count,
            "updated": update_count,
        }
    
    async def get_potholes(
        self,
        city: Optional[str] = None,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[list[PotholeInDB], int]:
        """
        Get potholes with optional filters.
        
        Args:
            city: Filter by city
            status: Filter by status
            skip: Number of records to skip
            limit: Maximum records to return
            
        Returns:
            Tuple of (potholes list, total count)
        """
        collection = get_potholes_collection()
        
        query = {}
        if city:
            query["city"] = city
        if status:
            query["status"] = status
        
        # Get total count
        total = await collection.count_documents(query)
        
        # Get paginated results
        cursor = collection.find(query).skip(skip).limit(limit)
        potholes = await cursor.to_list(length=limit)
        
        return potholes, total
    
    async def get_pothole_by_id(self, pothole_id: str) -> Optional[dict]:
        """Get a pothole by ID."""
        collection = get_potholes_collection()
        
        try:
            pothole = await collection.find_one({"_id": ObjectId(pothole_id)})
            return pothole
        except Exception as e:
            logger.error(f"Error fetching pothole {pothole_id}: {e}")
            return None
    
    async def create_pothole(self, pothole: PotholeCreate) -> dict:
        """Create a new pothole."""
        collection = get_potholes_collection()
        
        now = datetime.utcnow()
        document = {
            "external_id": pothole.external_id,
            "description": pothole.description,
            "location": {
                "type": "Point",
                "coordinates": [
                    pothole.location.coordinates[0],
                    pothole.location.coordinates[1]
                ]
            },
            "severity_score": pothole.severity_score,
            "status": pothole.status.value,
            "city": pothole.city,
            "reported_at": now,
            "created_at": now,
            "updated_at": now,
        }
        
        result = await collection.insert_one(document)
        
        return {
            "_id": str(result.inserted_id),
            **document,
        }
    
    async def update_pothole(
        self,
        pothole_id: str,
        pothole_update: PotholeUpdate,
    ) -> Optional[dict]:
        """Update a pothole."""
        collection = get_potholes_collection()
        
        update_data = pothole_update.model_dump(exclude_unset=True)
        
        if "status" in update_data:
            update_data["status"] = update_data["status"].value
        
        if not update_data:
            return await self.get_pothole_by_id(pothole_id)
        
        update_data["updated_at"] = datetime.utcnow()
        
        try:
            result = await collection.find_one_and_update(
                {"_id": ObjectId(pothole_id)},
                {"$set": update_data},
                return_document=True,
            )
            return result
        except Exception as e:
            logger.error(f"Error updating pothole {pothole_id}: {e}")
            return None
    
    async def delete_pothole(self, pothole_id: str) -> bool:
        """Delete a pothole."""
        collection = get_potholes_collection()
        
        try:
            result = await collection.delete_one({"_id": ObjectId(pothole_id)})
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Error deleting pothole {pothole_id}: {e}")
            return False


# Singleton instance
pothole_service = PotholeService()

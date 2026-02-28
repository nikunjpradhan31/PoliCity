"""Budget service for database operations."""

from datetime import datetime
from typing import Optional

from bson import ObjectId

from app.core.database import get_budgets_collection
from app.core.logging import logger
from app.models.budget import BudgetCreate, BudgetUpdate


class BudgetService:
    """Service for budget database operations."""
    
    async def create_budget(
        self,
        budget: BudgetCreate,
        uploaded_by: str,
    ) -> dict:
        """
        Create a new budget.
        
        Args:
            budget: Budget data
            uploaded_by: User ID who uploaded
            
        Returns:
            Created budget
        """
        collection = get_budgets_collection()
        
        now = datetime.utcnow()
        document = {
            "city": budget.city,
            "year": budget.year,
            "total_budget": budget.total_budget,
            "items": [item.model_dump() for item in budget.items],
            "uploaded_by": uploaded_by,
            "created_at": now,
            "updated_at": now,
        }
        
        result = await collection.insert_one(document)
        
        return {
            "_id": str(result.inserted_id),
            **document,
        }
    
    async def get_budgets(
        self,
        city: Optional[str] = None,
        year: Optional[int] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[list[dict], int]:
        """
        Get budgets with optional filters.
        
        Args:
            city: Filter by city
            year: Filter by year
            skip: Number of records to skip
            limit: Maximum records to return
            
        Returns:
            Tuple of (budgets list, total count)
        """
        collection = get_budgets_collection()
        
        query = {}
        if city:
            query["city"] = city
        if year:
            query["year"] = year
        
        # Get total count
        total = await collection.count_documents(query)
        
        # Get paginated results
        cursor = collection.find(query).skip(skip).limit(limit)
        budgets = await cursor.to_list(length=limit)
        
        return budgets, total
    
    async def get_budget_by_id(self, budget_id: str) -> Optional[dict]:
        """Get a budget by ID."""
        collection = get_budgets_collection()
        
        try:
            budget = await collection.find_one({"_id": ObjectId(budget_id)})
            return budget
        except Exception as e:
            logger.error(f"Error fetching budget {budget_id}: {e}")
            return None
    
    async def get_budget_by_city_year(
        self,
        city: str,
        year: int,
    ) -> Optional[dict]:
        """Get a budget by city and year."""
        collection = get_budgets_collection()
        
        budget = await collection.find_one({"city": city, "year": year})
        return budget
    
    async def update_budget(
        self,
        budget_id: str,
        budget_update: BudgetUpdate,
    ) -> Optional[dict]:
        """Update a budget."""
        collection = get_budgets_collection()
        
        update_data = budget_update.model_dump(exclude_unset=True)
        
        if "items" in update_data:
            update_data["items"] = [
                item.model_dump() if hasattr(item, 'model_dump') else item
                for item in update_data["items"]
            ]
        
        if not update_data:
            return await self.get_budget_by_id(budget_id)
        
        update_data["updated_at"] = datetime.utcnow()
        
        try:
            result = await collection.find_one_and_update(
                {"_id": ObjectId(budget_id)},
                {"$set": update_data},
                return_document=True,
            )
            return result
        except Exception as e:
            logger.error(f"Error updating budget {budget_id}: {e}")
            return None
    
    async def delete_budget(self, budget_id: str) -> bool:
        """Delete a budget."""
        collection = get_budgets_collection()
        
        try:
            result = await collection.delete_one({"_id": ObjectId(budget_id)})
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Error deleting budget {budget_id}: {e}")
            return False


# Singleton instance
budget_service = BudgetService()

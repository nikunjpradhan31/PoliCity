"""Optimization service for pothole repair optimization."""

import uuid
from datetime import datetime
from enum import Enum
from typing import Optional

from bson import ObjectId

from app.core.database import get_optimizations_collection, get_potholes_collection
from app.core.logging import logger
from app.models.pothole import PotholeStatus


class OptimizationStrategy(str, Enum):
    """Optimization strategy enumeration."""
    COST = "cost"
    SEVERITY = "severity"
    COVERAGE = "coverage"


# Estimated repair costs by severity (in USD)
REPAIR_COST_ESTIMATES = {
    "low": 50.0,      # $50 for minor potholes
    "medium": 150.0,  # $150 for moderate potholes
    "high": 300.0,    # $300 for severe potholes
}

# Cost per mile for travel
COST_PER_MILE = 2.0


class OptimizationService:
    """Service for optimizing pothole repairs."""
    
    async def run_optimization(
        self,
        city: str,
        budget: float,
        strategy: OptimizationStrategy,
        year: Optional[int] = None,
    ) -> dict:
        """
        Run optimization to select potholes for repair within budget.
        
        Args:
            city: City name
            budget: Available budget
            strategy: Optimization strategy (cost, severity, coverage)
            year: Optional year filter
            
        Returns:
            Optimization result
        """
        collection = get_potholes_collection()
        
        # Get all open potholes for the city
        query = {
            "city": city,
            "status": PotholeStatus.OPEN.value,
        }
        
        if year:
            query["year"] = year
        
        cursor = collection.find(query)
        potholes = await cursor.to_list(length=1000)
        
        logger.info(
            f"Running optimization for {city} with budget ${budget} "
            f"and strategy {strategy.value}"
        )
        
        # Add repair cost estimate to each pothole
        for pothole in potholes:
            pothole["repair_cost"] = self._estimate_repair_cost(
                pothole.get("severity_score", 50.0)
            )
        
        # Sort based on strategy
        if strategy == OptimizationStrategy.COST:
            # Sort by repair cost (lowest first)
            potholes.sort(key=lambda p: p.get("repair_cost", 0))
        elif strategy == OptimizationStrategy.SEVERITY:
            # Sort by severity (highest first)
            potholes.sort(key=lambda p: p.get("severity_score", 0), reverse=True)
        elif strategy == OptimizationStrategy.COVERAGE:
            # Sort by severity/cost ratio
            for p in potholes:
                cost = p.get("repair_cost", 1)
                severity = p.get("severity_score", 0)
                p["efficiency_score"] = severity / cost
            potholes.sort(key=lambda p: p.get("efficiency_score", 0), reverse=True)
        
        # Select potholes within budget
        selected_potholes = []
        total_repair_cost = 0.0
        remaining_budget = budget
        
        for pothole in potholes:
            cost = pothole.get("repair_cost", 0)
            if cost <= remaining_budget:
                selected_potholes.append(pothole)
                total_repair_cost += cost
                remaining_budget -= cost
        
        # Estimate travel cost (simplified: based on number of potholes)
        estimated_travel_cost = len(selected_potholes) * COST_PER_MILE
        
        # Generate run ID
        run_id = str(uuid.uuid4())
        
        # Store optimization result
        result = {
            "run_id": run_id,
            "city": city,
            "budget": budget,
            "strategy": strategy.value,
            "selected_potholes": [
                {
                    "id": str(p.get("_id")),
                    "external_id": p.get("external_id"),
                    "severity_score": p.get("severity_score"),
                    "repair_cost": p.get("repair_cost"),
                    "location": p.get("location"),
                }
                for p in selected_potholes
            ],
            "total_repair_cost": total_repair_cost,
            "estimated_travel_cost": estimated_travel_cost,
            "remaining_budget": remaining_budget - estimated_travel_cost,
            "total_potholes_considered": len(potholes),
            "potholes_selected": len(selected_potholes),
            "created_at": datetime.utcnow(),
        }
        
        # Save to database
        optim_collection = get_optimizations_collection()
        await optim_collection.insert_one(result)
        
        logger.info(
            f"Optimization complete: selected {len(selected_potholes)} "
            f"potholes with total cost ${total_repair_cost}"
        )
        
        return result
    
    def _estimate_repair_cost(self, severity_score: float) -> float:
        """Estimate repair cost based on severity score."""
        if severity_score < 30:
            return REPAIR_COST_ESTIMATES["low"]
        elif severity_score < 70:
            return REPAIR_COST_ESTIMATES["medium"]
        else:
            return REPAIR_COST_ESTIMATES["high"]
    
    async def get_optimization_by_id(self, run_id: str) -> Optional[dict]:
        """Get optimization result by run ID."""
        collection = get_optimizations_collection()
        
        result = await collection.find_one({"run_id": run_id})
        return result
    
    async def get_optimizations(
        self,
        city: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[list[dict], int]:
        """Get optimization history."""
        collection = get_optimizations_collection()
        
        query = {}
        if city:
            query["city"] = city
        
        total = await collection.count_documents(query)
        cursor = collection.find(query).skip(skip).limit(limit).sort(
            "created_at", -1
        )
        results = await cursor.to_list(length=limit)
        
        return results, total


# Singleton instance
optimization_service = OptimizationService()

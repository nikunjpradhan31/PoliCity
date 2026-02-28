"""Report service for generating reports."""

from datetime import datetime
from typing import Optional

from app.core.database import get_reports_collection, get_potholes_collection
from app.core.logging import logger


class ReportService:
    """Service for generating reports."""
    
    async def generate_report(
        self,
        run_id: str,
        optimization_result: Optional[dict] = None,
    ) -> dict:
        """
        Generate a report for an optimization run.
        
        Args:
            run_id: Optimization run ID
            optimization_result: Optional optimization result data
            
        Returns:
            Report data
        """
        collection = get_reports_collection()
        
        # If no optimization result provided, fetch it
        if not optimization_result:
            from app.services.optimization_service import optimization_service
            optimization_result = await optimization_service.get_optimization_by_id(
                run_id
            )
        
        if not optimization_result:
            return None
        
        # Generate summary
        selected = optimization_result.get("selected_potholes", [])
        total_repair_cost = optimization_result.get("total_repair_cost", 0)
        estimated_travel = optimization_result.get("estimated_travel_cost", 0)
        
        # Calculate metrics
        total_severity = sum(
            p.get("severity_score", 0) for p in selected
        )
        avg_severity = total_severity / len(selected) if selected else 0
        
        metrics = {
            "total_potholes_repaired": len(selected),
            "total_repair_cost": total_repair_cost,
            "travel_cost": estimated_travel,
            "total_spent": total_repair_cost + estimated_travel,
            "average_severity": round(avg_severity, 2),
            "budget_utilization": round(
                (total_repair_cost / optimization_result.get("budget", 1)) * 100,
                2
            ),
            "city": optimization_result.get("city"),
            "strategy": optimization_result.get("strategy"),
        }
        
        # Generate summary text
        summary = (
            f"Optimization Report for {metrics['city']}\n"
            f"Strategy: {metrics['strategy']}\n"
            f"Repaired {metrics['total_potholes_repaired']} potholes "
            f"with total cost ${metrics['total_spent']:.2f} "
            f"(Budget utilization: {metrics['budget_utilization']:.1f}%)"
        )
        
        # Generate report
        report = {
            "run_id": run_id,
            "summary": summary,
            "metrics": metrics,
            "download_url": f"/api/v1/reports/{run_id}/download",
            "created_at": datetime.utcnow(),
        }
        
        # Store report
        await collection.insert_one(report)
        
        logger.info(f"Generated report for optimization run {run_id}")
        
        return report
    
    async def get_report_by_run_id(self, run_id: str) -> Optional[dict]:
        """Get a report by run ID."""
        collection = get_reports_collection()
        
        report = await collection.find_one({"run_id": run_id})
        return report
    
    async def get_reports(
        self,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[list[dict], int]:
        """Get all reports."""
        collection = get_reports_collection()
        
        total = await collection.count_documents({})
        cursor = collection.find({}).skip(skip).limit(limit).sort(
            "created_at", -1
        )
        reports = await cursor.to_list(length=limit)
        
        return reports, total
    
    async def get_report_download(self, run_id: str) -> Optional[dict]:
        """
        Get report data for download (stub).
        
        Returns CSV or JSON data for the report.
        """
        report = await self.get_report_by_run_id(run_id)
        
        if not report:
            return None
        
        # In production, this would generate actual CSV/PDF
        # For now, return the report data
        return {
            "format": "json",
            "data": report,
            "filename": f"report_{run_id}.json",
        }


# Singleton instance
report_service = ReportService()

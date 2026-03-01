import uuid
from datetime import datetime
from typing import Dict, Any, List

from app.services.mongo import (
    get_incident,
    save_incident,
    update_incident_status,
    get_agent_output,
    save_agent_output,
    delete_agent_output
)
from app.db import get_collection

from app.agents.thinking import ThinkingAgent
from app.agents.report_gen import ReportGeneratorAgent
from app.agents.graph import GraphGeneratorAgent

class InfrastructureWorkflow:
    def __init__(self):
        self.thinking_agent = ThinkingAgent()
        self.report_agent = ReportGeneratorAgent()
        self.graph_agent = GraphGeneratorAgent()
        self.agent_collections = {
            "thinking": "agent_thinking",
            "report": "agent_report"
        }

    async def start_pipeline(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Initiates or resumes a workflow.
        Returns initial status response.
        In a real background tasks setup, the actual execution happens asynchronously.
        Here we run it but you might want to yield or launch it via asyncio.create_task.
        For simplicity, we will run it inline or assume it is run via background_tasks in route.
        """
        incident_id = request_data.get("incident_id")
        force_refresh = request_data.get("force_refresh", [])
        
        is_new = False
        if not incident_id:
            incident_id = f"INC-{datetime.utcnow().strftime('%Y%m%d')}-000{uuid.uuid4().hex[:4]}"
            is_new = True

        incident = await get_incident(incident_id) if not is_new else None

        if incident and incident.get("status") == "complete" and not force_refresh:
            # Already completed
            return {
                "report_id": incident_id,
                "incident_id": incident_id,
                "status": "complete",
                "progress": 100,
                "cache_hit": True,
                "agents_skipped": ["thinking", "report"],
                "result": {"report_url": incident.get("report_url", "Report already generated")}
            }

        collection = get_collection("seeclickfix_issues")
        
        from bson.objectid import ObjectId
        from bson.errors import InvalidId
        try:
            query_id = ObjectId(incident_id)
        except InvalidId:
            query_id = incident_id
            
        doc = collection.find_one({"_id": query_id})
        if not doc:
            doc = {}
        else: 
            doc["incident_id"] = str(doc["_id"])
            del doc["_id"]
            
            import json
            # Convert non-JSON types (like datetime) to strings so it remains a "json data type"
            doc = json.loads(json.dumps(doc, default=str))
            
        request_data["issue_data"] = doc
        # Initialize incident if new
        if not incident:
            incident = {
                "incident_id": incident_id,
                "created_at": datetime.utcnow().isoformat() + "Z",
                "updated_at": datetime.utcnow().isoformat() + "Z",
                "status": "running",
                "inputs": {
                    "issue_type": request_data.get("issue_type"),
                    "location": request_data.get("location"),
                    "fiscal_year": request_data.get("fiscal_year"),
                    "image_url": request_data.get("image_url"),
                    "issue_data": request_data.get("issue_data")
                },
                "pipeline_run": {
                    "started_at": datetime.utcnow().isoformat() + "Z",
                    "completed_at": None,
                    "total_duration_ms": 0,
                    "agents_completed": [],
                    "agents_skipped": [],
                    "agents_failed": []
                }
            }
            await save_incident(incident_id, incident)

        # In a typical setup, we'd spawn a background task for `_run_agents`.
        # To avoid blocking, we will spawn it using asyncio if we can, 
        # but since FastAPI uses await, returning here and letting background task run is best.
        # But we don't have the background task passed directly inside start_pipeline easily.
        # Actually, `routes.py` expects `start_pipeline` to return response, and maybe `start_pipeline` starts the background task?
        # Let's just execute it and return once started. Oh, `routes.py` does:
        # response = await workflow.start_pipeline(request.model_dump())
        # We can run it directly for now, or use asyncio.create_task
        import asyncio
        asyncio.create_task(self._run_agents(incident_id, request_data, force_refresh, incident))

        return {
            "report_id": incident_id,
            "incident_id": incident_id,
            "status": "running",
            "progress": 0,
            "cache_hit": False,
            "agents_skipped": []
        }

    async def _run_agents(self, incident_id: str, request_data: dict, force_refresh: list, incident: dict):
        force_refresh = force_refresh or []
        start_time = datetime.utcnow()
        inputs = incident["inputs"]
        
        # Thinking Agent Step
        thinking_coll = self.agent_collections["thinking"]
        if "thinking" in force_refresh:
            await delete_agent_output(thinking_coll, incident_id)
        
        saved_thinking = await get_agent_output(thinking_coll, incident_id)
        
        if saved_thinking and saved_thinking.get("confidence", 0) >= 0.6:
            thinking_output = saved_thinking["data"]
            incident["pipeline_run"]["agents_skipped"].append("thinking")
            await update_incident_status(incident_id, "running", {"pipeline_run": incident["pipeline_run"], "progress": 50})
        else:
            try:
                result = await self.thinking_agent.run(inputs)
                result["incident_id"] = incident_id
                result["run_count"] = saved_thinking.get("run_count", 0) + 1 if saved_thinking else 1
                await save_agent_output(thinking_coll, incident_id, result)
                thinking_output = result["data"]
                incident["pipeline_run"]["agents_completed"].append("thinking")
                await update_incident_status(incident_id, "running", {"pipeline_run": incident["pipeline_run"], "progress": 50})
            except Exception as e:
                incident["pipeline_run"]["agents_failed"].append("thinking")
                await update_incident_status(incident_id, "failed", {"error": str(e)})
                return

        # Report Generator Step
        report_coll = self.agent_collections["report"]
        if "report" in force_refresh:
            await delete_agent_output(report_coll, incident_id)
            
        saved_report = await get_agent_output(report_coll, incident_id)
        
        if saved_report and saved_report.get("confidence", 0) >= 0.6:
            report_output = saved_report["data"]
            incident["pipeline_run"]["agents_skipped"].append("report")
        else:
            try:
                report_inputs = {
                    "user_inputs": inputs,
                    "thinking_output": thinking_output
                }
                result = await self.report_agent.run(report_inputs)
                result["incident_id"] = incident_id
                result["run_count"] = saved_report.get("run_count", 0) + 1 if saved_report else 1
                await save_agent_output(report_coll, incident_id, result)
                report_output = result["data"]
                incident["pipeline_run"]["agents_completed"].append("report")
            except Exception as e:
                incident["pipeline_run"]["agents_failed"].append("report")
                await update_incident_status(incident_id, "failed", {"error": str(e)})
                return

        # Finish Workflow
        end_time = datetime.utcnow()
        duration = int((end_time - start_time).total_seconds() * 1000)
        incident["pipeline_run"]["completed_at"] = end_time.isoformat() + "Z"
        incident["pipeline_run"]["total_duration_ms"] = duration
        
        # update incident
        await update_incident_status(
            incident_id, 
            "complete", 
            {
                "pipeline_run": incident["pipeline_run"], 
                "progress": 100, 
                "report_url": f"/api/v1/workflow/infrastructure-report/{incident_id}/download"
            }
        )

    async def get_status(self, report_id: str) -> Dict[str, Any]:
        incident = await get_incident(report_id)
        if not incident:
            return None
        
        return {
            "report_id": report_id,
            "incident_id": report_id,
            "status": incident.get("status", "unknown"),
            "progress": incident.get("progress", 0),
            "current_agent": "report" if "thinking" in incident.get("pipeline_run", {}).get("agents_completed", []) else "thinking",
            "cache_hit": len(incident.get("pipeline_run", {}).get("agents_skipped", [])) > 0,
            "agents_completed": incident.get("pipeline_run", {}).get("agents_completed", []),
            "agents_skipped": incident.get("pipeline_run", {}).get("agents_skipped", []),
            "agents_failed": incident.get("pipeline_run", {}).get("agents_failed", []),
            "result": {"report_url": incident.get("report_url")} if incident.get("report_url") else None,
            "error": incident.get("error")
        }

    async def get_incident(self, incident_id: str) -> Dict[str, Any]:
        incident = await get_incident(incident_id)
        if not incident:
            return None
            
        thinking_out = await get_agent_output(self.agent_collections["thinking"], incident_id)
        if thinking_out and "_id" in thinking_out:
            thinking_out["_id"] = str(thinking_out["_id"])
            
        report_out = await get_agent_output(self.agent_collections["report"], incident_id)
        if report_out and "_id" in report_out:
            report_out["_id"] = str(report_out["_id"])
            
        if incident and "_id" in incident:
            incident["_id"] = str(incident["_id"])

        return {
            "incident_id": incident_id,
            "status": incident.get("status", "unknown"),
            "inputs": incident.get("inputs", {}),
            "pipeline_run": incident.get("pipeline_run", {}),
            "agent_outputs": {
                "thinking": thinking_out,
                "report": report_out
            },
            "report_url": incident.get("report_url"),
            "created_at": incident.get("created_at"),
            "updated_at": incident.get("updated_at")
        }

workflow = InfrastructureWorkflow()

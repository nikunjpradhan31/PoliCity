import uuid
import asyncio
import json
from datetime import datetime
from typing import Dict, Any, List
from bson.objectid import ObjectId
from bson.errors import InvalidId

from app.services.mongo import (
    get_incident,
    save_incident,
    update_incident_status,
    get_agent_output,
    save_agent_output,
    delete_agent_output
)
from app.db import get_collection
from app.services.pdfcreator import generatepdf

from app.agents.multi_thinking import MultiThinkingAgent
from app.agents.multi_report_gen import MultiReportGeneratorAgent
from app.agents.graph import GraphGeneratorAgent
class MultiInfrastructureWorkflow:
    def __init__(self):
        self.thinking_agent = MultiThinkingAgent()
        self.report_agent = MultiReportGeneratorAgent()
        self.graph_agent = GraphGeneratorAgent()
        self.agent_collections = {
            "multi_thinking": "agent_multi_thinking",
            "multi_report": "agent_multi_report",
            "graph_agent": "agent_graph"
        }

    async def start_pipeline(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Initiates a multi-incident workflow.
        Returns initial status response.
        """
        incident_ids = request_data.get("incident_ids", [])
        force_refresh = request_data.get("force_refresh", [])
        
        report_id = f"MULTI-INC-{datetime.utcnow().strftime('%Y%m%d')}-000{uuid.uuid4().hex[:4]}"

        collection = get_collection("seeclickfix_issues")

        incidents_data = []
        for i_id in incident_ids:
            try:
                query_id = ObjectId(i_id)
            except InvalidId:
                query_id = i_id
                
            doc = await asyncio.to_thread(collection.find_one, {"_id": query_id})
            
            if doc:
                doc["incident_id"] = str(doc["_id"])
                del doc["_id"]
                doc = json.loads(json.dumps(doc, default=str))
                incidents_data.append(doc)
            else:
                incidents_data.append({"incident_id": str(i_id), "status": "Not Found"})
            
        request_data["incidents_data"] = incidents_data
        
        incident = {
            "incident_id": report_id,
            "created_at": datetime.utcnow().isoformat() + "Z",
            "updated_at": datetime.utcnow().isoformat() + "Z",
            "status": "running",
            "inputs": {
                "incident_ids": incident_ids,
                "fiscal_year": request_data.get("fiscal_year"),
                "incidents_data": request_data.get("incidents_data")
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
        await save_incident(report_id, incident)

        asyncio.create_task(self._run_agents(report_id, request_data, force_refresh, incident))

        return {
            "report_id": report_id,
            "incident_id": "MULTIPLE",
            "status": "running",
            "progress": 0,
            "cache_hit": False,
            "agents_skipped": []
        }

    async def _run_agents(self, report_id: str, request_data: dict, force_refresh: list, incident: dict):
        force_refresh = force_refresh or []
        start_time = datetime.utcnow()
        inputs = incident["inputs"]
        
        # Multi-Thinking Agent Step
        thinking_coll = self.agent_collections["multi_thinking"]
        if "multi_thinking" in force_refresh:
            await delete_agent_output(thinking_coll, report_id)
        
        saved_thinking = await get_agent_output(thinking_coll, report_id)
        
        if saved_thinking and saved_thinking.get("confidence", 0) >= 0.6:
            thinking_output = saved_thinking["data"]
            incident["pipeline_run"]["agents_skipped"].append("multi_thinking")
            await update_incident_status(report_id, "running", {"pipeline_run": incident["pipeline_run"], "progress": 50})
        else:
            try:
                result = await self.thinking_agent.run(inputs)
                result["incident_id"] = report_id
                result["run_count"] = saved_thinking.get("run_count", 0) + 1 if saved_thinking else 1
                await save_agent_output(thinking_coll, report_id, result)
                thinking_output = result["data"]
                incident["pipeline_run"]["agents_completed"].append("multi_thinking")
                await update_incident_status(report_id, "running", {"pipeline_run": incident["pipeline_run"], "progress": 50})
            except Exception as e:
                incident["pipeline_run"]["agents_failed"].append("multi_thinking")
                await update_incident_status(report_id, "failed", {"error": str(e)})
                return

        # Multi-Report Generator Step
        report_coll = self.agent_collections["multi_report"]
        if "multi_report" in force_refresh:
            await delete_agent_output(report_coll, report_id)
            
        saved_report = await get_agent_output(report_coll, report_id)
        
        if saved_report and saved_report.get("confidence", 0) >= 0.6:
            report_output = saved_report["data"]
            incident["pipeline_run"]["agents_skipped"].append("multi_report")
        else:
            try:
                report_inputs = {
                    "user_inputs": inputs,
                    "thinking_output": thinking_output
                }
                result = await self.report_agent.run(report_inputs)
                result["incident_id"] = report_id
                result["run_count"] = saved_report.get("run_count", 0) + 1 if saved_report else 1
                await save_agent_output(report_coll, report_id, result)
                report_output = result["data"]
                incident["pipeline_run"]["agents_completed"].append("multi_report")
            except Exception as e:
                incident["pipeline_run"]["agents_failed"].append("multi_report")
                await update_incident_status(report_id, "failed", {"error": str(e)})
                return


        # Graph Step
        graph_coll = self.agent_collections["graph_agent"]

        if "graph_agent" in force_refresh:
            await delete_agent_output(graph_coll, report_id)

        saved_graph_doc = await get_agent_output(graph_coll, report_id)

        if saved_graph_doc and saved_graph_doc.get("confidence", 0) >= 0.6:
            graph_output = saved_graph_doc["data"]
            incident["pipeline_run"]["agents_skipped"].append("graph_agent")
        else:
            try:
                graph_inputs = {
                    "user_inputs": inputs,
                    "thinking_output": thinking_output
                }

                result = await self.graph_agent.run(graph_inputs)

                result["incident_id"] = report_id
                result["run_count"] = (
                    saved_graph_doc.get("run_count", 0) + 1
                    if saved_graph_doc else 1
                )

                await save_agent_output(graph_coll, report_id, result)

                graph_output = result["data"]
                incident["pipeline_run"]["agents_completed"].append("graph_agent")

            except Exception as e:
                incident["pipeline_run"]["agents_failed"].append("graph_agent")
                await update_incident_status(report_id, "failed", {"error": str(e)})
                return


        # Finish Workflow
        end_time = datetime.utcnow()
        duration = int((end_time - start_time).total_seconds() * 1000)
        incident["pipeline_run"]["completed_at"] = end_time.isoformat() + "Z"
        incident["pipeline_run"]["total_duration_ms"] = duration
        
        await update_incident_status(
            report_id, 
            "complete", 
            {
                "pipeline_run": incident["pipeline_run"], 
                "progress": 100, 
                "report_url": f"/api/v1/workflow/infrastructure-report/{report_id}/pdf" # ✅ And here!
            }
        )

    async def get_status(self, report_id: str) -> Dict[str, Any]:
        incident = await get_incident(report_id)
        if not incident:
            return None
        
        return {
            "report_id": report_id,
            "incident_id": "MULTIPLE",
            "status": incident.get("status", "unknown"),
            "progress": incident.get("progress", 0),
            "current_agent": "multi_report" if "multi_thinking" in incident.get("pipeline_run", {}).get("agents_completed", []) else "multi_thinking",
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
            
        thinking_out = await get_agent_output(self.agent_collections["multi_thinking"], incident_id)
        if thinking_out and "_id" in thinking_out:
            thinking_out["_id"] = str(thinking_out["_id"])
            
        report_out = await get_agent_output(self.agent_collections["multi_report"], incident_id)
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
                "multi_thinking": thinking_out,
                "multi_report": report_out
            },
            "report_url": incident.get("report_url"),
            "created_at": incident.get("created_at"),
            "updated_at": incident.get("updated_at")
        }
    
    async def get_incident_pdf(self, incident_id: str) -> bytes:
        incident = await get_incident(incident_id)
        if not incident:
            return None

        report_out = await get_agent_output(self.agent_collections["multi_report"], incident_id)
        graph_doc = await get_agent_output(
            self.agent_collections["graph_agent"],
            incident_id
        )

        if not report_out or not graph_doc:
            return None

        graph_data = graph_doc.get("data", {})
        image_bytes = graph_data.get("image_bytes")

        if not image_bytes:
            return None

        pdf_bytes = generatepdf(
            report=report_out["data"] if "data" in report_out else report_out,
            image_bytes=image_bytes
        )

        return pdf_bytes

multi_workflow = MultiInfrastructureWorkflow()
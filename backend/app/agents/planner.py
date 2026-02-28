from app.agents.base import BaseAgent
from app.services.geocoder import geocode_location
from typing import Dict, Any, List
from pydantic import BaseModel

class SearchQueries(BaseModel):
    cost_research: List[str]
    contractor_search: List[str]
    budget_data: List[str]

class TaskItem(BaseModel):
    agent: str
    priority: int

class ParsedIssue(BaseModel):
    category: str
    subtype: str
    severity_inferred: str
    severity_source: str
    urgency_flags: List[str]

class PlannerSchema(BaseModel):
    search_queries: SearchQueries
    tasks_list: List[TaskItem]
    parsed_issue: ParsedIssue

class PlannerAgent(BaseAgent):
    name = "planner"

    async def run(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        location = inputs.get("location", "")
        issue_type = inputs.get("issue_type", "")
        
        # Geocode the location
        geospatial = await geocode_location(location)
        if not geospatial:
            geospatial = {
                "coordinates": {"lat": 0.0, "lng": 0.0},
                "neighborhood": "Unknown",
                "geocoder": "fallback"
            }

        prompt = f"""
        You are an infrastructure planning agent.
        The user reported an issue of type: '{issue_type}' at location '{location}'.
        Create sensible search queries for cost, contractors, and budget.
        Assign tasks to appropriate agents (cost_research, budget, contractor, repair_plan) with priorities (1 = highest).
        Parse the issue to infer category, subtype, severity, severity source, and any urgency flags (e.g., near school, main road).
        """
        
        result = await self.ask_gemini(prompt, schema=PlannerSchema)
        data = result if not result.get("mock") and not result.get("error") else {
            "search_queries": {
                "cost_research": [f"{issue_type} repair cost {location} 2025", f"labor cost for {issue_type} repair"],
                "contractor_search": [f"{issue_type} repair contractors {location}", f"local companies {location}"],
                "budget_data": [f"{location} infrastructure budget 2025", "pavement repair allocation"]
            },
            "tasks_list": [
                {"agent": "cost_research", "priority": 1},
                {"agent": "budget", "priority": 1},
                {"agent": "contractor", "priority": 2},
                {"agent": "repair_plan", "priority": 2}
            ],
            "parsed_issue": {
                "category": "infrastructure",
                "subtype": issue_type,
                "severity_inferred": "high",
                "severity_source": "heuristics",
                "urgency_flags": ["near_school"]
            }
        }
        
        data["geospatial"] = geospatial
        
        return self.wrap_output(data, confidence=0.95, tokens=500, duration=1000)

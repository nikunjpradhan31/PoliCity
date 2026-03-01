import json
from typing import Dict, Any
from google import genai
from google.genai import types

from .base import AgentBase

class MultiThinkingAgent(AgentBase):
    def __init__(self):
        super().__init__("multi_thinking")

    async def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes the Multi-Thinking Agent workflow.
        Input: issue_type, location, fiscal_year, incidents_data
        """
        fiscal_year = inputs.get("fiscal_year", 2025)
        incidents_data = inputs.get("incidents_data", [])
        incidents_data_str = json.dumps(incidents_data, default=str)

        prompt = f"""
        You are the Multi-Thinking Agent for a Multi-Agent Infrastructure Reporting Workflow.
        Your goal is to gather and analyze data regarding multiple grouped infrastructure incidents in the same area.
        Do NOT generate fake or simulated data; use your general knowledge and real-world estimates as much as possible, or use your tools to find realistic estimates.
        
        Input Data:
        - Fiscal Year: {fiscal_year}
        - List of Incidents Metadata: {incidents_data_str}

        Analyze the combined severity of these incidents, infer the geospatial bounds/neighborhood, estimate total material/labor costs for fixing all of them, define a unified repair plan or phases, list potential real-world contractors in the area, and analyze the fiscal year budget and grant opportunities.
        
        Output MUST be a valid JSON object matching the following schema EXACTLY (with no extra markdown wrappers or text before/after):
        {{
            "parsed_issue": {{"category": "...", "subtype": "...", "severity_inferred": "...", "severity_source": "...", "urgency_flags": [...]}},
            "geospatial": {{"coordinates": {{"lat": ..., "lng": ...}}, "neighborhood": "...", "district": "...", "geocoder": "gemini"}},
            "search_queries_used": {{"cost_research": [...], "contractor_search": [...], "budget_data": [...]}},
            "material_costs": [{{"item": "...", "unit": "...", "cost_low": ..., "cost_high": ..., "source": "..."}}],
            "labor_costs": [{{"role": "...", "hourly_rate_low": ..., "hourly_rate_high": ...}}],
            "time_estimates": [{{"task": "...", "hours_low": ..., "hours_high": ...}}],
            "historical_benchmarks": [{{"year": ..., "avg_cost": ..., "source": "..."}}],
            "total_cost_estimate": {{"low": ..., "high": ..., "currency": "USD"}},
            "repair_phases": [{{"phase": 1, "name": "...", "description": "...", "duration_hours": ..., "materials_needed": [...], "prerequisites": [...]}}],
            "recommended_method": "...",
            "alternative_methods": [{{"method": "...", "pros": "...", "cons": "...", "best_for": "..."}}],
            "permits_required": true/false,
            "safety_considerations": [...],
            "contractors": [{{"name": "...", "address": "...", "phone": "...", "rating": ..., "review_count": ..., "services": [...], "estimated_response_time": "...", "license": {{"number": "...", "status": "...", "verified_via": "...", "verified_at": "..."}}, "source": "..."}}],
            "contractor_search_sources_used": [...],
            "contractor_filters_applied": [...],
            "budget_analysis": {{"fiscal_year": {fiscal_year}, "total_infrastructure_budget": ..., "allocated_to_issue_type": ..., "remaining": ..., "source": "..."}},
            "feasibility": {{"within_budget": true/false, "cost_as_percentage_of_allocation": ..., "recommendation": "..."}},
            "grant_opportunities": [{{"program": "...", "eligible": true/false, "max_award": ..., "deadline": "...", "source": "..."}}],
            "budget_recommendations": [...],
            "alternatives_if_over_budget": [{{"option": "...", "reason": "...", "cost_savings": "..."}}],
            "sources": [{{"url": "...", "accessed": "...", "reliability": "..."}}]
        }}
        """

        if not self.client:
            raise RuntimeError("Gemini API key is not configured.")

        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.2,
                    response_mime_type="application/json"
                )
            )
            
            text = response.text.strip()
            data = json.loads(text)
            return data
        except Exception as e:
            raise Exception(f"Failed to generate Multi-Thinking Agent output: {str(e)}")

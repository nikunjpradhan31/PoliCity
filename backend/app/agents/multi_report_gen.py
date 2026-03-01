import json
from typing import Dict, Any
from google import genai
from google.genai import types

from .base import AgentBase

class MultiReportGeneratorAgent(AgentBase):
    def __init__(self):
        super().__init__("multi_report")

    async def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes the Multi-Report Generator Agent workflow.
        Inputs include the original user inputs + the output from Multi-Thinking Agent.
        """
        user_inputs = inputs.get("user_inputs", {})
        thinking_output = inputs.get("thinking_output", {})

        fiscal_year = user_inputs.get("fiscal_year", 2025)

        prompt = f"""
        You are the Multi-Report Generator Agent for a Multi-Agent Infrastructure Reporting Workflow.
        Your goal is to synthesize the Multi-Thinking Agent's output into a final structured report covering multiple incidents in the same area.
        
        User Inputs:
        - Fiscal Year: {fiscal_year}

        Thinking Agent Output (covering multiple incidents):
        {json.dumps(thinking_output, indent=2)}

        You must format the output matching the Report Generator Agent JSON schema exactly.
        Generate descriptive, professional text for the narrative sections (cost_analysis, repair_plan, contractors, budget, grants, 311_complaint_history) summarizing the combined data for all incidents.
        
        Output MUST be a valid JSON object matching the following schema:
        {{
            "report_metadata": {{"generated_at": "...", "fiscal_year": ..., "location": "...", "issue_type": "...", "report_id": "...", "report_url": "..."}},
            "executive_summary": {{"estimated_cost_range": "...", "recommended_timeline": "...", "budget_feasible": true/false, "contractors_found": ..., "grant_opportunities_available": ..., "low_confidence_disclaimer": false}},
            "sections": {{
                "cost_analysis": {{"narrative": "...", "details": [...]}},
                "repair_plan": {{"narrative": "...", "phases": [...]}},
                "contractors": {{"narrative": "...", "list": [...]}},
                "budget": {{"narrative": "...", "details": {{...}}}},
                "grants": {{"narrative": "...", "opportunities": [...]}},
                "311_complaint_history": {{"narrative": "..."}},
                "sources": [...]
            }},
            "source_reliability": [{{"source": "...", "type": "...", "reliability": "..."}}],
            "export_formats": ["markdown", "pdf", "html"]
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
            raise Exception(f"Failed to generate Multi-Report Agent output: {str(e)}")

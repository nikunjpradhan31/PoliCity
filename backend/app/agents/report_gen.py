import json
import os
import io
import sys
import matplotlib.pyplot as plt
import numpy as np
from pydantic import BaseModel
from dotenv import load_dotenv
from typing import Dict, Any
from google import genai
from google.genai import types

from .base import AgentBase

class ReportGeneratorAgent(AgentBase):
    def __init__(self):
        super().__init__("report")

    async def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes the Report Generator Agent workflow.
        Inputs include the original user inputs + the output from Thinking Agent.
        """
        user_inputs = inputs.get("user_inputs", {})
        thinking_output = inputs.get("thinking_output", {})

        issue_type = user_inputs.get("issue_type", "Unknown issue")
        location = user_inputs.get("location", "Unknown location")
        fiscal_year = user_inputs.get("fiscal_year", 2025)

        prompt = f"""
        You are the Report Generator Agent for a Multi-Agent Infrastructure Reporting Workflow.
        Your goal is to synthesize the Thinking Agent's output into a final structured report.
        
        User Inputs:
        - Issue Type: {issue_type}
        - Location: {location}
        - Fiscal Year: {fiscal_year}

        Thinking Agent Output:
        {json.dumps(thinking_output, indent=2)}

        You must format the output matching the Report Generator Agent JSON schema exactly.
        Generate descriptive, professional text for the narrative sections (cost_analysis, repair_plan, contractors, budget, grants, 311_complaint_history) summarizing the data.
        
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
            raise Exception(f"Failed to generate Report Agent output: {str(e)}")

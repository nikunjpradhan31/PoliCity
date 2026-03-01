import json
import os
import io
import sys
import matplotlib
import textwrap
import base64
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from pydantic import BaseModel
from dotenv import load_dotenv
from typing import Dict, Any
from google import genai
from google.genai import types

from .base import AgentBase

# Library for PDF Generation
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.platypus import ListFlowable, ListItem
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import PageBreak

# Generate the graph for the report
class GraphData(BaseModel):
    label: str
    value: float

class Graph(BaseModel):
    type: str
    title: str
    x_axis: str
    y_axis: str
    data: list[GraphData] 

class GraphGeneratorAgent(AgentBase):
    def __init__(self):
        super().__init__("graph")
    
    def renderGraph(self, graph: Graph):
    
        labels = [item.label for item in graph.data]
        values = [item.value for item in graph.data]

        # Wrap labels
        wrapped_labels = [
            "\n".join(textwrap.wrap(label, 10))
            for label in labels
        ]

        colors = plt.cm.tab10(np.linspace(0, 1, len(values)))

        fig_width = max(10, len(values) * 2.2)
        fig, ax = plt.subplots(figsize=(fig_width, 8))

        ax.bar(range(len(values)), values, color=colors)

        ax.set_xticks(range(len(wrapped_labels)))
        ax.set_xticklabels(
            wrapped_labels,
            rotation=15,          
            ha="right",           
            fontsize=9
        )

        ax.set_title(graph.title)
        ax.set_xlabel(graph.x_axis)
        ax.set_ylabel(graph.y_axis)

        fig.tight_layout()

        buffer = io.BytesIO()
        fig.savefig(buffer, format="png", dpi=300)
        plt.close(fig)

        buffer.seek(0)
        return base64.b64encode(buffer.getvalue()).decode("utf-8")

    async def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        
        thinking_output = inputs.get("thinking_output", {})
        thinking_output_str = json.dumps(thinking_output, indent=2)

        response = self.client.models.generate_content(
            contents=f"""
            You are a municipal instrastructure and issues financial analyst.

            TASK:
            Generate bar graph data that is strictly based on the requirements and report provided to you below.

            REQUIREMENTS:
            - All numeric data must be numbers.
            - Do not invent any data that is not supported or contained within the report.
            - Ensure all graph values are realistic and proportional.
            - Use consistent Imperial units.
            - Output must strictly follow the provided JSON schema.

            REPORT:
            {thinking_output_str}
            """,
            model = "gemini-2.5-flash-lite",
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=Graph,
                temperature=0.1
            )
        )

        image_base64 = self.renderGraph(response.parsed)
        return {"image_bytes": image_base64}
    
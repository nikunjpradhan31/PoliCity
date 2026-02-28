import os
import sys
import matplotlib.pyplot as plt
import numpy as np
from pydantic import BaseModel
from dotenv import load_dotenv
from google import genai

load_dotenv()

api_key = os.getenv("GEMINI_KEY")

client = genai.Client(api_key=api_key)

class Contractors(BaseModel):
    name: str
    phone: str
    address: str

class GraphData(BaseModel):
    label: str
    value: float

class Graph(BaseModel):
    type: str
    title: str
    x_axis: str
    y_axis: str
    data: list[GraphData]

class Graphs(BaseModel): #TO-DO Multiple Graphs Loop
    graphs: list[Graph]

class Report(BaseModel):
    summary: str
    cuts: str
    priorities: str
    graphs: list[Graph]
    locations: str
    contractors: list[Contractors]

if len(sys.argv) < 2:
    print("Usage: python script.py <inputfile>")
    sys.exit(1)

inputfilename = sys.argv[1]

with open(inputfilename, "r", encoding="utf-8") as f:
    report_content = f.read()

def generateGraphData(report_content, Graph):
    response = client.models.generate_content(
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
        {report_content}
        """,
        model = "gemini-2.5-flash",
        config={
            "response_mime_type": "application/json",
            "response_schema": Graph,
            "temperature": 0.1
        }
    )

    return response.parsed

def renderGraph(graph: Graph, output_path="graph.png"):
    labels = [item.label for item in graph.data]
    values = [item.value for item in graph.data]

    colors = plt.cm.tab10(np.linspace(0, 1, len(values)))

    plt.figure()
    plt.bar(labels, values, color=colors)
    plt.title(graph.title)
    plt.xlabel(graph.x_axis)
    plt.ylabel(graph.y_axis)

    plt.savefig(output_path)
    plt.close()

    return output_path

def generateReport(report_content, graphs, Report):
    response = client.models.generate_content(
        contents=f"""
        You are a municipal instrastructure and issues financial analyst.

        TASK:
        Generate a summary analysis strictly based on the requirements and report provided to you below.
        
        REQUIREMENTS:
        - All numeric data must be numbers. (No currency symbols or commas).
        - Do not invent any data that is not supported or contained within the report.
        - If the exact numbers are missing, use conservative, clearly reasoned estimates supported by the data provided in the report.
        - Use consistent Imperial units.
        - Output must strictly follow the provided JSON schema.

        REPORT:
        {report_content}
        """,
        model = "gemini-2.5-flash",
        config={
            "response_mime_type": "application/json",
            "response_schema": Report,
            "temperature": 0.1
        }
    )

    return response.parsed

graphs = generateGraphData(report_content, Graph)
graphImagePath = renderGraph(graphs)
promptResponse = generateReport(report_content, graphs, Report)

print(promptResponse)
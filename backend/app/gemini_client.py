import os
import sys
import matplotlib.pyplot as plt
import numpy as np
from pydantic import BaseModel
from dotenv import load_dotenv
from google import genai

# Library for PDF Generation
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.platypus import ListFlowable, ListItem
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import PageBreak

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

def generateReport(report_content, Report):
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

def generatepdf(report, graphs, output_filename="PoliCity_Report.pdf"):
    doc = SimpleDocTemplate(output_filename)
    elements = []

    styles = getSampleStyleSheet()
    normal = styles["Normal"]
    heading = styles["Heading1"]

    # Title
    elements.append(Paragraph("Municipal Infrastructure Financial Report", heading))
    elements.append(Spacer(1, 0.3 * inch))

    # Location
    elements.append(Paragraph(f"<b>Location:</b> {report['locations']}", normal))
    elements.append(Spacer(1, 0.2 * inch))

    # Summary
    elements.append(Paragraph("<b>Summary</b>", styles["Heading2"]))
    elements.append(Spacer(1, 0.1 * inch))
    elements.append(Paragraph(report["summary"], normal))
    elements.append(Spacer(1, 0.3 * inch))

    # Cuts
    elements.append(Paragraph("<b>Budget Cuts</b>", styles["Heading2"]))
    elements.append(Spacer(1, 0.1 * inch))
    elements.append(Paragraph(report["cuts"], normal))
    elements.append(Spacer(1, 0.3 * inch))

    # Priorities
    elements.append(Paragraph("<b>Priorities</b>", styles["Heading2"]))
    elements.append(Spacer(1, 0.1 * inch))
    elements.append(Paragraph(report["priorities"], normal))
    elements.append(PageBreak())

    # Contractors
    elements.append(Paragraph("<b>Contractors</b>", styles["Heading2"]))
    elements.append(Spacer(1, 0.1 * inch))
    if report["contractors"]:
        for contractor in report["contractors"]:
            contractor_text = (
                f"<b>{contractor['name']}</b><br/>"
                f"Phone: {contractor['phone']}<br/>"
                f"Address: {contractor['address']}<br/><br/>"
            )
            elements.append(Paragraph(contractor_text, normal))
            elements.append(PageBreak())
    else:
        elements.append(Paragraph("No contractors were identified for this project.", normal))

    # Graphs
    elements.append(Paragraph("<b>Cost Breakdown Graphs</b>", styles["Heading1"]))
    elements.append(Spacer(1, 0.3 * inch))

    for i, graph in enumerate(report["graphs"]):
        image_filename = f"graph_{i}.png"
        renderGraph(graphs, image_filename)

        elements.append(Paragraph(graph["title"], styles["Heading2"]))
        elements.append(Spacer(1, 0.2 * inch))
        elements.append(Image(image_filename, width=6*inch, height=4*inch))
        elements.append(Spacer(1, 0.5 * inch))

    doc.build(elements)

graphs = generateGraphData(report_content, Graph)
promptResponse = generateReport(report_content, Report)
generatepdf(promptResponse.model_dump(), graphs)

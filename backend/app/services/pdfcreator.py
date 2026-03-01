import io
import base64
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak
)
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT


def generatepdf(report: dict, image_bytes: bytes) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer)
    elements = []

    styles = getSampleStyleSheet()

    # Custom style to prevent overflow issues
    body_style = ParagraphStyle(
        "BodyStyle",
        parent=styles["Normal"],
        fontSize=11,
        leading=14,
        alignment=TA_LEFT
    )

    heading = styles["Heading1"]
    subheading = styles["Heading2"]

    # ---- Safe getters ----
    location = report.get("locations", "N/A")
    summary = report.get("summary", "No summary available.")
    cuts = report.get("cuts", "No budget cuts identified.")
    priorities = report.get("priorities", "No priorities listed.")
    contractors = report.get("contractors") or []
    graph_title = report.get("graph", {}).get("title", "Cost Breakdown")

    # ---- Title ----
    elements.append(Paragraph("Municipal Infrastructure Financial Report", heading))
    elements.append(Spacer(1, 0.3 * inch))

    # ---- Location ----
    elements.append(Paragraph(f"<b>Location:</b> {location}", body_style))
    elements.append(Spacer(1, 0.3 * inch))

    # ---- Summary ----
    elements.append(Paragraph("Summary", subheading))
    elements.append(Spacer(1, 0.1 * inch))
    elements.append(Paragraph(summary, body_style))
    elements.append(Spacer(1, 0.3 * inch))

    # ---- Cuts ----
    elements.append(Paragraph("Budget Cuts", subheading))
    elements.append(Spacer(1, 0.1 * inch))
    elements.append(Paragraph(cuts, body_style))
    elements.append(Spacer(1, 0.3 * inch))

    # ---- Priorities ----
    elements.append(Paragraph("Priorities", subheading))
    elements.append(Spacer(1, 0.1 * inch))
    elements.append(Paragraph(priorities, body_style))
    elements.append(PageBreak())

    # ---- Contractors ----
    elements.append(Paragraph("Contractors", subheading))
    elements.append(Spacer(1, 0.2 * inch))

    if contractors:
        for contractor in contractors:
            name = contractor.get("name", "Unknown")
            phone = contractor.get("phone", "N/A")
            address = contractor.get("address", "N/A")

            contractor_text = (
                f"<b>{name}</b><br/>"
                f"Phone: {phone}<br/>"
                f"Address: {address}<br/><br/>"
            )

            elements.append(Paragraph(contractor_text, body_style))
            elements.append(Spacer(1, 0.2 * inch))
    else:
        elements.append(
            Paragraph("No contractors were identified for this project.", body_style)
        )

    elements.append(PageBreak())

    # ---- Graph Section ----
    elements.append(Paragraph("Cost Breakdown Graph", heading))
    elements.append(Spacer(1, 0.3 * inch))

    elements.append(Paragraph(graph_title, subheading))
    elements.append(Spacer(1, 0.2 * inch))

    # Handle base64 image if needed
    if isinstance(image_bytes, str):
        image_bytes = base64.b64decode(image_bytes)

    image_buffer = io.BytesIO(image_bytes)
    image_buffer.seek(0)

    elements.append(Image(image_buffer, width=6 * inch, height=4 * inch))

    # ---- Build ----
    doc.build(elements)
    buffer.seek(0)

    return buffer.getvalue()
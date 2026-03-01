import io
import base64
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_LEFT, TA_CENTER


def generatepdf(report: dict, image_bytes: bytes) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer)
    elements = []

    styles = getSampleStyleSheet()

    # ---- Custom Styles ----
    body_style = ParagraphStyle(
        "BodyStyle",
        parent=styles["Normal"],
        fontName="Times-Roman",
        fontSize=11,
        leading=14,
        alignment=TA_LEFT
    )

    heading = styles["Heading1"]
    heading.fontName = "Times-Roman"

    subheading = styles["Heading2"]
    subheading.fontName = "Times-Roman"

    centered_heading = ParagraphStyle(
        name="CenteredHeading",
        parent=heading,
        alignment=TA_CENTER
    )

    # ---- Extract Data Safely ----
    data = report.get("data", {})
    metadata = data.get("report_metadata", {})
    summary = data.get("executive_summary", {})
    sections = data.get("sections", {})

    contractors_section = sections.get("contractors", {})
    contractors_list = contractors_section.get("list", [])

    cost_analysis = sections.get("cost_analysis", {})
    repair_plan = sections.get("repair_plan", {})
    budget = sections.get("budget", {})
    grants = sections.get("grants", {})
    complaint_history = sections.get("311_complaint_history", {})

    # ---- Title ----
    elements.append(Paragraph("<u>Municipal Infrastructure Financial Report</u>", centered_heading))
    elements.append(Spacer(1, 0.3 * inch))

    # ---- Metadata ----
    location = metadata.get("location", "N/A")
    issue_type = metadata.get("issue_type", "N/A")
    fiscal_year = metadata.get("fiscal_year", "N/A")

    elements.append(Paragraph(f"<b>Location:</b> {location}", body_style))
    elements.append(Paragraph(f"<b>Issue Type:</b> {issue_type}", body_style))
    elements.append(Paragraph(f"<b>Fiscal Year:</b> {fiscal_year}", body_style))
    elements.append(Spacer(1, 0.3 * inch))

    # ---- Executive Summary ----
    elements.append(Paragraph("<u>Executive Summary</u>", subheading))
    elements.append(Spacer(1, 0.1 * inch))

    elements.append(Paragraph(
        f"<b>Estimated Cost Range:</b> {summary.get('estimated_cost_range', 'N/A')}",
        body_style
    ))
    elements.append(Paragraph(
        f"<b>Recommended Timeline:</b> {summary.get('recommended_timeline', 'N/A')}",
        body_style
    ))
    elements.append(Spacer(1, 0.3 * inch))

    # ---- Cost Analysis ----
    elements.append(Paragraph("<u>Cost Analysis</u>", subheading))
    elements.append(Spacer(1, 0.1 * inch))
    elements.append(Paragraph(cost_analysis.get("narrative", "No data available."), body_style))
    elements.append(PageBreak())

    # ---- Repair Plan ----
    elements.append(Paragraph("<u>Repair Plan</u>", subheading))
    elements.append(Spacer(1, 0.1 * inch))
    elements.append(Paragraph(repair_plan.get("narrative", "No data available."), body_style))
    elements.append(PageBreak())

    # ---- Contractors ----
    elements.append(Paragraph("<u>Contractors</u>", subheading))
    elements.append(Spacer(1, 0.2 * inch))

    if contractors_list:
        for contractor in contractors_list:
            name = contractor.get("name", "Unknown")
            phone = contractor.get("phone", "N/A")
            address = contractor.get("address", "N/A")
            rating = contractor.get("rating", "N/A")

            contractor_text = (
                f"<b>{name}</b><br/>"
                f"Phone: {phone}<br/>"
                f"Address: {address}<br/>"
                f"Rating: {rating}<br/><br/>"
            )

            elements.append(Paragraph(contractor_text, body_style))
            elements.append(Spacer(1, 0.2 * inch))
    else:
        elements.append(
            Paragraph("No contractors identified.", body_style)
        )

    elements.append(PageBreak())

    # ---- Budget ----
    elements.append(Paragraph("<u>Budget Overview</u>", subheading))
    elements.append(Spacer(1, 0.1 * inch))
    elements.append(Paragraph(budget.get("narrative", "No budget data available."), body_style))
    elements.append(PageBreak())

    # ---- Grants ----
    elements.append(Paragraph("<u>Grant Opportunities</u>", subheading))
    elements.append(Spacer(1, 0.1 * inch))
    elements.append(Paragraph(grants.get("narrative", "No grant data available."), body_style))
    elements.append(PageBreak())

    # ---- 311 Complaint History ----
    elements.append(Paragraph("<u>311 Complaint History</u>", subheading))
    elements.append(Spacer(1, 0.1 * inch))
    elements.append(Paragraph(complaint_history.get("narrative", "No complaint history available."), body_style))
    elements.append(PageBreak())

    # ---- Graph Section ----
    elements.append(Paragraph("<u>Cost Breakdown Graph</u>", centered_heading))
    elements.append(Spacer(1, 0.3 * inch))

    if isinstance(image_bytes, str):
        image_bytes = base64.b64decode(image_bytes)

    image_buffer = io.BytesIO(image_bytes)
    image_buffer.seek(0)

    elements.append(Image(image_buffer, width=6 * inch, height=4 * inch))

    # ---- Build ----
    doc.build(elements)
    buffer.seek(0)

    return buffer.getvalue()
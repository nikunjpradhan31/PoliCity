import io
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak
)
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch

def generatepdf(report, image_bytes):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer)
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
        elements.append(PageBreak())

    # Graph
    elements.append(Paragraph("Cost Breakdown Graph", heading))
    elements.append(Spacer(1, 0.3 * inch))

    image_buffer = io.BytesIO(image_bytes)
    image_buffer.seek(0)

    elements.append(Paragraph(report["graph"]["title"], styles["Heading2"]))
    elements.append(Spacer(1, 0.2 * inch))
    elements.append(Image(image_buffer, width=6 * inch, height=4 * inch))

    doc.build(elements)

    buffer.seek(0)
    return buffer.getvalue()
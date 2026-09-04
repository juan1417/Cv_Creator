from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm, mm
from reportlab.lib.colors import HexColor
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)

from .cv_models import CvData

COLOR_DARK = HexColor("#1a1a2e")
COLOR_LIGHT = HexColor("#f0f0f5")
COLOR_LINE = HexColor("#cccccc")


def _get_styles():
    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(
        name="CvTitle",
        parent=styles["Title"],
        fontName="Helvetica-Bold",
        fontSize=22,
        textColor=COLOR_DARK,
        alignment=TA_CENTER,
        spaceAfter=4 * mm,
    ))

    styles.add(ParagraphStyle(
        name="CvContact",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10,
        textColor=HexColor("#444444"),
        alignment=TA_CENTER,
        spaceAfter=6 * mm,
    ))

    styles.add(ParagraphStyle(
        name="CvSectionHeader",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=13,
        textColor=COLOR_DARK,
        spaceBefore=8 * mm,
        spaceAfter=3 * mm,
        borderWidth=0,
        borderPadding=0,
    ))

    styles.add(ParagraphStyle(
        name="CvNormal",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10,
        textColor=HexColor("#333333"),
        leading=14,
        spaceAfter=2 * mm,
    ))

    styles.add(ParagraphStyle(
        name="CvSmall",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        textColor=HexColor("#555555"),
        leading=12,
        spaceAfter=1 * mm,
    ))

    styles.add(ParagraphStyle(
        name="CvJobTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=11,
        textColor=COLOR_DARK,
        spaceAfter=1 * mm,
    ))

    styles.add(ParagraphStyle(
        name="CvCompany",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=10,
        textColor=HexColor("#333333"),
        spaceAfter=1 * mm,
    ))

    styles.add(ParagraphStyle(
        name="CvDates",
        parent=styles["Normal"],
        fontName="Helvetica-Oblique",
        fontSize=9,
        textColor=HexColor("#666666"),
        spaceAfter=2 * mm,
    ))

    styles.add(ParagraphStyle(
        name="CvBullet",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10,
        textColor=HexColor("#333333"),
        leading=13,
        leftIndent=10,
        spaceAfter=1 * mm,
        bulletIndent=0,
    ))

    return styles


def _section_line():
    return HRFlowable(
        width="100%", thickness=0.5, color=COLOR_LINE,
        spaceBefore=0, spaceAfter=4 * mm
    )


def create_pdf(cv_data: CvData, output_dir: str = "output") -> Path:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    styles = _get_styles()
    elements = []

    elements.append(Paragraph(cv_data.name, styles["CvTitle"]))

    contact_parts = [cv_data.address]
    if cv_data.linkedin:
        contact_parts.append(cv_data.linkedin)
    phone = f"+{cv_data.phone}" if not cv_data.phone.startswith("+") else cv_data.phone
    contact_parts.append(phone)
    contact_parts.append(cv_data.email)
    contact_str = "  |  ".join(contact_parts)
    elements.append(Paragraph(contact_str, styles["CvContact"]))

    elements.append(_section_line())

    if cv_data.about:
        elements.append(Paragraph("SOBRE MÍ", styles["CvSectionHeader"]))
        elements.append(Paragraph(cv_data.about, styles["CvNormal"]))

    if cv_data.experience:
        elements.append(Paragraph("EXPERIENCIA PROFESIONAL", styles["CvSectionHeader"]))
        elements.append(_section_line())
        for exp in cv_data.experience:
            job_data = [[
                Paragraph(f"<b>{exp.title}</b>", styles["CvJobTitle"]),
                Paragraph(exp.duration, styles["CvDates"]),
            ]]
            job_table = Table(job_data, colWidths=[12 * cm, 5 * cm])
            job_table.setStyle(TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ]))
            elements.append(job_table)
            elements.append(Paragraph(exp.company, styles["CvCompany"]))
            if exp.description:
                elements.append(Paragraph(exp.description, styles["CvNormal"]))
            elements.append(Spacer(1, 3 * mm))

    if cv_data.education:
        elements.append(Paragraph("EDUCACIÓN", styles["CvSectionHeader"]))
        elements.append(_section_line())
        for edu in cv_data.education:
            edu_data = [[
                Paragraph(f"<b>{edu.degree}</b>", styles["CvJobTitle"]),
                Paragraph(edu.year, styles["CvDates"]),
            ]]
            edu_table = Table(edu_data, colWidths=[12 * cm, 5 * cm])
            edu_table.setStyle(TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ]))
            elements.append(edu_table)
            elements.append(Paragraph(edu.school, styles["CvCompany"]))
            if edu.location:
                elements.append(Paragraph(edu.location, styles["CvDates"]))
            elements.append(Spacer(1, 3 * mm))

    if cv_data.skills:
        elements.append(Paragraph("SKILLS ADICIONALES", styles["CvSectionHeader"]))
        elements.append(_section_line())
        for skill in cv_data.skills:
            elements.append(Paragraph(f"\u2022  {skill}", styles["CvBullet"]))

        elements.append(Paragraph("TECNOLOGÍAS", styles["CvSectionHeader"]))
        elements.append(_section_line())
        tech_str = ", ".join(cv_data.skills)
        elements.append(Paragraph(tech_str, styles["CvNormal"]))

    safe_name = cv_data.name.replace(" ", "_").replace("/", "_")
    file_path = output_path / f"{safe_name}_cv.pdf"

    doc = SimpleDocTemplate(
        str(file_path),
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )
    doc.build(elements)
    return file_path

"""Creates PDF files matching the paragraph-based plantilla.docx template.

Uses ReportLab to generate A4 PDFs with the same section order and styling
as the DOCX template: Arial, #404040 color, ● contact separator, pipe-separated skills.
"""
from pathlib import Path
from datetime import datetime

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm, cm
from reportlab.lib.colors import HexColor
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, HRFlowable
)

from .cv_models import CvData

COLOR_TEXT = HexColor("#404040")
COLOR_LIGHT = HexColor("#666666")
FONT = "Helvetica"
FONT_BOLD = "Helvetica-Bold"
FONT_ITALIC = "Helvetica-Oblique"


def _get_styles():
    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(
        name="CvName",
        fontName=FONT_BOLD,
        fontSize=16,
        textColor=COLOR_TEXT,
        spaceAfter=2 * mm,
    ))

    styles.add(ParagraphStyle(
        name="CvContact",
        fontName=FONT,
        fontSize=11,
        textColor=COLOR_TEXT,
        spaceAfter=6 * mm,
    ))

    styles.add(ParagraphStyle(
        name="CvSection",
        fontName=FONT_BOLD,
        fontSize=12,
        textColor=COLOR_TEXT,
        spaceBefore=6 * mm,
        spaceAfter=2 * mm,
    ))

    styles.add(ParagraphStyle(
        name="CvBody",
        fontName=FONT,
        fontSize=10,
        textColor=COLOR_TEXT,
        leading=14,
        spaceAfter=2 * mm,
    ))

    styles.add(ParagraphStyle(
        name="CvSmall",
        fontName=FONT,
        fontSize=11,
        textColor=COLOR_TEXT,
        leading=14,
        spaceAfter=1 * mm,
    ))

    styles.add(ParagraphStyle(
        name="CvExpHeader",
        fontName=FONT,
        fontSize=10,
        textColor=COLOR_TEXT,
        spaceAfter=1 * mm,
    ))

    styles.add(ParagraphStyle(
        name="CvInstitution",
        fontName=FONT_ITALIC,
        fontSize=11,
        textColor=COLOR_TEXT,
        spaceAfter=3 * mm,
    ))

    styles.add(ParagraphStyle(
        name="CvBullet",
        fontName=FONT,
        fontSize=10,
        textColor=COLOR_TEXT,
        leading=13,
        leftIndent=10,
        bulletIndent=0,
        spaceAfter=1 * mm,
    ))

    styles.add(ParagraphStyle(
        name="CvSkills",
        fontName=FONT,
        fontSize=10,
        textColor=COLOR_TEXT,
        leading=14,
        spaceAfter=2 * mm,
    ))

    return styles


def _format_date(start: str, end: str | None) -> str:
    """Format date range like 'Mar 2023 - Presente'."""
    if not start:
        return ""
    try:
        s = datetime.strptime(start, "%Y-%m-%d")
        start_str = s.strftime("%b %Y")
    except (ValueError, TypeError):
        start_str = start
    if not end:
        return f"{start_str} - Presente"
    try:
        e = datetime.strptime(end, "%Y-%m-%d")
        end_str = e.strftime("%b %Y")
    except (ValueError, TypeError):
        end_str = end
    return f"{start_str} - {end_str}"


def create_pdf(cv_data: CvData, output_dir: str = "output") -> Path:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    styles = _get_styles()
    elements = []

    # --- Name ---
    elements.append(Paragraph(cv_data.name.upper(), styles["CvName"]))

    # --- Contact ---
    parts = []
    if cv_data.address:
        parts.append(cv_data.address)
    if cv_data.email:
        parts.append(cv_data.email)
    phone = f"+{cv_data.phone}" if cv_data.phone and not cv_data.phone.startswith("+") else cv_data.phone
    if phone:
        parts.append(phone)
    if cv_data.linkedin:
        parts.append(cv_data.linkedin)
    if cv_data.portfolio:
        parts.append(cv_data.portfolio)
    elements.append(Paragraph(" ● ".join(parts), styles["CvContact"]))

    # --- PERFIL PROFESIONAL ---
    if cv_data.about:
        elements.append(Paragraph("PERFIL PROFESIONAL", styles["CvSection"]))
        elements.append(Paragraph(cv_data.about, styles["CvBody"]))

    # --- EDUCACIÓN ---
    if cv_data.education:
        elements.append(Paragraph("EDUCACIÓN", styles["CvSection"]))
        for edu in cv_data.education:
            date_str = _format_date(edu.start_date, edu.end_date)
            exp_line = f"<b>{edu.degree}</b>\t{date_str}"
            elements.append(Paragraph(exp_line, styles["CvExpHeader"]))
            elements.append(Paragraph(f"<i>{edu.institution}</i>", styles["CvInstitution"]))
            if edu.description:
                elements.append(Paragraph(edu.description, styles["CvBody"]))

    # --- EXPERIENCIA PROFESIONAL ---
    if cv_data.experience:
        elements.append(Paragraph("EXPERIENCIA PROFESIONAL", styles["CvSection"]))
        for exp in cv_data.experience:
            date_str = _format_date(exp.start_date, exp.end_date)
            header = f"<b>{exp.company}</b>\t{date_str}"
            elements.append(Paragraph(header, styles["CvExpHeader"]))
            if exp.title:
                elements.append(Paragraph(exp.title, styles["CvBody"]))
            if exp.description:
                elements.append(Paragraph(exp.description, styles["CvBody"]))
            elements.append(Spacer(1, 2 * mm))

    # --- HABILIDADES ---
    if cv_data.skills:
        elements.append(Paragraph("HABILIDADES", styles["CvSection"]))
        elements.append(Paragraph(" | ".join(cv_data.skills), styles["CvSkills"]))

    # --- LOGROS DESTACADOS ---
    if cv_data.achievements:
        elements.append(Paragraph("LOGROS DESTACADOS", styles["CvSection"]))
        for ach in cv_data.achievements:
            text = ach.title
            if ach.description:
                text += f" — {ach.description}"
            elements.append(Paragraph(text, styles["CvBody"]))

    # --- PROGRAMAS ---
    if cv_data.programs:
        elements.append(Paragraph("PROGRAMAS", styles["CvSection"]))
        elements.append(Paragraph(" | ".join(cv_data.programs), styles["CvSkills"]))

    # --- IDIOMAS ---
    if cv_data.languages:
        elements.append(Paragraph("IDIOMAS", styles["CvSection"]))
        lang_parts = [f"{lang.name} ({lang.level})" if lang.level else lang.name for lang in cv_data.languages]
        elements.append(Paragraph(" | ".join(lang_parts), styles["CvSkills"]))

    # --- Save ---
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

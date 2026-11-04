"""Renderizadores Harvard del CV en DOCX y PDF.

Un único `build_layout()` define el orden, los textos y la jerarquía visual. Los
dos renderers consumen ese layout, así que el DOCX y el PDF no pueden divergir.

Formato Harvard (resume de una página, A4):

- Nombre en mayúsculas, negrita, centrado.
- Línea de contacto centrada, separada por ``•``.
- Encabezados de sección en mayúsculas con línea inferior.
- Entradas: organización en negrita a la izquierda, fecha alineada a la derecha,
  cargo/institución en itálica debajo, viñetas con ``•``.
- Sin tablas, imágenes, cuadros de texto, encabezados ni pies: el documento es
  texto plano de una sola columna, legible por un parser ATS.

Los renderers devuelven ``bytes`` y nunca escriben en disco.
"""

import re
from dataclasses import dataclass, field
from io import BytesIO
from typing import Literal

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_TAB_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    KeepTogether,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from .cv_models import CvData

FONT_NAME = "Arial"
TEXT_COLOR = RGBColor(0x40, 0x40, 0x40)
TEXT_COLOR_HEX = "#404040"

PAGE_WIDTH_CM = 21.0
PAGE_HEIGHT_CM = 29.7
MARGIN_CM = 1.27
CONTENT_WIDTH_CM = PAGE_WIDTH_CM - 2 * MARGIN_CM

BODY_SIZE_PT = 10.5
NAME_SIZE_PT = 16.0
SECTION_SIZE_PT = 11.0
CONTACT_SIZE_PT = 10.0

SECTION_SUMMARY = "PERFIL PROFESIONAL"
SECTION_EDUCATION = "EDUCACIÓN"
SECTION_EXPERIENCE = "EXPERIENCIA PROFESIONAL"
SECTION_SKILLS = "HABILIDADES"
SECTION_ACHIEVEMENTS = "LOGROS DESTACADOS"
SECTION_PROGRAMS = "TECNOLOGÍAS"
SECTION_LANGUAGES = "IDIOMAS"

_MONTHS_ES = (
    "ene", "feb", "mar", "abr", "may", "jun",
    "jul", "ago", "sep", "oct", "nov", "dic",
)

Segment = tuple[str, bool, bool]  # (texto, negrita, itálica)


# ---------------------------------------------------------------------------
# Formato de fechas
# ---------------------------------------------------------------------------

def _parse_iso(value: str | None):
    """Devuelve (año, mes) desde ``YYYY-MM-DD`` o desde ``YYYY-MM``/``YYYY``."""
    if not value:
        return None
    match = re.match(r"^(\d{4})(?:-(\d{2}))?", value.strip())
    if not match:
        return None
    year = int(match.group(1))
    month = int(match.group(2)) if match.group(2) else None
    if month is not None and not 1 <= month <= 12:
        month = None
    return year, month


def format_date(start: str | None, end: str | None) -> str:
    """Formatea un rango como ``mar 2023 - Presente``."""
    start_parsed = _parse_iso(start)
    end_parsed = _parse_iso(end)

    if start_parsed is None and end_parsed is None:
        return ""

    def render(parsed) -> str:
        year, month = parsed
        if month is None:
            return str(year)
        return f"{_MONTHS_ES[month - 1]} {year}"

    if start_parsed is None:
        return render(end_parsed)
    if end_parsed is None:
        return f"{render(start_parsed)} - Presente"
    return f"{render(start_parsed)} - {render(end_parsed)}"


# ---------------------------------------------------------------------------
# Layout compartido
# ---------------------------------------------------------------------------

LayoutKind = Literal["name", "contact", "heading", "text", "entry", "bullet", "spacer"]


@dataclass
class LayoutItem:
    kind: LayoutKind
    text: str = ""
    segments: list[Segment] = field(default_factory=list)
    left: str = ""
    right: str = ""

    def plain_text(self) -> str:
        if self.segments:
            return "".join(seg[0] for seg in self.segments)
        if self.kind == "entry":
            return f"{self.left} {self.right}".strip()
        return self.text


def _split_lines(description: str) -> list[str]:
    """Divide una descripción en líneas y limpia viñetas/guiones iniciales."""
    if not description or not description.strip():
        return []
    lines: list[str] = []
    for raw in description.splitlines():
        cleaned = raw.strip()
        if not cleaned:
            continue
        cleaned = re.sub(r"^[•\-\u2013\u2014\*]\s*", "", cleaned)
        lines.append(cleaned)
    return lines


def _contact_line(cv: CvData) -> str:
    parts = [cv.address, cv.email, cv.phone, cv.linkedin, cv.portfolio]
    return " • ".join(part.strip() for part in parts if part and part.strip())


def _skills_line(cv: CvData) -> str:
    ordered = [s for s in cv.skills if (s.type or "tech") != "soft"]
    ordered += [s for s in cv.skills if (s.type or "tech") == "soft"]
    chunks = [skill.name.strip() for skill in ordered if skill.name.strip()]
    return ", ".join(chunks)


def _languages_line(cv: CvData) -> str:
    chunks = []
    for language in cv.languages:
        name = language.name.strip()
        if not name:
            continue
        level = language.level.strip()
        chunks.append(f"{name} ({level})" if level else name)
    return ", ".join(chunks)


def build_layout(cv: CvData) -> list[LayoutItem]:
    """Construye el layout Harvard completo a partir del CV."""
    items: list[LayoutItem] = []

    items.append(LayoutItem(kind="name", text=(cv.name or "").strip().upper()))

    contact = _contact_line(cv)
    if contact:
        items.append(LayoutItem(kind="contact", text=contact))

    about = (cv.about or "").strip()
    if about:
        items.append(LayoutItem(kind="heading", text=SECTION_SUMMARY))
        for line in _split_lines(about):
            items.append(LayoutItem(kind="text", text=line))

    if cv.education:
        items.append(LayoutItem(kind="heading", text=SECTION_EDUCATION))
        for education in cv.education:
            items.append(LayoutItem(
                kind="entry",
                left=(education.degree or "").strip(),
                right=format_date(education.start_date, education.end_date),
            ))
            institution = (education.institution or "").strip()
            if institution:
                items.append(LayoutItem(
                    kind="bullet", segments=[(institution, False, True)]
                ))
            for line in _split_lines(education.description):
                items.append(LayoutItem(kind="bullet", segments=[(line, False, False)]))

    if cv.experience:
        items.append(LayoutItem(kind="heading", text=SECTION_EXPERIENCE))
        for experience in cv.experience:
            items.append(LayoutItem(
                kind="entry",
                left=(experience.company or "").strip(),
                right=format_date(experience.start_date, experience.end_date),
            ))
            title = (experience.title or "").strip()
            if title:
                items.append(LayoutItem(
                    kind="bullet", segments=[(title, False, True)]
                ))
            for line in _split_lines(experience.description):
                items.append(LayoutItem(kind="bullet", segments=[(line, False, False)]))

    skills = _skills_line(cv)
    if skills:
        items.append(LayoutItem(kind="heading", text=SECTION_SKILLS))
        items.append(LayoutItem(kind="text", text=skills))

    if cv.achievements:
        items.append(LayoutItem(kind="heading", text=SECTION_ACHIEVEMENTS))
        for achievement in cv.achievements:
            segments: list[Segment] = []
            title = (achievement.title or "").strip()
            if title:
                segments.append((title, True, False))
            description = (achievement.description or "").strip()
            if description:
                if segments:
                    segments.append((" — ", False, False))
                segments.append((description, False, False))
            if segments:
                items.append(LayoutItem(kind="bullet", segments=segments))

    if cv.programs:
        items.append(LayoutItem(kind="heading", text=SECTION_PROGRAMS))
        items.append(LayoutItem(
            kind="text",
            text=", ".join(p.strip() for p in cv.programs if p and p.strip()),
        ))

    languages = _languages_line(cv)
    if languages:
        items.append(LayoutItem(kind="heading", text=SECTION_LANGUAGES))
        items.append(LayoutItem(kind="text", text=languages))

    return items


def expected_fragments(cv: CvData) -> list[str]:
    """Fragmentos que un parser ATS debe poder leer del archivo generado."""
    fragments: list[str] = []
    name = (cv.name or "").strip()
    if name:
        fragments.append(name)
    if cv.email and cv.email.strip():
        fragments.append(cv.email.strip())
    for item in build_layout(cv):
        if item.kind == "heading":
            fragments.append(item.text)
    return fragments


# ---------------------------------------------------------------------------
# DOCX
# ---------------------------------------------------------------------------

def _add_bottom_border(paragraph) -> None:
    """Agrega una línea inferior al párrafo respetando el orden de `w:pPr`."""
    p_pr = paragraph._p.get_or_add_pPr()
    border = OxmlElement("w:pBdr")
    bottom = OxmlElement("w:bottom")
    bottom.set(qn("w:val"), "single")
    bottom.set(qn("w:sz"), "6")
    bottom.set(qn("w:space"), "1")
    bottom.set(qn("w:color"), "404040")
    border.append(bottom)
    p_pr.append(border)


def _docx_new_document() -> Document:
    document = Document()

    section = document.sections[0]
    section.page_width = Cm(PAGE_WIDTH_CM)
    section.page_height = Cm(PAGE_HEIGHT_CM)
    section.left_margin = Cm(MARGIN_CM)
    section.right_margin = Cm(MARGIN_CM)
    section.top_margin = Cm(MARGIN_CM)
    section.bottom_margin = Cm(MARGIN_CM)
    section.header_distance = Cm(0.6)
    section.footer_distance = Cm(0.6)

    normal = document.styles["Normal"]
    normal.font.name = FONT_NAME
    normal.font.size = Pt(BODY_SIZE_PT)
    normal.font.color.rgb = TEXT_COLOR
    r_pr = normal.element.get_or_add_rPr()
    r_fonts = r_pr.get_or_add_rFonts()
    r_fonts.set(qn("w:ascii"), FONT_NAME)
    r_fonts.set(qn("w:hAnsi"), FONT_NAME)
    r_fonts.set(qn("w:eastAsia"), FONT_NAME)
    r_fonts.set(qn("w:cs"), FONT_NAME)

    normal.paragraph_format.space_before = Pt(0)
    normal.paragraph_format.space_after = Pt(2)
    normal.paragraph_format.line_spacing = 1.0

    return document


def _docx_text_paragraph(
    document,
    text: str = "",
    *,
    bold: bool = False,
    italic: bool = False,
    size_pt: float | None = None,
    alignment=None,
    space_before: float = 0,
    space_after: float = 2,
):
    paragraph = document.add_paragraph()
    fmt = paragraph.paragraph_format
    fmt.space_before = Pt(space_before)
    fmt.space_after = Pt(space_after)
    fmt.line_spacing = 1.0
    if alignment is not None:
        paragraph.alignment = alignment
    if text:
        run = paragraph.add_run(text)
        run.bold = bold
        run.italic = italic
        if size_pt is not None:
            run.font.size = Pt(size_pt)
    return paragraph


def _docx_heading(document, text: str):
    paragraph = document.add_paragraph()
    paragraph.paragraph_format.keep_with_next = True
    _add_bottom_border(paragraph)
    fmt = paragraph.paragraph_format
    fmt.space_before = Pt(8)
    fmt.space_after = Pt(3)
    fmt.line_spacing = 1.0
    run = paragraph.add_run(text)
    run.bold = True
    run.font.size = Pt(SECTION_SIZE_PT)
    return paragraph


def _docx_entry(document, left: str, right: str):
    paragraph = document.add_paragraph()
    fmt = paragraph.paragraph_format
    fmt.space_before = Pt(5)
    fmt.space_after = Pt(0)
    fmt.line_spacing = 1.0
    fmt.tab_stops.add_tab_stop(Cm(CONTENT_WIDTH_CM), WD_TAB_ALIGNMENT.RIGHT)

    left_run = paragraph.add_run(left)
    left_run.bold = True
    if right:
        paragraph.add_run("\t")
        right_run = paragraph.add_run(right)
        right_run.bold = False
    return paragraph


def _docx_bullet(document, segments: list[Segment]):
    paragraph = document.add_paragraph()
    fmt = paragraph.paragraph_format
    fmt.left_indent = Cm(0.45)
    fmt.first_line_indent = Cm(-0.45)
    fmt.space_before = Pt(0)
    fmt.space_after = Pt(2)
    fmt.line_spacing = 1.0
    paragraph.add_run("•\t")
    for text, bold, italic in segments:
        run = paragraph.add_run(text)
        run.bold = bold
        run.italic = italic
    return paragraph


def render_docx(cv: CvData) -> bytes:
    """Genera el DOCX Harvard y devuelve sus bytes."""
    document = _docx_new_document()

    author = (cv.name or "").strip() or "CvCreator"
    document.core_properties.author = author
    document.core_properties.title = f"CV - {author}"

    for item in build_layout(cv):
        if item.kind == "name":
            _docx_text_paragraph(
                document,
                item.text,
                bold=True,
                size_pt=NAME_SIZE_PT,
                alignment=WD_ALIGN_PARAGRAPH.CENTER,
                space_after=2,
            )
        elif item.kind == "contact":
            _docx_text_paragraph(
                document,
                item.text,
                size_pt=CONTACT_SIZE_PT,
                alignment=WD_ALIGN_PARAGRAPH.CENTER,
                space_after=4,
            )
        elif item.kind == "heading":
            _docx_heading(document, item.text)
        elif item.kind == "text":
            _docx_text_paragraph(document, item.text, space_after=3)
        elif item.kind == "entry":
            _docx_entry(document, item.left, item.right)
        elif item.kind == "bullet":
            _docx_bullet(document, item.segments)
        elif item.kind == "spacer":
            _docx_text_paragraph(document, "", space_after=0)

    buffer = BytesIO()
    document.save(buffer)
    return buffer.getvalue()


# ---------------------------------------------------------------------------
# PDF
# ---------------------------------------------------------------------------

_PDF_FONT_CANDIDATES = (
    (
        "CVSans",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Italic.ttf",
    ),
    (
        "CVSans",
        "/usr/share/fonts/liberation/LiberationSans-Regular.ttf",
        "/usr/share/fonts/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/liberation/LiberationSans-Italic.ttf",
    ),
)

_fonts_registered: dict[str, tuple[str, str, str]] = {}


def _pdf_fonts() -> tuple[str, str, str]:
    """Registra una familia sans (Arial-compatible) con fallback a Helvetica."""
    if "family" in _fonts_registered:
        return _fonts_registered["family"]

    import os

    for name, regular, bold, italic in _PDF_FONT_CANDIDATES:
        if all(os.path.exists(path) for path in (regular, bold, italic)):
            try:
                pdfmetrics.registerFont(TTFont(name, regular))
                pdfmetrics.registerFont(TTFont(f"{name}-Bold", bold))
                pdfmetrics.registerFont(TTFont(f"{name}-Italic", italic))
                pdfmetrics.registerFontFamily(
                    name,
                    normal=name,
                    bold=f"{name}-Bold",
                    italic=f"{name}-Italic",
                    boldItalic=f"{name}-Bold",
                )
                family = (name, f"{name}-Bold", f"{name}-Italic")
                _fonts_registered["family"] = family
                return family
            except Exception:  # pragma: no cover - fuentes corruptas
                continue

    family = ("Helvetica", "Helvetica-Bold", "Helvetica-Oblique")
    _fonts_registered["family"] = family
    return family


def _escape(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def _pdf_styles():
    regular, bold, italic = _pdf_fonts()
    base = ParagraphStyle(
        "cv-body",
        fontName=regular,
        fontSize=BODY_SIZE_PT,
        leading=BODY_SIZE_PT * 1.32,
        textColor=colors.HexColor(TEXT_COLOR_HEX),
        alignment=TA_LEFT,
        spaceBefore=0,
        spaceAfter=3,
    )
    return {
        "name": ParagraphStyle(
            "cv-name",
            parent=base,
            fontName=bold,
            fontSize=NAME_SIZE_PT,
            leading=NAME_SIZE_PT * 1.2,
            alignment=TA_CENTER,
            spaceAfter=2,
        ),
        "contact": ParagraphStyle(
            "cv-contact",
            parent=base,
            fontSize=CONTACT_SIZE_PT,
            leading=CONTACT_SIZE_PT * 1.35,
            alignment=TA_CENTER,
            spaceAfter=4,
        ),
        "heading": ParagraphStyle(
            "cv-heading",
            parent=base,
            fontName=bold,
            fontSize=SECTION_SIZE_PT,
            leading=SECTION_SIZE_PT * 1.25,
            spaceBefore=8,
            spaceAfter=3,
        ),
        "body": base,
        "entry_left": ParagraphStyle(
            "cv-entry-left",
            parent=base,
            fontName=bold,
            spaceBefore=0,
            spaceAfter=0,
        ),
        "entry_right": ParagraphStyle(
            "cv-entry-right",
            parent=base,
            alignment=TA_RIGHT,
            spaceBefore=0,
            spaceAfter=0,
        ),
        "bullet": ParagraphStyle(
            "cv-bullet",
            parent=base,
            leftIndent=12,
            bulletIndent=0,
            bulletFontName=regular,
            bulletFontSize=BODY_SIZE_PT,
            spaceBefore=0,
            spaceAfter=2,
        ),
    }


def _pdf_segments_html(segments: list[Segment]) -> str:
    chunks = []
    for text, bold, italic in segments:
        html = _escape(text)
        if bold:
            html = f"<b>{html}</b>"
        if italic:
            html = f"<i>{html}</i>"
        chunks.append(html)
    return "".join(chunks)


def _pdf_heading_flowable(text: str, style) -> list:
    from reportlab.platypus import HRFlowable

    paragraph = Paragraph(_escape(text), style)
    rule = HRFlowable(
        width="100%",
        thickness=0.6,
        color=colors.HexColor(TEXT_COLOR_HEX),
        spaceBefore=0,
        spaceAfter=4,
    )
    return [KeepTogether([paragraph, rule])]


def render_pdf(cv: CvData) -> bytes:
    """Genera el PDF Harvard y devuelve sus bytes."""
    styles = _pdf_styles()
    content_width = CONTENT_WIDTH_CM * cm
    date_width = 4.2 * cm

    story: list = []
    for item in build_layout(cv):
        if item.kind == "name":
            story.append(Paragraph(_escape(item.text), styles["name"]))
        elif item.kind == "contact":
            story.append(Paragraph(_escape(item.text), styles["contact"]))
        elif item.kind == "heading":
            story.extend(_pdf_heading_flowable(item.text, styles["heading"]))
        elif item.kind == "text":
            story.append(Paragraph(_escape(item.text), styles["body"]))
        elif item.kind == "entry":
            left = Paragraph(
                f"<b>{_escape(item.left)}</b>",
                styles["entry_left"],
            )
            right = Paragraph(_escape(item.right), styles["entry_right"])
            table = Table(
                [[left, right]],
                colWidths=[content_width - date_width, date_width],
            )
            table.setStyle(TableStyle([
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ALIGN", (1, 0), (1, 0), "RIGHT"),
            ]))
            story.append(table)
        elif item.kind == "bullet":
            story.append(Paragraph(
                _pdf_segments_html(item.segments),
                styles["bullet"],
                bulletText="•",
            ))
        elif item.kind == "spacer":
            story.append(Spacer(1, 4))

    buffer = BytesIO()
    author = (cv.name or "").strip() or "CvCreator"
    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=MARGIN_CM * cm,
        rightMargin=MARGIN_CM * cm,
        topMargin=MARGIN_CM * cm,
        bottomMargin=MARGIN_CM * cm,
        title=f"CV - {author}",
        author=author,
        subject="Curriculum Vitae",
    )
    document.build(story)
    return buffer.getvalue()

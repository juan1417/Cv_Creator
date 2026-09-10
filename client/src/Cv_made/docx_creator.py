"""Creates DOCX files using the paragraph-based plantilla.docx template.

Strategy: Open template → clear all body content → rebuild paragraphs from scratch
using the template's existing styles. This avoids placeholder duplication issues.
"""
import copy
from pathlib import Path

from docx import Document
from docx.shared import Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

from .cv_models import CvData

FONT_NAME = "Arial"
COLOR_TEXT = RGBColor(0x40, 0x40, 0x40)
TEMPLATE_PATH = Path(__file__).parent / "plantilla.docx"


# ---------------------------------------------------------------------------
# Low-level XML helpers
# ---------------------------------------------------------------------------

def _make_run(text, bold=False, italic=False, size_pt=None, color=COLOR_TEXT, font=FONT_NAME):
    """Create a <w:r> element with styling."""
    r = OxmlElement('w:r')
    rPr = OxmlElement('w:rPr')

    rFonts = OxmlElement('w:rFonts')
    rFonts.set(qn('w:ascii'), font)
    rFonts.set(qn('w:hAnsi'), font)
    rPr.append(rFonts)

    if size_pt is not None:
        for tag in ('w:sz', 'w:szCs'):
            elem = OxmlElement(tag)
            elem.set(qn('w:val'), str(int(size_pt * 2)))
            rPr.append(elem)

    if bold:
        rPr.append(OxmlElement('w:b'))
        rPr.append(OxmlElement('w:bCs'))
    if italic:
        rPr.append(OxmlElement('w:i'))
        rPr.append(OxmlElement('w:iCs'))

    if color:
        c = OxmlElement('w:color')
        c.set(qn('w:val'), str(color))
        rPr.append(c)

    r.append(rPr)
    t = OxmlElement('w:t')
    t.set(qn('xml:space'), 'preserve')
    t.text = text
    r.append(t)
    return r


def _clear_body(doc):
    """Remove all paragraphs from document body, keeping the body element."""
    body = doc.element.body
    for child in list(body):
        if child.tag == qn('w:p'):
            body.remove(child)


def _add_para(doc, text="", bold=False, italic=False, size_pt=None,
              color=COLOR_TEXT, alignment=None, style_name=None):
    """Append a new paragraph to the document body."""
    p_elem = OxmlElement('w:p')

    # Style
    if style_name:
        pPr = OxmlElement('w:pPr')
        pStyle = OxmlElement('w:pStyle')
        try:
            style = doc.styles[style_name]
            pStyle.set(qn('w:val'), style.style_id)
        except KeyError:
            pStyle.set(qn('w:val'), style_name)
        pPr.append(pStyle)

        if alignment is not None:
            jc = OxmlElement('w:jc')
            align_map = {
                WD_ALIGN_PARAGRAPH.CENTER: 'center',
                WD_ALIGN_PARAGRAPH.LEFT: 'left',
                WD_ALIGN_PARAGRAPH.RIGHT: 'right',
            }
            jc.set(qn('w:val'), align_map.get(alignment, 'left'))
            pPr.append(jc)

        p_elem.append(pPr)
    elif alignment is not None:
        pPr = OxmlElement('w:pPr')
        jc = OxmlElement('w:jc')
        align_map = {
            WD_ALIGN_PARAGRAPH.CENTER: 'center',
            WD_ALIGN_PARAGRAPH.LEFT: 'left',
            WD_ALIGN_PARAGRAPH.RIGHT: 'right',
        }
        jc.set(qn('w:val'), align_map.get(alignment, 'left'))
        pPr.append(jc)
        p_elem.append(pPr)

    if text:
        p_elem.append(_make_run(text, bold=bold, italic=italic, size_pt=size_pt, color=color))

    doc.element.body.append(p_elem)
    return p_elem


def _add_para_multirun(doc, runs_data, style_name=None, alignment=None):
    """Append a paragraph with multiple styled runs."""
    p_elem = OxmlElement('w:p')

    if style_name:
        pPr = OxmlElement('w:pPr')
        pStyle = OxmlElement('w:pStyle')
        try:
            style = doc.styles[style_name]
            pStyle.set(qn('w:val'), style.style_id)
        except KeyError:
            pStyle.set(qn('w:val'), style_name)
        pPr.append(pStyle)
        if alignment is not None:
            jc = OxmlElement('w:jc')
            align_map = {
                WD_ALIGN_PARAGRAPH.CENTER: 'center',
                WD_ALIGN_PARAGRAPH.LEFT: 'left',
            }
            jc.set(qn('w:val'), align_map.get(alignment, 'left'))
            pPr.append(jc)
        p_elem.append(pPr)

    for rd in runs_data:
        if rd.get('text'):
            p_elem.append(_make_run(
                rd['text'],
                bold=rd.get('bold', False),
                italic=rd.get('italic', False),
                size_pt=rd.get('size_pt'),
                color=rd.get('color', COLOR_TEXT),
            ))

    doc.element.body.append(p_elem)
    return p_elem


def _add_empty(doc):
    """Add an empty paragraph."""
    _add_para(doc, "")


def _add_bullet(doc, text):
    """Add a bullet-point paragraph (List Paragraph style)."""
    p_elem = _add_para(doc, f"  {text}", style_name="List Paragraph")
    return p_elem


def _format_date(start: str, end: str | None) -> str:
    """Format date range like 'mar. 2023 - Presente'."""
    if not start:
        return ""
    from datetime import datetime
    try:
        s = datetime.strptime(start, "%Y-%m-%d")
        start_str = s.strftime("%b %Y").capitalize()
    except (ValueError, TypeError):
        start_str = start
    if not end:
        return f"{start_str} - Presente"
    try:
        e = datetime.strptime(end, "%Y-%m-%d")
        end_str = e.strftime("%b %Y").capitalize()
    except (ValueError, TypeError):
        end_str = end
    return f"{start_str} - {end_str}"


# ---------------------------------------------------------------------------
# Section builders
# ---------------------------------------------------------------------------

def _build_header(doc, cv):
    """Name + contact line."""
    _add_para(doc, cv.name.upper(), bold=True, size_pt=16, color=COLOR_TEXT,
              alignment=WD_ALIGN_PARAGRAPH.LEFT)

    parts = []
    if cv.address:
        parts.append(cv.address)
    if cv.email:
        parts.append(cv.email)
    phone = f"+{cv.phone}" if cv.phone and not cv.phone.startswith("+") else cv.phone
    if phone:
        parts.append(phone)
    if cv.linkedin:
        parts.append(cv.linkedin)
    if cv.portfolio:
        parts.append(cv.portfolio)
    _add_para(doc, " ● ".join(parts), size_pt=11, color=COLOR_TEXT)

    _add_empty(doc)
    _add_empty(doc)


def _build_perfil(doc, cv):
    """PERFIL PROFESIONAL section."""
    _add_para(doc, "PERFIL PROFESIONAL", bold=True, size_pt=12, color=COLOR_TEXT)
    _add_empty(doc)
    _add_para(doc, cv.about if cv.about else "")
    _add_empty(doc)


def _build_educacion(doc, cv):
    """EDUCACIÓN section."""
    if not cv.education:
        return
    _add_para(doc, "EDUCACIÓN", bold=True, size_pt=12, color=COLOR_TEXT)
    _add_empty(doc)

    for edu in cv.education:
        date_str = _format_date(edu.start_date, edu.end_date)
        _add_para_multirun(doc, [
            {'text': edu.degree, 'bold': True},
            {'text': '\t'},
            {'text': date_str},
        ])
        _add_para(doc, edu.institution, italic=True, size_pt=11)
        if edu.description:
            _add_para(doc, edu.description)
        _add_empty(doc)


def _build_experiencia(doc, cv):
    """EXPERIENCIA PROFESIONAL section."""
    if not cv.experience:
        return
    _add_para(doc, "EXPERIENCIA PROFESIONAL", bold=True, size_pt=12, color=COLOR_TEXT)
    _add_empty(doc)

    for exp in cv.experience:
        date_str = _format_date(exp.start_date, exp.end_date)
        _add_para_multirun(doc, [
            {'text': exp.company, 'bold': True},
            {'text': '\t'},
            {'text': date_str},
        ])
        if exp.title:
            _add_para(doc, exp.title)
        if exp.description:
            _add_para(doc, exp.description)
        _add_empty(doc)


def _build_habilidades(doc, cv):
    """HABILIDADES section — pipe-separated."""
    if not cv.skills:
        return
    _add_para(doc, "HABILIDADES", bold=True, size_pt=12, color=COLOR_TEXT)
    _add_empty(doc)
    _add_para(doc, " | ".join(cv.skills))
    _add_empty(doc)


def _build_logros(doc, cv):
    """LOGROS DESTACADOS section."""
    if not cv.achievements:
        return
    _add_para(doc, "LOGROS DESTACADOS", bold=True, size_pt=12, color=COLOR_TEXT)
    _add_empty(doc)

    for ach in cv.achievements:
        text = ach.title
        if ach.description:
            text += f" — {ach.description}"
        _add_para(doc, text)
        _add_empty(doc)


def _build_programas(doc, cv):
    """PROGRAMAS section."""
    if not cv.programs:
        return
    _add_para(doc, "PROGRAMAS", bold=True, size_pt=12, color=COLOR_TEXT)
    _add_empty(doc)
    _add_para(doc, " | ".join(cv.programs))
    _add_empty(doc)


def _build_idiomas(doc, cv):
    """IDIOMAS section."""
    if not cv.languages:
        return
    _add_para(doc, "IDIOMAS", bold=True, size_pt=12, color=COLOR_TEXT)
    _add_empty(doc)
    lang_parts = [f"{lang.name} ({lang.level})" if lang.level else lang.name for lang in cv.languages]
    _add_para(doc, " | ".join(lang_parts))
    _add_empty(doc)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def create_docx(cv_data: CvData, output_dir: str = "output") -> Path:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    doc = Document(str(TEMPLATE_PATH))
    _clear_body(doc)

    _build_header(doc, cv_data)
    _build_perfil(doc, cv_data)
    _build_educacion(doc, cv_data)
    _build_experiencia(doc, cv_data)
    _build_habilidades(doc, cv_data)
    _build_logros(doc, cv_data)
    _build_programas(doc, cv_data)
    _build_idiomas(doc, cv_data)

    safe_name = cv_data.name.replace(" ", "_").replace("/", "_")
    file_path = output_path / f"{safe_name}_cv.docx"
    doc.save(str(file_path))
    return file_path

import copy
from pathlib import Path
from docx import Document
from docx.shared import Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

from .cv_models import CvData

FONT_NAME = "STIX Two Text"
COLOR_DARK = RGBColor(0x1A, 0x1A, 0x2E)
TEMPLATE_PATH = Path(__file__).parent / "Copia de Plantilla CV - Harvard.docx"


def _set_cell_font(cell, text: str, size: float = 10.5, bold: bool = False,
                   color: RGBColor | None = None, align: int | None = None):
    cell.text = ""
    p = cell.paragraphs[0]
    if align is not None:
        p.alignment = align
    run = p.add_run(text)
    run.font.name = FONT_NAME
    run.font.size = Pt(size)
    run.font.bold = bold
    if color:
        run.font.color.rgb = color


def _set_cell_multiline(cell, lines: list, size: float = 10.5, bold: bool = False,
                         color: RGBColor | None = None):
    cell.text = ""
    for i, line in enumerate(lines):
        p = cell.paragraphs[0] if i == 0 else cell.add_paragraph()
        run = p.add_run(line)
        run.font.name = FONT_NAME
        run.font.size = Pt(size)
        run.font.bold = bold
        if color:
            run.font.color.rgb = color


def _set_cell_multiline_raw(tc, lines: list, size: float = 10.5, bold: bool = False,
                              color: RGBColor | None = None):
    for p in tc.findall(qn('w:p')):
        tc.remove(p)
    for i, line in enumerate(lines):
        p_elem = OxmlElement('w:p')
        r_elem = OxmlElement('w:r')
        rPr = OxmlElement('w:rPr')
        rFonts = OxmlElement('w:rFonts')
        rFonts.set(qn('w:ascii'), FONT_NAME)
        rFonts.set(qn('w:hAnsi'), FONT_NAME)
        rPr.append(rFonts)
        sz = OxmlElement('w:sz')
        sz.set(qn('w:val'), str(int(size * 2)))
        rPr.append(sz)
        if bold:
            b = OxmlElement('w:b')
            rPr.append(b)
        if color:
            color_elem = OxmlElement('w:color')
            color_elem.set(qn('w:val'), str(color))
            rPr.append(color_elem)
        r_elem.append(rPr)
        t = OxmlElement('w:t')
        t.set(qn('xml:space'), 'preserve')
        t.text = line
        r_elem.append(t)
        p_elem.append(r_elem)
        tc.append(p_elem)


def _merge_cells(table, row: int, col_start: int, col_end: int):
    table.cell(row, col_start).merge(table.cell(row, col_end))


def _get_tr_elements(table):
    tbl = table._tbl
    return [child for child in tbl if child.tag == qn('w:tr')]


def _set_row7(table, exp):
    tbl = table._tbl
    tr = _get_tr_elements(table)[7]
    tcs = tr.findall(qn('w:tc'))
    if len(tcs) >= 2:
        tc0, tc1 = tcs[0], tcs[-1]
        _set_cell_multiline_raw(tc0, [exp.company, exp.title], bold=True, color=COLOR_DARK)
        _set_cell_multiline_raw(tc1, [exp.duration])
    else:
        _set_cell_multiline(table.cell(7, 0), [exp.company, exp.title], bold=True, color=COLOR_DARK)
        _set_cell_multiline(table.cell(7, 4), [exp.duration])


def _set_row12(table, edu, row_idx: int = 12):
    tbl = table._tbl
    tr = _get_tr_elements(table)[row_idx]
    tcs = tr.findall(qn('w:tc'))
    if len(tcs) >= 2:
        tc0, tc1 = tcs[0], tcs[-1]
        _set_cell_multiline_raw(tc0, [edu.school, edu.degree], bold=True, color=COLOR_DARK)
        loc_year = [p for p in [edu.location, edu.year] if p]
        _set_cell_multiline_raw(tc1, loc_year)
    else:
        _set_cell_multiline(table.cell(row_idx, 0), [edu.school, edu.degree], bold=True, color=COLOR_DARK)
        loc_year = [p for p in [edu.location, edu.year] if p]
        _set_cell_multiline(table.cell(row_idx, 3), loc_year)


def _insert_exp_rows(table, exp, after_row: int = 9):
    tbl = table._tbl
    tr_list = _get_tr_elements(table)

    new_header = copy.deepcopy(tr_list[7])
    new_desc = copy.deepcopy(tr_list[8])

    ref_tr = tr_list[after_row]
    ref_idx = list(tbl).index(ref_tr)

    tbl.insert(ref_idx + 1, new_desc)
    tbl.insert(ref_idx + 1, new_header)

    new_idx = after_row + 1
    _set_cell_multiline(table.cell(new_idx, 0), [exp.company, exp.title], bold=True, color=COLOR_DARK)
    _set_cell_multiline(table.cell(new_idx, 4), [exp.duration])
    _set_cell_font(table.cell(new_idx + 1, 0), exp.description, size=10.5)


def create_docx(cv_data: CvData, output_dir: str = "output") -> Path:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    doc = Document(str(TEMPLATE_PATH))
    table = doc.tables[0]

    _set_cell_font(table.cell(0, 0), cv_data.name, size=24, bold=True, color=COLOR_DARK,
                   align=WD_ALIGN_PARAGRAPH.CENTER)

    contact_parts = [cv_data.address]
    if cv_data.linkedin:
        contact_parts.append(cv_data.linkedin)
    phone = f"+{cv_data.phone}" if not cv_data.phone.startswith("+") else cv_data.phone
    contact_parts.append(phone)
    contact_parts.append(cv_data.email)
    contact_str = " \u2022 ".join(contact_parts)
    _set_cell_font(table.cell(1, 0), contact_str, size=11, align=WD_ALIGN_PARAGRAPH.CENTER)

    _set_cell_font(table.cell(3, 0), cv_data.about, size=10.5)

    _set_cell_font(table.cell(5, 0), "EXPERIENCIA PROFESIONAL", size=12, bold=True,
                   color=COLOR_DARK, align=WD_ALIGN_PARAGRAPH.CENTER)

    if cv_data.experience:
        exp = cv_data.experience[0]
        _set_row7(table, exp)
        _set_cell_font(table.cell(8, 0), exp.description, size=10.5)

    extra_exp_count = max(0, len(cv_data.experience) - 1)
    for exp in cv_data.experience[1:]:
        _insert_exp_rows(table, exp, after_row=9)

    offset = 2 * extra_exp_count

    _set_cell_font(table.cell(10 + offset, 0), "EDUCACIÓN", size=12, bold=True,
                   color=COLOR_DARK, align=WD_ALIGN_PARAGRAPH.CENTER)

    if cv_data.education:
        edu = cv_data.education[0]
        _set_row12(table, edu, row_idx=12 + offset)

    for edu in cv_data.education[1:]:
        tbl = table._tbl
        tr_list = _get_tr_elements(table)
        ref_tr = tr_list[13 + offset]

        new_tr1 = copy.deepcopy(tr_list[12 + offset])
        new_tr2 = copy.deepcopy(tr_list[13 + offset])
        ref_idx = list(tbl).index(ref_tr)

        tbl.insert(ref_idx + 1, new_tr2)
        tbl.insert(ref_idx + 1, new_tr1)

        _set_cell_multiline(table.cell(13 + offset, 0), [edu.school, edu.degree], bold=True, color=COLOR_DARK)
        loc_year = [p for p in [edu.location, edu.year] if p]
        _set_cell_multiline(table.cell(13 + offset, 3), loc_year)

    _set_cell_font(table.cell(14 + offset, 0), "SKILLS ADICIONALES", size=12, bold=True,
                   color=COLOR_DARK, align=WD_ALIGN_PARAGRAPH.CENTER)

    skills_text = "\n".join(f"\u2022 {s}" for s in cv_data.skills) if cv_data.skills else ""
    _set_cell_font(table.cell(16 + offset, 0), skills_text, size=10.5)

    _set_cell_font(table.cell(17 + offset, 0), "TECNOLOGÍAS", size=12, bold=True,
                   color=COLOR_DARK, align=WD_ALIGN_PARAGRAPH.CENTER)

    tech_text = ", ".join(cv_data.skills) if cv_data.skills else ""
    _set_cell_font(table.cell(19 + offset, 0), tech_text, size=10.5)

    safe_name = cv_data.name.replace(" ", "_").replace("/", "_")
    file_path = output_path / f"{safe_name}_cv.docx"
    doc.save(str(file_path))
    return file_path

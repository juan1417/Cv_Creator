from io import BytesIO

from docx import Document
from pypdf import PdfReader

from Cv_made import (
    CvData,
    expected_fragments,
    render_docx,
    render_pdf,
    validate_export,
)
from Cv_made.harvard import _skill_groups, build_layout, format_date


def test_renderers_return_bytes_not_files(cv, tmp_path):
    docx_bytes = render_docx(cv)
    pdf_bytes = render_pdf(cv)
    assert isinstance(docx_bytes, bytes) and docx_bytes.startswith(b"PK")
    assert isinstance(pdf_bytes, bytes) and pdf_bytes.startswith(b"%PDF")
    # Los renderers no escriben en disco.
    assert list(tmp_path.iterdir()) == []


def test_format_date_is_spanish_and_locale_independent():
    assert format_date("2023-03-01", None) == "mar 2023 - Presente"
    assert format_date("2019-01-01", "2021-02-01") == "ene 2019 - feb 2021"
    assert format_date("2019", None) == "2019 - Presente"
    assert format_date(None, None) == ""


def test_docx_is_ats_friendly(cv):
    docx_bytes = render_docx(cv)
    document = Document(BytesIO(docx_bytes))
    text = "\n".join(p.text for p in document.paragraphs)

    assert document.tables == []
    assert len(document.inline_shapes) == 0
    assert text.strip()

    # Nombre centrado en mayúsculas y encabezados estándar.
    assert "ANA PÉREZ" in text
    for heading in expected_fragments(cv):
        if heading.isupper():
            assert heading in text

    # Una sola columna: nada de contenido en tablas.
    assert "EXPERIENCIA PROFESIONAL" in text
    assert "mar 2021 - Presente" in text or "mar 2021" in text


def test_pdf_extracts_text_and_fits_one_page(cv):
    pdf_bytes = render_pdf(cv)
    reader = PdfReader(BytesIO(pdf_bytes))
    assert len(reader.pages) == 1
    text = "\n".join(page.extract_text() or "" for page in reader.pages)
    assert "ANA PÉREZ" in text
    assert "ana@example.com" in text
    assert "EXPERIENCIA PROFESIONAL" in text


def test_validation_passes_for_both_formats(cv):
    expected = expected_fragments(cv)
    docx_result = validate_export(render_docx(cv), "docx", expected)
    pdf_result = validate_export(render_pdf(cv), "pdf", expected)
    assert docx_result.ok, docx_result.problems
    assert pdf_result.ok, pdf_result.problems
    assert docx_result.missing == []
    assert pdf_result.missing == []


def test_validation_detects_missing_fragment(cv):
    expected = expected_fragments(cv) + ["Fragmento Inexistente"]
    result = validate_export(render_docx(cv), "docx", expected)
    assert not result.ok
    assert result.missing == ["Fragmento Inexistente"]


# ─── HABILIDADES agrupadas por categoría ──────────────────────────────────────

def _cv_con_categorias() -> CvData:
    return CvData(
        name="Ana Pérez",
        email="ana@example.com",
        skills=[
            {"name": "Python", "type": "tech", "category": "Lenguajes"},
            {"name": "TypeScript", "type": "tech", "category": "Lenguajes"},
            {"name": "FastAPI", "type": "tech", "category": "Backend"},
            {"name": ".NET", "type": "tech", "category": ""},
            {"name": "Comunicación", "type": "soft", "category": "Soft Skills"},
        ],
        programs=["Scrum"],
    )


def test_skill_groupsOrdena_por_categoria_y_encaja_lo_desconocido():
    groups = _skill_groups(_cv_con_categorias())

    etiquetas = [label for label, _ in groups]
    assert etiquetas == ["Lenguajes", "Backend", "Otros conocimientos", "Habilidades blandas"]
    assert groups[0][1] == ["Python", "TypeScript"]
    # lo que no está en el catálogo y los programas comparten línea de rebrote
    assert groups[2][1] == [".NET", "Scrum"]
    assert groups[3][1] == ["Comunicación"]


def test_habilidades_aparecen_agrupadas_en_docx_y_pdf():
    cv = _cv_con_categorias()
    docx_text = "\n".join(
        p.text for p in Document(BytesIO(render_docx(cv))).paragraphs
    )
    pdf_text = "\n".join(
        page.extract_text() or "" for page in PdfReader(BytesIO(render_pdf(cv))).pages
    )

    for texto in (docx_text, pdf_text):
        assert "Lenguajes: Python, TypeScript" in texto
        assert "Habilidades blandas: Comunicación" in texto
        # la sección aparte de TECNOLOGÍAS desapareció
        assert "TECNOLOGÍAS" not in texto


def test_una_sola_seccion_de_habilidades(cv):
    headings = [item.text for item in build_layout(cv) if item.kind == "heading"]
    assert headings.count("HABILIDADES") == 1
    assert "TECNOLOGÍAS" not in headings

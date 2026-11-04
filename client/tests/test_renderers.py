from io import BytesIO

from docx import Document
from pypdf import PdfReader

from Cv_made import expected_fragments, render_docx, render_pdf, validate_export
from Cv_made.harvard import format_date


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

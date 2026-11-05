"""Validación post-generación de los archivos exportados.

No confía en el renderer: vuelve a abrir el archivo generado y comprueba que un
parser ATS pueda leer el texto. Un DOCX con tablas o imágenes, o un PDF sin
texto extraíble, se reportan como problema.
"""

from dataclasses import dataclass, field
from io import BytesIO

from docx import Document
from pypdf import PdfReader

from text_norm import normalize


@dataclass
class ExportValidation:
    format: str
    ok: bool = False
    pages: int = 0
    characters: int = 0
    present: list[str] = field(default_factory=list)
    missing: list[str] = field(default_factory=list)
    problems: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {
            "format": self.format,
            "ok": self.ok,
            "pages": self.pages,
            "characters": self.characters,
            "present": self.present,
            "missing": self.missing,
            "problems": self.problems,
            "warnings": self.warnings,
        }


def _check_fragments(text: str, expected: list[str]) -> tuple[list[str], list[str]]:
    haystack = normalize(text)
    present: list[str] = []
    missing: list[str] = []
    for fragment in expected:
        needle = normalize(fragment)
        if not needle:
            continue
        if needle in haystack:
            present.append(fragment)
        else:
            missing.append(fragment)
    return present, missing


def validate_docx_bytes(data: bytes, expected: list[str]) -> ExportValidation:
    result = ExportValidation(format="docx")
    try:
        document = Document(BytesIO(data))
    except Exception as exc:  # pragma: no cover - archivo corrupto
        result.problems.append(f"No se pudo abrir el DOCX: {exc}")
        return result

    text = "\n".join(paragraph.text for paragraph in document.paragraphs)
    result.characters = len(text.strip())

    if document.tables:
        result.problems.append(
            f"El DOCX contiene {len(document.tables)} tabla(s); los ATS las ignoran."
        )
    if document.inline_shapes:
        result.problems.append(
            f"El DOCX contiene {len(document.inline_shapes)} imagen(es) incrustada(s)."
        )
    if result.characters == 0:
        result.problems.append("El DOCX no tiene texto legible.")

    result.present, result.missing = _check_fragments(text, expected)
    for fragment in result.missing:
        result.problems.append(f"Falta en el documento: {fragment}")

    result.pages = 0
    result.ok = not result.problems
    return result


def validate_pdf_bytes(data: bytes, expected: list[str]) -> ExportValidation:
    result = ExportValidation(format="pdf")
    try:
        reader = PdfReader(BytesIO(data))
    except Exception as exc:  # pragma: no cover - archivo corrupto
        result.problems.append(f"No se pudo abrir el PDF: {exc}")
        return result

    result.pages = len(reader.pages)
    text = "\n".join(page.extract_text() or "" for page in reader.pages)
    result.characters = len(text.strip())

    if result.pages == 0:
        result.problems.append("El PDF no tiene páginas.")
    if result.characters == 0:
        result.problems.append("El PDF no tiene texto extraíble (posible documento escaneado).")
    if result.pages > 1:
        result.warnings.append(
            f"El PDF ocupa {result.pages} páginas; el formato Harvard apunta a una."
        )

    result.present, result.missing = _check_fragments(text, expected)
    for fragment in result.missing:
        result.problems.append(f"Falta en el documento: {fragment}")

    result.ok = not result.problems
    return result


def validate_export(
    data: bytes, export_format: str, expected: list[str]
) -> ExportValidation:
    if export_format == "docx":
        return validate_docx_bytes(data, expected)
    if export_format == "pdf":
        return validate_pdf_bytes(data, expected)
    raise ValueError(f"Formato no soportado: {export_format}")

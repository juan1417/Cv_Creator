"""Motor ATS determinista.

No usa LLM. Mide lo que un sistema de seguimiento de candidaturas realmente
evalúa:

1. Datos de contacto que el parser necesita para indexar al candidato.
2. Presencia de las secciones estándar que el parser busca.
3. Formato legible: fechas, descripciones y líneas de longitud razonable.
4. Cobertura de las palabras clave de la vacante.

Las cuatro partes pesan 25 puntos cada una.
"""

import re

from models.cv_analysis import ATSMetrics, KeywordCoverage, MetricDetail

from .keywords import KEYWORD_MAX_SCORE, keyword_coverage

CONTACT_PTS = 25.0
SECTION_PTS = 25.0
FORMAT_PTS = 25.0

MAX_DESCRIPTION_LINE = 260

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[A-Za-z]{2,}$")
_PHONE_DIGITS_RE = re.compile(r"\d")

_STANDARD_SECTIONS = (
    ("Resumen profesional", "about"),
    ("Experiencia laboral", "experience"),
    ("Formación académica", "education"),
    ("Habilidades", "skills"),
)


def _status(score: float) -> str:
    if score >= 80:
        return "excellent"
    if score >= 60:
        return "good"
    if score >= 40:
        return "fair"
    return "poor"


def cv_plain_text(cv_data: dict) -> str:
    """Todo el texto visible del CV, en el orden en que lo lee un parser."""
    cv = cv_data.get("cv", {})
    parts: list[str] = [
        cv.get("name", ""),
        cv.get("about", ""),
    ]

    for experience in cv_data.get("experience", []):
        parts.extend([
            experience.get("title", ""),
            experience.get("company", ""),
            experience.get("description", ""),
        ])

    for skill in cv_data.get("skills", []):
        parts.append(skill.get("name", ""))

    for education in cv_data.get("education", []):
        parts.extend([
            education.get("degree", ""),
            education.get("institution", ""),
            education.get("description", ""),
        ])

    for achievement in cv_data.get("achievements", []):
        parts.extend([
            achievement.get("title", ""),
            achievement.get("description", ""),
        ])

    for program in cv_data.get("programs", []):
        parts.append(program.get("name", "") if isinstance(program, dict) else str(program))

    for language in cv_data.get("languages", []):
        parts.append(language.get("name", ""))

    return "\n".join(part for part in parts if part)


def _contact_detail(cv: dict) -> tuple[MetricDetail, float]:
    checks = (
        ("nombre", bool((cv.get("name") or "").strip())),
        ("email", bool(_EMAIL_RE.match((cv.get("email") or "").strip()))),
        ("teléfono", bool(_PHONE_DIGITS_RE.search(cv.get("phone") or ""))),
    )
    filled = sum(1 for _, ok in checks if ok)
    score = round(CONTACT_PTS * filled / len(checks), 1)
    missing = [label for label, ok in checks if not ok]

    return MetricDetail(
        name="Datos de contacto",
        score=score,
        max_score=CONTACT_PTS,
        status=_status(score / CONTACT_PTS * 100),
        message=f"{filled}/{len(checks)} datos de contacto válidos",
        suggestions=(
            [] if not missing else [f"Completá o corregí: {', '.join(missing)}"]
        ),
    ), score


def _sections_detail(cv_data: dict) -> tuple[MetricDetail, float]:
    cv = cv_data.get("cv", {})
    values = {
        "about": cv.get("about"),
        "experience": cv_data.get("experience"),
        "education": cv_data.get("education"),
        "skills": cv_data.get("skills"),
    }

    present: list[str] = []
    missing: list[str] = []
    for label, key in _STANDARD_SECTIONS:
        value = values.get(key)
        has_value = bool(value.strip()) if isinstance(value, str) else bool(value)
        (present if has_value else missing).append(label)

    score = round(SECTION_PTS * len(present) / len(_STANDARD_SECTIONS), 1)
    return MetricDetail(
        name="Secciones estándar",
        score=score,
        max_score=SECTION_PTS,
        status=_status(score / SECTION_PTS * 100),
        message=f"{len(present)}/{len(_STANDARD_SECTIONS)} secciones presentes",
        suggestions=(
            [] if not missing else [f"Agregá una sección de: {', '.join(missing)}"]
        ),
    ), score


def _format_detail(cv_data: dict) -> tuple[MetricDetail, float]:
    experiences = cv_data.get("experience", [])
    education = cv_data.get("education", [])
    entries = list(experiences) + list(education)

    dated = sum(
        1 for entry in entries
        if entry.get("start_date") or entry.get("end_date")
    )
    dated_ratio = dated / len(entries) if entries else 0.0

    with_description = sum(
        1 for experience in experiences
        if (experience.get("description") or "").strip()
    )
    description_ratio = with_description / len(experiences) if experiences else 0.0

    long_line_entries = 0
    for experience in experiences:
        description = (experience.get("description") or "").strip()
        if not description:
            continue
        if any(len(line) > MAX_DESCRIPTION_LINE for line in description.splitlines()):
            long_line_entries += 1
    readable_ratio = (
        1.0 - long_line_entries / len(experiences) if experiences else 0.0
    )

    score = round(
        FORMAT_PTS * 0.4 * dated_ratio
        + FORMAT_PTS * 0.4 * description_ratio
        + FORMAT_PTS * 0.2 * readable_ratio,
        1,
    )

    suggestions: list[str] = []
    if entries and dated_ratio < 1.0:
        suggestions.append("Poné fecha de inicio (y fin) en cada experiencia y formación")
    if experiences and description_ratio < 1.0:
        suggestions.append("Agregá una descripción a cada experiencia")
    if long_line_entries:
        suggestions.append(
            f"Partí en viñetas las descripciones con líneas de más de {MAX_DESCRIPTION_LINE} caracteres"
        )

    return MetricDetail(
        name="Formato y legibilidad",
        score=score,
        max_score=FORMAT_PTS,
        status=_status(score / FORMAT_PTS * 100),
        message=(
            f"{dated}/{len(entries)} entradas con fecha, "
            f"{with_description}/{len(experiences)} experiencias con descripción"
        ),
        suggestions=suggestions,
    ), score


def _keywords_detail(
    cv_data: dict, job_description: str | None
) -> tuple[MetricDetail, float, KeywordCoverage]:
    if not (job_description or "").strip():
        coverage = KeywordCoverage(
            score=0.0,
            max_score=KEYWORD_MAX_SCORE,
            job_description_provided=False,
            message="Sin descripción del puesto: no se puede medir la cobertura de keywords.",
        )
        detail = MetricDetail(
            name="Cobertura de palabras clave",
            score=0.0,
            max_score=KEYWORD_MAX_SCORE,
            status="poor",
            message=coverage.message,
            suggestions=[
                "Pegá la descripción del puesto para medir qué keywords de la vacante faltan en tu CV"
            ],
        )
        return detail, 0.0, coverage

    coverage = keyword_coverage(cv_plain_text(cv_data), job_description)

    suggestions: list[str] = []
    if coverage.missing:
        top_missing = ", ".join(coverage.missing[:8])
        suggestions.append(
            f"Si es honesto para tu perfil, incluí estas keywords de la vacante: {top_missing}"
        )

    detail = MetricDetail(
        name="Cobertura de palabras clave",
        score=coverage.score,
        max_score=coverage.max_score,
        status=_status(coverage.score / coverage.max_score * 100),
        message=coverage.message,
        suggestions=suggestions,
    )
    return detail, coverage.score, coverage


def analyze_ats(cv_data: dict, job_description: str | None = None) -> ATSMetrics:
    """Calcula el score ATS determinista del CV (opcionalmente contra una vacante).

    Sin descripción del puesto no hay nada que comparar: el bloque de keywords
    queda sin medir y el score se normaliza sobre los 75 puntos aplicables, para
    no castigar al candidato por un dato que no aportó.
    """
    cv = cv_data.get("cv", {})

    contact_detail, contact_score = _contact_detail(cv)
    sections_detail, sections_score = _sections_detail(cv_data)
    format_detail, format_score = _format_detail(cv_data)
    keywords_detail, keywords_score, coverage = _keywords_detail(cv_data, job_description)

    raw_total = contact_score + sections_score + format_score + keywords_score
    applicable_max = (
        CONTACT_PTS + SECTION_PTS + FORMAT_PTS + KEYWORD_MAX_SCORE
        if coverage.job_description_provided
        else CONTACT_PTS + SECTION_PTS + FORMAT_PTS
    )
    total = round(raw_total * 100 / applicable_max, 1)

    return ATSMetrics(
        score=total,
        details=[
            contact_detail,
            sections_detail,
            format_detail,
            keywords_detail,
        ],
        keyword_coverage=coverage,
    )

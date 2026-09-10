import hashlib
import json
import logging
import os
import re
from uuid import UUID

from database.get_user_cv import get_user_cv_data, get_user_cv_formatted
from models.cv_analysis import (
    CVAnalysis,
    CompletenessMetrics,
    ContentMetrics,
    ATSMetrics,
    StructureMetrics,
    MetricDetail,
)
from .generator import generate_response

logger = logging.getLogger(__name__)

# Modelo específico para análisis. Si no está definido, usa MODELO.
ANALYSIS_MODEL = os.getenv("MODELO_ANALISIS") or os.getenv("MODELO")

# Cadena de modelos de respaldo (NVIDIA a través de OpenRouter).
def _analysis_model_chain() -> list[str]:
    chain = [
        ANALYSIS_MODEL,
        os.getenv("MODELO"),
    ]
    seen: set[str] = set()
    out: list[str] = []
    for m in chain:
        if m and m not in seen:
            seen.add(m)
            out.append(m)
    return out


# ─── Section Definitions ─────────────────────────────────────────────────────

SECTIONS = ("personal", "experience", "education", "skills", "languages")


def _section_fingerprint(section: str, cv_data: dict) -> str:
    """Hash de una sección individual del CV."""
    payload = json.dumps(cv_data.get(section, {}), sort_keys=True, default=str)
    return hashlib.md5(payload.encode("utf-8")).hexdigest()


def _full_fingerprint(cv_data: dict) -> str:
    """Hash completo del CV (para comparación general)."""
    payload = json.dumps(cv_data, sort_keys=True, default=str)
    return hashlib.md5(payload.encode("utf-8")).hexdigest()


# ─── Section-Level Cache ─────────────────────────────────────────────────────
# Estructura: { user_id: { section: (fingerprint, section_result) } }
# section_result es un dict con scores y detalles de esa sección específica.

_section_cache: dict[str, dict[str, tuple[str, dict]]] = {}


def _get_cached_section(user_id: str, section: str, fp: str) -> dict | None:
    """Devuelve el resultado cacheado de una sección si el fingerprint coincide."""
    user_cache = _section_cache.get(user_id, {})
    cached = user_cache.get(section)
    if cached and cached[0] == fp:
        return cached[1]
    return None


def _save_section_cache(user_id: str, section: str, fp: str, result: dict):
    """Guarda el resultado de una sección en cache."""
    if user_id not in _section_cache:
        _section_cache[user_id] = {}
    _section_cache[user_id][section] = (fp, result)


# ─── JSON Parsing ────────────────────────────────────────────────────────────

def _extract_json(text: str) -> str:
    """Extrae el primer objeto JSON balanceado, ignorando fences y basura."""
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    start = text.find("{")
    if start == -1:
        raise ValueError("No se encontró JSON en la respuesta")
    depth = 0
    in_str = False
    esc = False
    for i in range(start, len(text)):
        c = text[i]
        if in_str:
            if esc:
                esc = False
            elif c == "\\":
                esc = True
            elif c == '"':
                in_str = False
        else:
            if c == '"':
                in_str = True
            elif c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
                if depth == 0:
                    return text[start : i + 1]
    return text[start:]


def _parse_json_lenient(text: str) -> dict:
    raw = _extract_json(text)
    try:
        return json.loads(raw, strict=False)
    except json.JSONDecodeError:
        repaired = re.sub(r",\s*([}\]])", r"\1", raw)
        return json.loads(repaired, strict=False)


# ─── Section Analysis Prompts ────────────────────────────────────────────────

SECTION_PROMPTS = {
    "personal": """Analiza los DATOS PERSONALES y el RESUMEN PROFESIONAL de este CV.
Enfócate en: completitud de datos, calidad del "Sobre mí", presencia de portfolio y LinkedIn.

## Datos personales:
{section_data}

## Responde SOLO con JSON:
{{
  "score": 70,
  "details": [
    {{"name": "Datos de contacto", "score": 80, "max_score": 100, "status": "bueno", "message": " mensaje", "suggestions": ["sugerencia"]}},
    {{"name": "Resumen profesional", "score": 60, "max_score": 100, "status": "mejorable", "message": " mensaje", "suggestions": ["sugerencia"]}}
  ]
}}

## Reglas:
- Máximo 2 details, máximo 2 suggestions por detail
- NO sugieras agregar secciones que no existen
- Recomendaciones ESPECÍFICAS basadas en el contenido real
- JSON en español, comillas simples en strings""",

    "experience": """Analiza la EXPERIENCIA LABORAL de este CV.
Enfócate en: calidad de descripciones, logros cuantificables, verbos de acción, métricas, progresión de carrera.

## Experiencia:
{section_data}

## Responde SOLO con JSON:
{{
  "score": 70,
  "details": [
    {{"name": "Descripciones de experiencia", "score": 65, "max_score": 100, "status": "regular", "message": " mensaje", "suggestions": ["sugerencia"]}},
    {{"name": "Progresión de carrera", "score": 75, "max_score": 100, "status": "bueno", "message": " mensaje", "suggestions": ["sugerencia"]}}
  ]
}}

## Reglas:
- Máximo 2 details, máximo 2 suggestions por detail
- NO recomiendes "prácticas", "proyectos académicos" ni "freelance"
- El campo PORTFOLIO es para proyectos → si querés mencionar proyectos, decí "Completá tu portfolio con enlaces"
- Recomendaciones ESPECÍFICAS que mencionen el contenido real del CV
- JSON en español, comillas simples en strings""",

    "education": """Analiza la FORMACIÓN ACADÉMICA de este CV.
Enfócate en: relevancia, completitud, descripción.

## Formación:
{section_data}

## Responde SOLO con JSON:
{{
  "score": 75,
  "details": [
    {{"name": "Formación académica", "score": 75, "max_score": 100, "status": "bueno", "message": " mensaje", "suggestions": ["sugerencia"]}}
  ]
}}

## Reglas:
- Máximo 1 detail, máximo 2 suggestions
- NO sugieras agregar secciones que no existen
- JSON en español, comillas simples en strings""",

    "skills": """Analiza las HABILIDADES de este CV.
Enfócate en: variedad, equilibrio técnico/blanda, niveles, relevancia para el perfil.

## Habilidades:
{section_data}

## Responde SOLO con JSON:
{{
  "score": 70,
  "details": [
    {{"name": "Variedad y equilibrio", "score": 65, "max_score": 100, "status": "regular", "message": " mensaje", "suggestions": ["sugerencia"]}},
    {{"name": "Niveles de dominio", "score": 75, "max_score": 100, "status": "bueno", "message": " mensaje", "suggestions": ["sugerencia"]}}
  ]
}}

## Reglas:
- Máximo 2 details, máximo 2 suggestions por detail
- NO sugieras agregar secciones que no existen
- JSON en español, comillas simples en strings""",

    "languages": """Analiza los IDIOMAS de este CV.
Enfócate en: cantidad, niveles, relevancia.

## Idiomas:
{section_data}

## Responde SOLO con JSON:
{{
  "score": 70,
  "details": [
    {{"name": "Idiomas", "score": 70, "max_score": 100, "status": "bueno", "message": " mensaje", "suggestions": ["sugerencia"]}}
  ]
}}

## Reglas:
- Máximo 1 detail, máximo 2 suggestions
- NO sugieras agregar idiomas que no existen
- JSON en español, comillas simples en strings""",
}


def _section_to_text(section: str, cv_data: dict) -> str:
    """Convierte una sección del CV a texto para el prompt."""
    if section == "personal":
        cv = cv_data.get("cv", {})
        lines = [f"Nombre: {cv.get('name', '')}"]
        if cv.get("about"):
            lines.append(f"Sobre mí: {cv['about']}")
        if cv.get("porfolio"):
            lines.append(f"Portfolio: {cv['porfolio']}")
        if cv.get("linkedin"):
            lines.append(f"LinkedIn: {cv['linkedin']}")
        return "\n".join(lines)

    if section == "experience":
        exps = cv_data.get("experience", [])
        if not exps:
            return "Sin experiencia registrada."
        lines = []
        for e in exps:
            lines.append(f"- {e.get('title', '')} en {e.get('company', '')} ({e.get('start_date', '')} - {e.get('end_date', 'Presente')})")
            if e.get("description"):
                lines.append(f"  Descripción: {e['description']}")
        return "\n".join(lines)

    if section == "education":
        edus = cv_data.get("education", [])
        if not edus:
            return "Sin formación registrada."
        lines = []
        for ed in edus:
            lines.append(f"- {ed.get('degree', '')} en {ed.get('institution', '')} ({ed.get('start_date', '')} - {ed.get('end_date', 'Presente')})")
            if ed.get("description"):
                lines.append(f"  Descripción: {ed['description']}")
        return "\n".join(lines)

    if section == "skills":
        skills = cv_data.get("skills", [])
        if not skills:
            return "Sin habilidades registradas."
        return "\n".join(f"- {s['name']} ({s['level']})" for s in skills)

    if section == "languages":
        # Los idiomas vienen del FullCV, no de get_user_cv_data
        # Los manejamos por separado
        return "Los idiomas se analizan por separado."

    return ""


def _analyze_section(section: str, cv_data: dict) -> dict | None:
    """Analiza una sección individual con la IA. Devuelve el dict de resultado."""
    prompt_template = SECTION_PROMPTS.get(section)
    if not prompt_template:
        return None

    section_text = _section_to_text(section, cv_data)
    if not section_text or section_text.startswith("Sin ") or section_text.startswith("Los "):
        # Sección vacía o no aplicable
        return {
            "score": 0,
            "details": [{
                "name": section,
                "score": 0,
                "max_score": 100,
                "status": "débil",
                "message": f"Sin {section} registrados",
                "suggestions": [f"Agregá {section} a tu CV"],
            }],
        }

    prompt = prompt_template.format(section_data=section_text)
    messages = [
        {"role": "system", "content": "Eres un experto en CVs. Responde SOLO con JSON válido y EXCLUSIVAMENTE en español."},
        {"role": "user", "content": prompt},
    ]

    for model in _analysis_model_chain():
        try:
            response = generate_response(
                messages, model=model, temperature=0.3, max_tokens=1500,
                response_format={"type": "json_object"},
            )
            data = _parse_json_lenient(response)
            return data
        except Exception as e:
            logger.error("Section %s analysis failed with model %s: %s", section, model, e)
            try:
                response = generate_response(
                    messages, model=model, temperature=0.3, max_tokens=1500,
                )
                data = _parse_json_lenient(response)
                return data
            except Exception as e2:
                logger.error("Section %s retry failed: %s", section, e2)
                continue

    return None


# ─── Completeness (determinista, sin IA) ─────────────────────────────────────

def _detail(name: str, score: float, message: str, suggestions: list[str]) -> MetricDetail:
    return MetricDetail(
        name=name,
        score=score,
        max_score=100,
        status="bueno" if score >= 75 else ("mejorable" if score >= 50 else "débil"),
        message=message,
        suggestions=suggestions,
    )


def _deterministic_completeness(cv_data: dict) -> CompletenessMetrics:
    """Completitud objetiva: qué tan lleno está el CV."""
    cv = cv_data.get("cv", {})
    experiences = cv_data.get("experience", [])
    skills = cv_data.get("skills", [])
    education = cv_data.get("education", [])

    details: list[MetricDetail] = []

    personal_fields = [cv.get("name"), cv.get("email"), cv.get("phone"), cv.get("address")]
    filled = sum(1 for f in personal_fields if f and str(f).strip())
    personal_score = round(filled / len(personal_fields) * 100)
    details.append(_detail(
        "Datos personales",
        personal_score,
        f"{filled} de {len(personal_fields)} campos completos",
        [] if personal_score == 100 else ["Completá nombre, email, teléfono y dirección"],
    ))

    about = (cv.get("about") or "").strip()
    about_score = 0 if not about else (100 if len(about) >= 100 else 60)
    details.append(_detail(
        "Resumen profesional",
        about_score,
        "Presente y desarrollado" if about_score == 100 else ("Presente pero corto" if about else "Falta el resumen"),
        [] if about_score == 100 else ["Escribí un 'Sobre mí' de al menos 100 caracteres"],
    ))

    exp_with_desc = sum(1 for e in experiences if (e.get("description") or "").strip())
    exp_score = 0 if not experiences else round(exp_with_desc / len(experiences) * 100)
    details.append(_detail(
        "Experiencia laboral",
        exp_score,
        f"{len(experiences)} experiencia(s), {exp_with_desc} con descripción",
        [] if exp_score == 100 else ["Agregá una descripción a cada experiencia"],
    ))

    skill_score = min(100, len(skills) * 12)
    details.append(_detail(
        "Habilidades",
        skill_score,
        f"{len(skills)} habilidades registradas",
        [] if skill_score >= 80 else ["Agregá más habilidades técnicas y blandas"],
    ))

    edu_score = 100 if education else 0
    details.append(_detail(
        "Formación académica",
        edu_score,
        f"{len(education)} formación(es) registradas",
        [] if edu_score == 100 else ["Agregá tu formación académica"],
    ))

    score = round(sum(d.score for d in details) / len(details), 1) if details else 0
    return CompletenessMetrics(score=score, details=details)


# ─── Main Analysis Function ──────────────────────────────────────────────────

def analyze_cv(user_id: UUID, sections_to_analyze: list[str] | None = None) -> CVAnalysis:
    """
    Analiza el CV con soporte por secciones.

    Args:
        user_id: ID del usuario
        sections_to_analyze: Lista de secciones a re-analizar.
            Si es None, analiza todas.
            Si es lista vacía, usa todo cacheado.
            Ej: ["experience", "skills"] → solo re-analiza esas secciones.
    """
    cv_data = get_user_cv_data(user_id)
    if not cv_data:
        raise ValueError("No se encontró CV para este usuario")

    user_key = str(user_id)
    completeness = _deterministic_completeness(cv_data)

    # Determinar qué secciones analizar
    if sections_to_analyze is None:
        # Análisis completo: todas las secciones
        sections_to_analyze = list(SECTIONS)

    # Fingerprints de cada sección
    section_fps = {s: _section_fingerprint(s, cv_data) for s in SECTIONS}

    # Resultados: usar cache o analizar
    section_results: dict[str, dict] = {}
    sections_analyzed_now: list[str] = []

    for section in SECTIONS:
        fp = section_fps[section]

        if section not in sections_to_analyze:
            # No se pidió re-analizar → usar cache
            cached = _get_cached_section(user_key, section, fp)
            if cached:
                section_results[section] = cached
                logger.info("Section %s: using cache", section)
                continue

        # Verificar cache por fingerprint
        cached = _get_cached_section(user_key, section, fp)
        if cached:
            section_results[section] = cached
            logger.info("Section %s: cache hit (fp match)", section)
            continue

        # Analizar con IA
        logger.info("Section %s: analyzing with AI", section)
        result = _analyze_section(section, cv_data)
        if result:
            section_results[section] = result
            _save_section_cache(user_key, section, fp, result)
            sections_analyzed_now.append(section)
        else:
            # Fallback: score 0
            section_results[section] = {
                "score": 0,
                "details": [],
            }

    # Construir respuesta completa
    return _build_analysis(section_results, completeness, sections_analyzed_now)


def _build_analysis(
    section_results: dict[str, dict],
    completeness: CompletenessMetrics,
    sections_analyzed: list[str],
) -> CVAnalysis:
    """Construye CVAnalysis combinando resultados de secciones."""

    # Mapear secciones a métricas del modelo
    # Contenido = experience + personal (about)
    content_data = _merge_sections(section_results, ["experience", "personal"])
    # ATS = skills + experience (palabras clave)
    ats_data = _merge_sections(section_results, ["skills", "experience"])
    # Estructura = education + skills (organización y variedad)
    structure_data = _merge_sections(section_results, ["education", "skills"])

    content = ContentMetrics(
        score=content_data.get("score", 0),
        details=[MetricDetail(**d) for d in content_data.get("details", [])],
    )
    ats = ATSMetrics(
        score=ats_data.get("score", 0),
        details=[MetricDetail(**d) for d in ats_data.get("details", [])],
    )
    structure = StructureMetrics(
        score=structure_data.get("score", 0),
        details=[MetricDetail(**d) for d in structure_data.get("details", [])],
    )

    overall = round(
        completeness.score * 0.25
        + content.score * 0.35
        + ats.score * 0.20
        + structure.score * 0.20,
        1,
    )

    # Generar top_improvements de las secciones con menor score
    all_details = []
    for section, data in section_results.items():
        for d in data.get("details", []):
            if d.get("score", 100) < 70:
                all_details.append((section, d))

    # Ordenar por score ascendente
    all_details.sort(key=lambda x: x[1].get("score", 0))

    top_improvements = []
    for section, detail in all_details[:3]:
        suggs = detail.get("suggestions", [])
        if suggs:
            top_improvements.append(suggs[0])

    if not top_improvements:
        top_improvements = ["Tu CV está bien optimizado. Mantené las descripciones actualizadas."]

    # Generar summary
    scores = {s: d.get("score", 0) for s, d in section_results.items()}
    if scores:
        best = max(scores, key=lambda k: scores[k])
        worst = min(scores, key=lambda k: scores[k])
    else:
        best = worst = "general"

    summary = f"Mayor fortaleza: {best} ({scores.get(best, 0)}/100). "
    summary += f"Principal área de mejora: {worst} ({scores.get(worst, 0)}/100). "
    if sections_analyzed:
        summary += f"Secciones analizadas: {', '.join(sections_analyzed)}."

    return CVAnalysis(
        overall_score=overall,
        completeness=completeness,
        content=content,
        ats_compatibility=ats,
        structure=structure,
        summary=summary,
        top_improvements=top_improvements,
    )


def _merge_sections(section_results: dict[str, dict], sections: list[str]) -> dict:
    """Combina resultados de múltiples secciones en un solo dict."""
    all_details = []
    scores = []
    for s in sections:
        data = section_results.get(s, {})
        scores.append(data.get("score", 0))
        for d in data.get("details", []):
            all_details.append(d)

    avg_score = round(sum(scores) / len(scores)) if scores else 0
    return {"score": avg_score, "details": all_details}

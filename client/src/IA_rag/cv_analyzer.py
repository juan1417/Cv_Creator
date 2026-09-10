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
# Si uno está rate-limited o caído, se prueba el siguiente.
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

# Cache de análisis por usuario, validada por fingerprint del contenido del CV.
# Si el CV no cambió, se devuelve el análisis cacheado SIN llamar a la IA
# (evita lentitud y rate-limits del modelo free).
_analysis_cache: dict[str, tuple[str, CVAnalysis]] = {}


def _fingerprint(cv_data: dict) -> str:
    payload = json.dumps(cv_data, sort_keys=True, default=str)
    return hashlib.md5(payload.encode("utf-8")).hexdigest()


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
        # strict=False tolera caracteres de control dentro de strings
        return json.loads(raw, strict=False)
    except json.JSONDecodeError:
        # Reparación ligera: elimina comas colgantes antes de } o ]
        repaired = re.sub(r",\s*([}\]])", r"\1", raw)
        return json.loads(repaired, strict=False)


# La IA analiza lo CUALITATIVO (contenido, ATS, estructura) y da recomendaciones
# específicas. La COMPLETITUD es objetiva (campos llenos o no) y se calcula
# determinista en backend para que nunca quede vacía ni mal puntuada.
ANALYSIS_PROMPT = """Eres un experto en recursos humanos y optimización de CVs. Analiza el siguiente CV y devuelve un análisis con scores y recomendaciones específicas.

## ESTRUCTURA DE LA PLANTILLA ( Harvard ):
El CV tiene EXACTAMENTE estas secciones y NO OTRAS:
1. DATOS PERSONALES: nombre, email, teléfono, dirección, portfolio, linkedin
2. RESUMEN PROFESIONAL (about)
3. EXPERIENCIA LABORAL: empresa, cargo, fechas, descripción con logros
4. EDUCACIÓN: institución, título, fechas
5. SKILLS: habilidades técnicas y blandas

IMPORTANTE: NO existen secciones de "proyectos", "certificaciones", "idiomas", "voluntariado" ni ninguna otra. NO sugieras agregar secciones que no existen en la plantilla.

## CV a analizar:
{cv_text}

## Analiza estas 3 dimensiones (0-100 cada una):
1. **Contenido**: calidad de descripciones, logros cuantificables, verbos de acción, métricas
2. **Compatibilidad ATS**: palabras clave técnicas, formato legible por sistemas de tracking
3. **Estructura**: organización, progresión de carrera, variedad y equilibrio de habilidades

## Formato de respuesta (JSON exacto, sin texto adicional):
{{
  "content": {{
    "score": 70,
    "details": [
      {{"name": "Descripciones de experiencia", "score": 65, "max_score": 100, "status": "regular", "message": "Las descripciones son genéricas", "suggestions": ["En tu rol de [X], cambia '[texto actual]' por '[texto con métrica]'"]}}
    ]
  }},
  "ats_compatibility": {{
    "score": 75,
    "details": [
      {{"name": "Palabras clave", "score": 70, "max_score": 100, "status": "mejorable", "message": "Faltan keywords técnicas", "suggestions": ["Incluye [tecnología específica] que aparece en tu experiencia"]}}
    ]
  }},
  "structure": {{
    "score": 72,
    "details": [
      {{"name": "Progresión de carrera", "score": 65, "max_score": 100, "status": "regular", "message": "Poca evolución visible", "suggestions": ["Muestra tu crecimiento de [rol A] a [rol B]"]}}
    ]
  }},
  "summary": "Resumen de 2-3 frases: mayor fortaleza y principal área de mejora del CV concreto.",
  "top_improvements": [
    "Recomendación específica 1 basada en el contenido real del CV",
    "Recomendación específica 2",
    "Recomendación específica 3"
  ]
}}

## Reglas IMPORTANTES:
- NO sugieras agregar secciones que no existen (NO proyectos, NO certificaciones, NO idiomas)
- Solo recomienda mejoras DENTRO de las secciones que ya existen
- Scores REALISTAS basados en la calidad real del contenido
- Recomendaciones ESPECÍFICAS que mencionen el contenido real del CV
- NO des consejos genéricos ("usa verbos de acción"); di EN CAMBIO "En tu experiencia como [X], cambia '[texto actual]' por '[texto mejorado]'"
- Máximo 3 details por categoría y máximo 2 suggestions por detail (sé conciso)
- Escribí TODO el JSON en español; prohibido usar caracteres de otros idiomas
- Dentro de los strings del JSON usá SOLO comillas simples para citar texto
- Responde SOLO con el JSON válido"""


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

    # Datos personales
    personal_fields = [cv.get("name"), cv.get("email"), cv.get("phone"), cv.get("address")]
    filled = sum(1 for f in personal_fields if f and str(f).strip())
    personal_score = round(filled / len(personal_fields) * 100)
    details.append(_detail(
        "Datos personales",
        personal_score,
        f"{filled} de {len(personal_fields)} campos completos",
        [] if personal_score == 100 else ["Completá nombre, email, teléfono y dirección"],
    ))

    # Resumen profesional
    about = (cv.get("about") or "").strip()
    about_score = 0 if not about else (100 if len(about) >= 100 else 60)
    details.append(_detail(
        "Resumen profesional",
        about_score,
        "Presente y desarrollado" if about_score == 100 else ("Presente pero corto" if about else "Falta el resumen"),
        [] if about_score == 100 else ["Escribí un 'Sobre mí' de al menos 100 caracteres"],
    ))

    # Experiencia
    exp_with_desc = sum(1 for e in experiences if (e.get("description") or "").strip())
    exp_score = 0 if not experiences else round(exp_with_desc / len(experiences) * 100)
    details.append(_detail(
        "Experiencia laboral",
        exp_score,
        f"{len(experiences)} experiencia(s), {exp_with_desc} con descripción",
        [] if exp_score == 100 else ["Agregá una descripción a cada experiencia"],
    ))

    # Habilidades
    skill_score = min(100, len(skills) * 12)
    details.append(_detail(
        "Habilidades",
        skill_score,
        f"{len(skills)} habilidades registradas",
        [] if skill_score >= 80 else ["Agregá más habilidades técnicas y blandas"],
    ))

    # Formación
    edu_score = 100 if education else 0
    details.append(_detail(
        "Formación académica",
        edu_score,
        f"{len(education)} formación(es) registradas",
        [] if edu_score == 100 else ["Agregá tu formación académica"],
    ))

    score = round(sum(d.score for d in details) / len(details), 1) if details else 0
    return CompletenessMetrics(score=score, details=details)


def analyze_cv(user_id: UUID) -> CVAnalysis:
    """Analiza el CV: completitud determinista + análisis cualitativo por IA (con cache)."""
    cv_data = get_user_cv_data(user_id)
    if not cv_data:
        raise ValueError("No se encontró CV para este usuario")

    key = str(user_id)
    fp = _fingerprint(cv_data)

    # Cache hit: mismo contenido de CV -> devolver análisis previo sin llamar a la IA
    cached = _analysis_cache.get(key)
    if cached and cached[0] == fp:
        logger.info("Analysis cache hit for user %s", key)
        return cached[1]

    completeness = _deterministic_completeness(cv_data)
    cv_text = get_user_cv_formatted(user_id)
    prompt = ANALYSIS_PROMPT.format(cv_text=cv_text)

    messages = [
        {"role": "system", "content": "Eres un experto en CVs. Responde SOLO con JSON válido y EXCLUSIVAMENTE en español (castellano); nunca uses caracteres de otros idiomas."},
        {"role": "user", "content": prompt},
    ]

    # Reintenta ante errores de conexión O de parseo (los modelos de razonamiento
    # a veces devuelven chain-of-thought en vez de JSON).
    data = None
    last_err: Exception | None = None
    for model in _analysis_model_chain():
        # Intento con JSON forzado
        try:
            response = generate_response(
                messages, model=model, temperature=0.3, max_tokens=3000,
                response_format={"type": "json_object"},
            )
        except Exception as e:
            last_err = e
            logger.error("Model %s connection failed: %s", model, e)
            continue  # rate-limit o caído -> siguiente modelo
        try:
            data = _parse_json_lenient(response)
            logger.info("Analysis OK with model %s", model)
            break
        except (json.JSONDecodeError, ValueError) as e:
            last_err = e
            logger.error("Model %s parse failed: %s", model, e)
        # Parse falló: un intento más sin JSON forzado en el mismo modelo
        try:
            response = generate_response(
                messages, model=model, temperature=0.3, max_tokens=3000
            )
            data = _parse_json_lenient(response)
            logger.info("Analysis OK (sin json_format) with model %s", model)
            break
        except Exception as e:
            last_err = e
            continue

    if data is None:
        return _fallback_analysis(completeness, f"No se pudo generar el análisis: {last_err}")

    result = _build_analysis(data, completeness)
    _analysis_cache[key] = (fp, result)
    return result


def _build_analysis(data: dict, completeness: CompletenessMetrics) -> CVAnalysis:
    """Construye CVAnalysis: IA para lo cualitativo + completitud determinista."""
    content = ContentMetrics(
        score=data.get("content", {}).get("score", 0),
        details=[MetricDetail(**d) for d in data.get("content", {}).get("details", [])],
    )
    ats = ATSMetrics(
        score=data.get("ats_compatibility", {}).get("score", 0),
        details=[MetricDetail(**d) for d in data.get("ats_compatibility", {}).get("details", [])],
    )
    structure = StructureMetrics(
        score=data.get("structure", {}).get("score", 0),
        details=[MetricDetail(**d) for d in data.get("structure", {}).get("details", [])],
    )

    overall = round(
        completeness.score * 0.25
        + content.score * 0.35
        + ats.score * 0.20
        + structure.score * 0.20,
        1,
    )

    return CVAnalysis(
        overall_score=overall,
        completeness=completeness,
        content=content,
        ats_compatibility=ats,
        structure=structure,
        summary=data.get("summary", ""),
        top_improvements=data.get("top_improvements", []),
    )


def _fallback_analysis(completeness: CompletenessMetrics, reason: str) -> CVAnalysis:
    """Si la IA falla, mostramos al menos la completitud objetiva."""
    return CVAnalysis(
        overall_score=round(completeness.score * 0.25, 1),
        completeness=completeness,
        content=ContentMetrics(score=0, details=[]),
        ats_compatibility=ATSMetrics(score=0, details=[]),
        structure=StructureMetrics(score=0, details=[]),
        summary=f"{reason}. Mostramos solo la completitud de tu CV.",
        top_improvements=["Reintentá el análisis en unos segundos"],
    )

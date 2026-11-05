"""Análisis del CV.

Las cuatro métricas (completitud, contenido, ATS y estructura) son
deterministas: salen de `IA_rag/metrics/` y no dependen del LLM. El LLM solo
redacta el resumen cualitativo y las mejoras recomendadas; si falla, hay un
resumen determinista de respaldo. El mismo CV produce siempre los mismos
puntajes.
"""

import json
import logging
import os
import re
from uuid import UUID

from database.get_user_cv import get_user_cv_data
from models.cv_analysis import CVAnalysis, MetricDetail

from .generator import RateLimitError, generate_response
from .metrics import (
    analyze_ats,
    analyze_completeness,
    analyze_content,
    analyze_structure,
    cv_plain_text,
)

logger = logging.getLogger(__name__)

# Modelo específico para el resumen. Si no está definido, usa MODELO.
ANALYSIS_MODEL = os.getenv("MODELO_ANALISIS") or os.getenv("MODELO")

# El cupo gratuito es de 50 pedidos por día. Las cuatro métricas ya son
# deterministas, así que con MODO_ECONOMICO=1 el análisis sigue funcionando y
# no quema un pedido por cada vez que se abre la pantalla.
NARRATIVE_DISABLED = os.getenv("MODO_ECONOMICO", "").strip().lower() in {
    "1", "true", "si", "sí",
}


def _analysis_model_chain() -> list[str]:
    """Cadena de modelos de respaldo (NVIDIA a través de OpenRouter)."""
    chain = [ANALYSIS_MODEL, os.getenv("MODELO")]
    seen: set[str] = set()
    out: list[str] = []
    for model in chain:
        if model and model not in seen:
            seen.add(model)
            out.append(model)
    return out


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
        char = text[i]
        if in_str:
            if esc:
                esc = False
            elif char == "\\":
                esc = True
            elif char == '"':
                in_str = False
        else:
            if char == '"':
                in_str = True
            elif char == "{":
                depth += 1
            elif char == "}":
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


# ─── Deterministic improvements ──────────────────────────────────────────────

IMPROVEMENT_LIMIT = 5
DETAIL_ALERT_RATIO = 0.7


def _detail_ratio(detail: MetricDetail) -> float:
    return detail.score / detail.max_score if detail.max_score else 1.0


def _deterministic_improvements(groups: list[tuple[str, list[MetricDetail]]]) -> list[str]:
    """Sugerencias concretas de los detalles con peor desempeño."""
    ranked: list[tuple[float, str]] = []
    for _label, details in groups:
        for detail in details:
            if _detail_ratio(detail) >= DETAIL_ALERT_RATIO:
                continue
            for suggestion in detail.suggestions:
                ranked.append((_detail_ratio(detail), suggestion))

    ranked.sort(key=lambda item: item[0])
    out: list[str] = []
    for _ratio, suggestion in ranked:
        if suggestion not in out:
            out.append(suggestion)
    return out


def _merge_improvements(deterministic: list[str], from_llm: list[str]) -> list[str]:
    merged: list[str] = []
    for suggestion in from_llm + deterministic:
        text = (suggestion or "").strip()
        if text and text not in merged:
            merged.append(text)
    if not merged:
        merged.append(
            "Tu CV está bien optimizado. Mantené las descripciones actualizadas."
        )
    return merged[:IMPROVEMENT_LIMIT]


def _fallback_summary(
    scores: dict[str, float],
    job_description: str | None,
) -> str:
    """Resumen determinista cuando el LLM no responde."""
    best = max(scores, key=lambda key: scores[key])
    worst = min(scores, key=lambda key: scores[key])
    summary = (
        f"Mayor fortaleza: {best} ({scores[best]:.0f}/100). "
        f"Principal área de mejora: {worst} ({scores[worst]:.0f}/100)."
    )
    if not (job_description or "").strip():
        summary += (
            " Pegá la descripción del puesto para medir la cobertura de palabras clave."
        )
    return summary


# ─── Optional LLM narrative ──────────────────────────────────────────────────

def _metrics_prompt_block(groups: list[tuple[str, list[MetricDetail]]]) -> str:
    lines: list[str] = []
    for label, details in groups:
        total = sum(d.score for d in details)
        max_total = sum(d.max_score for d in details) or 1
        lines.append(f"- {label}: {total:.0f}/{max_total:.0f}")
        for detail in details:
            lines.append(
                f"  - {detail.name}: {detail.score}/{detail.max_score} ({detail.message})"
            )
    return "\n".join(lines)


def _llm_narrative(
    cv_data: dict,
    groups: list[tuple[str, list[MetricDetail]]],
    job_description: str | None,
) -> tuple[str, list[str]] | None:
    """Pide al LLM un resumen y mejoras; no toca los puntajes."""
    if NARRATIVE_DISABLED:
        return None

    cv_text = cv_plain_text(cv_data)
    if not cv_text.strip():
        return None

    vacancy = (
        job_description.strip()
        if (job_description or "").strip()
        else "No se proporcionó descripción del puesto."
    )
    prompt = f"""Analiza este CV usando las métricas ya calculadas. NO cambies los
puntajes: solo redactá un resumen y mejoras concretas.

## Texto del CV
{cv_text}

## Métricas deterministas
{_metrics_prompt_block(groups)}

## Descripción del puesto
{vacancy}

## Responde SOLO con JSON:
{{
  "summary": "2 o 3 frases sobre el estado del CV y su ajuste al puesto",
  "top_improvements": ["mejora concreta 1", "mejora concreta 2", "mejora concreta 3"]
}}

## Reglas:
- Máximo 3 mejoras, accionables y específicas del contenido real
- No inventes experiencia, estudios ni logros que no estén en el CV
- No repitas los puntajes como si fueran texto
- Español neutro, sin regionalismos
- JSON válido, comillas dobles"""

    messages = [
        {
            "role": "system",
            "content": (
                "Sos un experto en CVs y sistemas ATS. Responde SOLO con JSON "
                "válido y exclusivamente en español."
            ),
        },
        {"role": "user", "content": prompt},
    ]

    for model in _analysis_model_chain():
        for use_json_mode in (True, False):
            kwargs = {
                "model": model,
                "temperature": 0.2,
                # Los modelos gratuitos razonan antes de responder y los
                # prompts largos se truncan: 4000 deja margen para el JSON
                # completo. Un solo intento por modo acota la latencia peor
                # caso a dos requests; si falla, el resumen determinista
                # (abajo) responde igual.
                "max_tokens": 4000,
                "max_retries": 0,
            }
            if use_json_mode:
                kwargs["response_format"] = {"type": "json_object"}
            try:
                response = generate_response(messages, **kwargs)
                data = _parse_json_lenient(response)
            except RateLimitError as exc:
                # Sin cupo no tiene sentido gastar otro modo de llamada: el
                # resumen determinista responde igual.
                logger.warning("Narrative sin cupo disponible: %s", exc)
                return None
            except Exception as exc:  # noqa: BLE001 - el fallback es determinista
                logger.warning(
                    "Narrative with model %s failed (json=%s): %s",
                    model,
                    use_json_mode,
                    exc,
                )
                continue

            summary = str(data.get("summary") or "").strip()
            raw_improvements = data.get("top_improvements") or []
            if isinstance(raw_improvements, str):
                raw_improvements = [raw_improvements]
            improvements = [
                str(item).strip()
                for item in raw_improvements
                if str(item).strip()
            ]
            if summary:
                return summary, improvements[:3]

    return None


# ─── Main Analysis Function ──────────────────────────────────────────────────

OVERALL_WEIGHTS = {
    "completeness": 0.25,
    "content": 0.35,
    "ats": 0.20,
    "structure": 0.20,
}


def analyze_cv(user_id: UUID, job_description: str | None = None) -> CVAnalysis:
    """Analiza el CV de forma determinista.

    Args:
        user_id: ID del usuario.
        job_description: descripción opcional del puesto para medir la
            cobertura de palabras clave.
    """
    cv_data = get_user_cv_data(user_id)
    if not cv_data:
        raise ValueError("No se encontró CV para este usuario")

    completeness = analyze_completeness(cv_data)
    content = analyze_content(cv_data)
    ats = analyze_ats(cv_data, job_description)
    structure = analyze_structure(cv_data)

    overall = round(
        completeness.score * OVERALL_WEIGHTS["completeness"]
        + content.score * OVERALL_WEIGHTS["content"]
        + ats.score * OVERALL_WEIGHTS["ats"]
        + structure.score * OVERALL_WEIGHTS["structure"],
        1,
    )

    groups: list[tuple[str, list[MetricDetail]]] = [
        ("Completitud", completeness.details),
        ("Contenido", content.details),
        ("Compatibilidad ATS", ats.details),
        ("Estructura", structure.details),
    ]
    scores = {
        "Completitud": completeness.score,
        "Contenido": content.score,
        "Compatibilidad ATS": ats.score,
        "Estructura": structure.score,
    }

    deterministic = _deterministic_improvements(groups)
    narrative = _llm_narrative(cv_data, groups, job_description)
    if narrative:
        summary, llm_improvements = narrative
    else:
        summary = _fallback_summary(scores, job_description)
        llm_improvements = []

    return CVAnalysis(
        overall_score=overall,
        completeness=completeness,
        content=content,
        ats_compatibility=ats,
        structure=structure,
        summary=summary,
        top_improvements=_merge_improvements(deterministic, llm_improvements),
    )

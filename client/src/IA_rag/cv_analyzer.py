from uuid import UUID

from database.get_user_cv import get_user_cv_data
from models.cv_analysis import (
    CVAnalysis,
    CompletenessMetrics,
    ContentMetrics,
    ATSMetrics,
    StructureMetrics,
    MetricDetail,
)
from .metrics import analyze_completeness, analyze_content, analyze_ats, analyze_structure


def _calculate_overall(
    completeness: CompletenessMetrics,
    content: ContentMetrics,
    ats: ATSMetrics,
    structure: StructureMetrics,
) -> float:
    c = completeness.score / 100 * 25
    t = content.score / 100 * 30
    a = ats.score / 100 * 25
    s = structure.score / 100 * 20
    return round(c + t + a + s, 1)


def _generate_summary(overall_score: float, metrics: dict) -> str:
    if overall_score >= 80:
        level = "excelente"
        emoji = ""
    elif overall_score >= 60:
        level = "bueno"
        emoji = ""
    elif overall_score >= 40:
        level = "regular"
        emoji = ""
    else:
        level = "necesita mejoras significativas"
        emoji = ""

    weakest = min(
        metrics.items(),
        key=lambda m: m[1].score,
    )
    strongest = max(
        metrics.items(),
        key=lambda m: m[1].score,
    )

    return (
        f"Tu CV tiene un nivel {level} con un puntaje de {overall_score}/100. "
        f"Tu mayor fortaleza es {strongest[0]} ({strongest[1].score}/100) "
        f"y tu principal área de mejora es {weakest[0]} ({weakest[1].score}/100)."
    )


def _generate_top_improvements(metrics: dict) -> list[str]:
    improvements: list[str] = []
    for name, metric in sorted(metrics.items(), key=lambda m: m[1].score):
        for detail in metric.details:
            if detail.suggestions:
                improvements.extend(detail.suggestions)
            if len(improvements) >= 5:
                break
        if len(improvements) >= 5:
            break
    return improvements[:5]


def analyze_cv(user_id: UUID) -> CVAnalysis:
    cv_data = get_user_cv_data(user_id)
    if not cv_data:
        raise ValueError("No se encontró CV para este usuario")

    completeness = analyze_completeness(cv_data)
    content = analyze_content(cv_data)
    ats = analyze_ats(cv_data)
    structure = analyze_structure(cv_data)

    overall = _calculate_overall(completeness, content, ats, structure)

    metrics_map = {
        "Completitud": completeness,
        "Contenido": content,
        "Compatibilidad ATS": ats,
        "Estructura": structure,
    }
    summary = _generate_summary(overall, metrics_map)
    top_improvements = _generate_top_improvements(metrics_map)

    return CVAnalysis(
        overall_score=overall,
        completeness=completeness,
        content=content,
        ats_compatibility=ats,
        structure=structure,
        summary=summary,
        top_improvements=top_improvements,
    )

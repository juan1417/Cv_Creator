import re

from ...models.cv_analysis import ContentMetrics, MetricDetail


def _status(score: float) -> str:
    if score >= 80:
        return "excellent"
    if score >= 60:
        return "good"
    if score >= 40:
        return "fair"
    return "poor"


def analyze_content(cv_data: dict) -> ContentMetrics:
    details: list[MetricDetail] = []
    total = 0.0

    about = cv_data["cv"]["about"]
    about_len = len(about.strip())
    about_pts = 25.0
    if about_len == 0:
        about_score = 0.0
        about_msg = "Sin resumen personal"
        about_suggestions = ["Escribe un resumen profesional de 100-300 caracteres"]
    elif about_len < 50:
        about_score = about_pts * 0.3
        about_msg = f"Resumen muy corto ({about_len} caracteres)"
        about_suggestions = ["Amplía tu resumen a 100-300 caracteres para dar más contexto"]
    elif about_len <= 300:
        about_score = about_pts
        about_msg = f"Resumen de longitud óptima ({about_len} caracteres)"
        about_suggestions = []
    elif about_len <= 500:
        about_score = about_pts * 0.7
        about_msg = f"Resumen largo ({about_len} caracteres)"
        about_suggestions = ["Considera reducir a 300 caracteres para mayor impacto"]
    else:
        about_score = about_pts * 0.5
        about_msg = f"Resumen excesivamente largo ({about_len} caracteres)"
        about_suggestions = ["Reduce tu resumen a 100-300 caracteres; los reclutadores prefieren texto conciso"]
    total += about_score
    details.append(MetricDetail(
        name="Longitud del About",
        score=round(about_score, 1),
        max_score=about_pts,
        status=_status(about_score / about_pts * 100),
        message=about_msg,
        suggestions=about_suggestions,
    ))

    experiences = cv_data["experience"]
    exp_pts = 25.0
    if not experiences:
        exp_score = 0.0
        exp_msg = "Sin experiencias para evaluar"
        exp_suggestions = ["Agrega experiencias laborales con descripciones detalladas"]
    else:
        with_desc = [e for e in experiences if e["description"].strip()]
        desc_ratio = len(with_desc) / len(experiences)
        avg_desc_len = (
            sum(len(e["description"]) for e in with_desc) / len(with_desc)
            if with_desc else 0
        )
        exp_score = exp_pts * desc_ratio * (1.0 if avg_desc_len >= 50 else 0.6)
        exp_msg = (
            f"{len(with_desc)}/{len(experiences)} experiencias con descripción "
            f"(promedio {int(avg_desc_len)} caracteres)"
        )
        missing = len(experiences) - len(with_desc)
        exp_suggestions = []
        if missing > 0:
            exp_suggestions.append(f"Agrega descripción a {missing} experiencia(s) sin ella")
        if avg_desc_len < 50 and with_desc:
            exp_suggestions.append("Amplía las descripciones con logros y responsabilidades específicas")
    total += exp_score
    details.append(MetricDetail(
        name="Descripciones de experiencia",
        score=round(exp_score, 1),
        max_score=exp_pts,
        status=_status(exp_score / exp_pts * 100),
        message=exp_msg,
        suggestions=exp_suggestions,
    ))

    all_desc = " ".join(e["description"] for e in experiences)
    action_verbs = [
        "desarrollé", "implementé", "lideré", "creé", "diseñé", "optimicé",
        " gestioné", "coordiné", "establecí", "incremé", "reduje", "mejoré",
        "incremé", "logré", "supervisé", "planifiqué", "ejecuté", "integré",
        "developed", "implemented", "led", "created", "designed", "optimized",
        "managed", "coordinated", "established", "increased", "reduced",
        "improved", "achieved", "supervised", "planned", "executed", "integrated",
        "dirigí", "administré", "construí", "lanzé", "motivé", "formé",
    ]
    all_desc_lower = all_desc.lower()
    found_verbs = [v.strip() for v in action_verbs if v.strip() in all_desc_lower]
    verb_pts = 25.0
    verb_score = verb_pts * min(len(found_verbs) / 5, 1.0)
    total += verb_score
    details.append(MetricDetail(
        name="Uso de verbos de acción",
        score=round(verb_score, 1),
        max_score=verb_pts,
        status=_status(verb_score / verb_pts * 100),
        message=f"{len(found_verbs)} verbo(s) de acción encontrado(s)",
        suggestions=(
            []
            if len(found_verbs) >= 5
            else ["Usa verbos de acción como 'desarrollé', 'implementé', 'lideré' en tus descripciones"]
        ),
    ))

    numbers_pattern = r'\d+[%$]?|\$\d+'
    found_numbers = re.findall(numbers_pattern, all_desc)
    quant_pts = 15.0
    quant_score = quant_pts * min(len(found_numbers) / 3, 1.0)
    total += quant_score
    details.append(MetricDetail(
        name="Logros cuantificables",
        score=round(quant_score, 1),
        max_score=quant_pts,
        status=_status(quant_score / quant_pts * 100),
        message=f"{len(found_numbers)} número(s)/métrica(s) encontrada(s)",
        suggestions=(
            []
            if len(found_numbers) >= 3
            else ["Incluye números y porcentajes en tus logros (ej: 'incrementé ventas un 25%')"]
        ),
    ))

    skills = cv_data["skills"]
    skill_pts = 10.0
    if skills:
        with_level = [s for s in skills if s["level"].strip()]
        level_ratio = len(with_level) / len(skills) if skills else 0
        skill_score = skill_pts * level_ratio
        skill_msg = f"{len(with_level)}/{len(skills)} skills con nivel definido"
        skill_suggestions = (
            []
            if level_ratio >= 1.0
            else ["Asigna un nivel a cada habilidad (ej: 'Avanzado', 'Intermedio')"]
        )
    else:
        skill_score = 0.0
        skill_msg = "Sin habilidades registradas"
        skill_suggestions = ["Agrega habilidades con sus niveles de dominio"]
    total += skill_score
    details.append(MetricDetail(
        name="Skills con nivel definido",
        score=round(skill_score, 1),
        max_score=skill_pts,
        status=_status(skill_score / skill_pts * 100),
        message=skill_msg,
        suggestions=skill_suggestions,
    ))

    return ContentMetrics(score=round(total, 1), details=details)

from datetime import datetime, timezone

from ...models.cv_analysis import StructureMetrics, MetricDetail


def _status(score: float) -> str:
    if score >= 80:
        return "excellent"
    if score >= 60:
        return "good"
    if score >= 40:
        return "fair"
    return "poor"


def analyze_structure(cv_data: dict) -> StructureMetrics:
    details: list[MetricDetail] = []
    total = 0.0
    now = datetime.now(timezone.utc)

    experiences = cv_data["experience"]
    recency_pts = 25.0
    if experiences:
        most_recent = None
        for e in experiences:
            sd = e["start_date"]
            if sd is not None:
                if most_recent is None or sd > most_recent:
                    most_recent = sd
        if most_recent:
            if most_recent.tzinfo is None:
                most_recent = most_recent.replace(tzinfo=timezone.utc)
            years_ago = (now - most_recent).days / 365.25
            if years_ago <= 2:
                recency_score = recency_pts
                recency_msg = f"Experiencia más reciente hace {years_ago:.1f} años"
            elif years_ago <= 5:
                recency_score = recency_pts * 0.6
                recency_msg = f"Experiencia más reciente hace {years_ago:.1f} años (considera actualizar)"
            else:
                recency_score = recency_pts * 0.2
                recency_msg = f"Experiencia más reciente hace {years_ago:.1f} años (muy desactualizado)"
        else:
            recency_score = 0.0
            recency_msg = "No se pudo determinar la fecha más reciente"
    else:
        recency_score = 0.0
        recency_msg = "Sin experiencias para evaluar recencia"
    total += recency_score
    details.append(MetricDetail(
        name="Experiencia reciente",
        score=round(recency_score, 1),
        max_score=recency_pts,
        status=_status(recency_score / recency_pts * 100),
        message=recency_msg,
        suggestions=(
            []
            if recency_score >= recency_pts * 0.6
            else ["Agrega una experiencia más reciente o actualiza las fechas existentes"]
        ),
    ))

    titles = [e["title"].strip() for e in experiences if e["title"].strip()]
    unique_titles = set(titles)
    progression_pts = 25.0
    if len(titles) >= 2:
        progression_score = progression_pts * min(len(unique_titles) / len(titles), 1.0)
        progression_msg = (
            f"{len(unique_titles)} títulos únicos de {len(titles)} experiencias"
        )
        progression_suggestions = (
            []
            if len(unique_titles) / len(titles) >= 0.7
            else ["Varía los títulos para mostrar crecimiento profesional"]
        )
    else:
        progression_score = progression_pts * 0.5 if titles else 0.0
        progression_msg = "Insuficientes experiencias para evaluar progresión"
        progression_suggestions = ["Agrega más experiencias para demostrar progresión de carrera"]
    total += progression_score
    details.append(MetricDetail(
        name="Progresión de títulos",
        score=round(progression_score, 1),
        max_score=progression_pts,
        status=_status(progression_score / progression_pts * 100),
        message=progression_msg,
        suggestions=progression_suggestions,
    ))

    growth_pts = 25.0
    if len(experiences) >= 3:
        growth_score = growth_pts
        growth_msg = f"{len(experiences)} experiencias muestran trayectoria"
    elif len(experiences) >= 1:
        growth_score = growth_pts * 0.5
        growth_msg = f"{len(experiences)} experiencia(s) — agrega más para mostrar crecimiento"
    else:
        growth_score = 0.0
        growth_msg = "Sin experiencias"
    total += growth_score
    details.append(MetricDetail(
        name="Crecimiento profesional",
        score=round(growth_score, 1),
        max_score=growth_pts,
        status=_status(growth_score / growth_pts * 100),
        message=growth_msg,
        suggestions=(
            []
            if len(experiences) >= 3
            else ["Agrega más experiencias para demostrar evolución profesional"]
        ),
    ))

    skills = cv_data["skills"]
    variety_pts = 25.0
    if skills:
        unique_names = set(s["name"].strip().lower() for s in skills if s["name"].strip())
        variety_ratio = len(unique_names) / len(skills) if skills else 0
        variety_score = variety_pts * min(variety_ratio, 1.0)
        variety_msg = f"{len(unique_names)} habilidades únicas de {len(skills)} total"
        variety_suggestions = (
            []
            if variety_ratio >= 0.8
            else ["Evita duplicar habilidades; agrega nuevas para ampliar tu perfil"]
        )
    else:
        variety_score = 0.0
        variety_msg = "Sin skills para evaluar variedad"
        variety_suggestions = ["Agrega habilidades diversas"]
    total += variety_score
    details.append(MetricDetail(
        name="Variedad de skills",
        score=round(variety_score, 1),
        max_score=variety_pts,
        status=_status(variety_score / variety_pts * 100),
        message=variety_msg,
        suggestions=variety_suggestions,
    ))

    return StructureMetrics(score=round(total, 1), details=details)

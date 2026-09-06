import re
from uuid import UUID
from datetime import datetime, timezone

from sqlmodel import Session, select

from ..database.DB import get_engine
from ..models.cv import CV
from ..models.experience import Experience
from ..models.skill import Skills
from ..models.education import Education
from ..models.cv_analysis import (
    CVAnalysis,
    CompletenessMetrics,
    ContentMetrics,
    ATSMetrics,
    StructureMetrics,
    MetricDetail,
)


def _status(score: float) -> str:
    if score >= 80:
        return "excellent"
    if score >= 60:
        return "good"
    if score >= 40:
        return "fair"
    return "poor"


def _get_cv_data(user_id: UUID) -> dict | None:
    engine = get_engine()
    with Session(engine) as session:
        cv = session.exec(select(CV).where(CV.idUser == user_id)).first()
        if not cv:
            return None

        experiences = list(session.exec(
            select(Experience)
            .where(Experience.idUser == user_id)
            .order_by(Experience.start_date.desc())
        ).all())

        skills = list(session.exec(
            select(Skills).where(Skills.idUser == user_id)
        ).all())

        education = list(session.exec(
            select(Education)
            .where(Education.idUser == user_id)
            .order_by(Education.start_date.desc())
        ).all())

        return {
            "cv": {
                "name": cv.name or "",
                "email": cv.email or "",
                "phone": cv.phone or "",
                "address": cv.address or "",
                "about": cv.about or "",
                "porfolio": cv.porfolio or "",
                "linkedin": cv.linkedin or "",
            },
            "experience": [
                {
                    "title": e.title or "",
                    "company": e.company or "",
                    "start_date": e.start_date,
                    "end_date": e.end_date,
                    "description": e.description or "",
                }
                for e in experiences
            ],
            "skills": [
                {"name": s.name or "", "level": s.level or ""}
                for s in skills
            ],
            "education": [
                {
                    "degree": ed.degree or "",
                    "institution": ed.institution or "",
                    "start_date": ed.start_date,
                    "end_date": ed.end_date,
                    "description": ed.description or "",
                }
                for ed in education
            ],
        }


def _analyze_completeness(cv_data: dict) -> CompletenessMetrics:
    cv = cv_data["cv"]
    details: list[MetricDetail] = []
    total = 0.0

    checks = [
        ("Nombre completo", bool(cv["name"].strip()), 10, "name"),
        ("Email de contacto", bool(cv["email"].strip()), 10, "email"),
        ("Teléfono", bool(cv["phone"].strip()), 10, "phone"),
        ("Dirección", bool(cv["address"].strip()), 5, "address"),
        ("Resumen personal (About)", bool(cv["about"].strip()), 15, "about"),
        ("LinkedIn", bool(cv["linkedin"].strip()), 10, "linkedin"),
        ("Portafolio", bool(cv["porfolio"].strip()), 5, "porfolio"),
    ]

    for label, has, pts, field in checks:
        score = pts if has else 0
        total += score
        suggestions = [] if has else [f"Agrega tu {label.lower()} para completar tu perfil"]
        details.append(MetricDetail(
            name=label,
            score=float(score),
            max_score=float(pts),
            status=_status(score / pts * 100 if pts else 100),
            message="Completado" if has else f"Falta {label.lower()}",
            suggestions=suggestions,
        ))

    has_exp = len(cv_data["experience"]) >= 1
    exp_pts = 15
    exp_score = exp_pts if has_exp else 0
    total += exp_score
    details.append(MetricDetail(
        name="Experiencia laboral",
        score=float(exp_score),
        max_score=float(exp_pts),
        status=_status(exp_score / exp_pts * 100 if exp_pts else 100),
        message=f"{len(cv_data['experience'])} experiencia(s) registrada(s)" if has_exp else "Sin experiencias",
        suggestions=[] if has_exp else ["Agrega al menos una experiencia laboral"],
    ))

    skill_count = len(cv_data["skills"])
    has_skills = skill_count >= 3
    skill_pts = 10
    skill_score = skill_pts if has_skills else (skill_pts * skill_count / 3 if skill_count > 0 else 0)
    total += skill_score
    details.append(MetricDetail(
        name="Habilidades (mínimo 3)",
        score=float(skill_score),
        max_score=float(skill_pts),
        status=_status(skill_score / skill_pts * 100 if skill_pts else 100),
        message=f"{skill_count} habilidad(es) registrada(s)",
        suggestions=[] if has_skills else [f"Agrega al menos {3 - skill_count} habilidad(es) más"],
    ))

    has_edu = len(cv_data["education"]) >= 1
    edu_pts = 10
    edu_score = edu_pts if has_edu else 0
    total += edu_score
    details.append(MetricDetail(
        name="Formación académica",
        score=float(edu_score),
        max_score=float(edu_pts),
        status=_status(edu_score / edu_pts * 100 if edu_pts else 100),
        message=f"{len(cv_data['education'])} formación(es) registrada(s)" if has_edu else "Sin formación académica",
        suggestions=[] if has_edu else ["Agrega al menos una formación académica"],
    ))

    return CompletenessMetrics(score=round(total, 1), details=details)


def _analyze_content(cv_data: dict) -> ContentMetrics:
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


def _analyze_ats(cv_data: dict) -> ATSMetrics:
    details: list[MetricDetail] = []
    total = 0.0
    cv = cv_data["cv"]

    contact_fields = [cv["name"], cv["email"], cv["phone"]]
    contact_filled = sum(1 for f in contact_fields if f.strip())
    contact_pts = 25.0
    contact_score = contact_pts * (contact_filled / len(contact_fields))
    total += contact_score
    details.append(MetricDetail(
        name="Información de contacto",
        score=round(contact_score, 1),
        max_score=contact_pts,
        status=_status(contact_score / contact_pts * 100),
        message=f"{contact_filled}/3 campos de contacto completos",
        suggestions=(
            []
            if contact_filled == 3
            else ["Completa nombre, email y teléfono para máxima compatibilidad ATS"]
        ),
    ))

    skills = cv_data["skills"]
    skill_pts = 25.0
    if skills:
        short_skills = [s for s in skills if len(s["name"]) <= 30]
        skill_score = skill_pts * (len(short_skills) / len(skills))
        skill_msg = f"{len(short_skills)}/{len(skills)} skills con formato ATS-amigable"
        skill_suggestions = (
            []
            if len(short_skills) == len(skills)
            else ["Usa nombres cortos y keywords en tus skills (ej: 'Python', 'React', no frases largas)"]
        )
    else:
        skill_score = 0.0
        skill_msg = "Sin skills para evaluar compatibilidad ATS"
        skill_suggestions = ["Agrega habilidades con keywords técnicas relevantes"]
    total += skill_score
    details.append(MetricDetail(
        name="Skills como keywords",
        score=round(skill_score, 1),
        max_score=skill_pts,
        status=_status(skill_score / skill_pts * 100),
        message=skill_msg,
        suggestions=skill_suggestions,
    ))

    experiences = cv_data["experience"]
    exp_pts = 25.0
    if experiences:
        titled = [e for e in experiences if e["title"].strip()]
        title_ratio = len(titled) / len(experiences)
        exp_score = exp_pts * title_ratio
        exp_msg = f"{len(titled)}/{len(experiences)} experiencias con título claro"
        exp_suggestions = (
            []
            if title_ratio >= 1.0
            else ["Asegúrate de que cada experiencia tenga un título claro y específico"]
        )
    else:
        exp_score = 0.0
        exp_msg = "Sin experiencias para evaluar"
        exp_suggestions = ["Agrega experiencias con títulos descriptivos"]
    total += exp_score
    details.append(MetricDetail(
        name="Títulos de experiencia claros",
        score=round(exp_score, 1),
        max_score=exp_pts,
        status=_status(exp_score / exp_pts * 100),
        message=exp_msg,
        suggestions=exp_suggestions,
    ))

    education = cv_data["education"]
    edu_pts = 25.0
    if education:
        edu_score = edu_pts
        edu_msg = f"{len(education)} formación(es) presente(s)"
    else:
        edu_score = 0.0
        edu_msg = "Sin sección de educación"
    total += edu_score
    details.append(MetricDetail(
        name="Sección de educación",
        score=round(edu_score, 1),
        max_score=edu_pts,
        status=_status(edu_score / edu_pts * 100),
        message=edu_msg,
        suggestions=[] if education else ["Agrega tu formación académica para mejorar el puntaje ATS"],
    ))

    return ATSMetrics(score=round(total, 1), details=details)


def _analyze_structure(cv_data: dict) -> StructureMetrics:
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
    cv_data = _get_cv_data(user_id)
    if not cv_data:
        raise ValueError("No se encontró CV para este usuario")

    completeness = _analyze_completeness(cv_data)
    content = _analyze_content(cv_data)
    ats = _analyze_ats(cv_data)
    structure = _analyze_structure(cv_data)

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

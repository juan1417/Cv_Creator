from models.cv_analysis import CompletenessMetrics, MetricDetail


def _status(score: float) -> str:
    if score >= 80:
        return "excellent"
    if score >= 60:
        return "good"
    if score >= 40:
        return "fair"
    return "poor"


def analyze_completeness(cv_data: dict) -> CompletenessMetrics:
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

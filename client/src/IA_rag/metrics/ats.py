from ...models.cv_analysis import ATSMetrics, MetricDetail


def _status(score: float) -> str:
    if score >= 80:
        return "excellent"
    if score >= 60:
        return "good"
    if score >= 40:
        return "fair"
    return "poor"


def analyze_ats(cv_data: dict) -> ATSMetrics:
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

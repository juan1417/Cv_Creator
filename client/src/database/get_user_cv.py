from uuid import UUID
from sqlmodel import Session, select
from .DB import get_engine
from ..models.cv import CV
from ..models.experience import Experience
from ..models.skill import Skills
from ..models.education import Education


def get_user_cv_data(user_id: UUID) -> dict | None:
    """Obtiene todos los datos del CV de un usuario (CV, experiencias, skills, educación)."""
    engine = get_engine()
    with Session(engine) as session:
        cv = session.exec(
            select(CV).where(CV.idUser == user_id)
        ).first()

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


def get_user_cv_formatted(user_id: UUID) -> str:
    """Obtiene el CV formateado como texto para el contexto del RAG."""
    cv_data = get_user_cv_data(user_id)
    
    if not cv_data:
        return "El usuario no tiene un CV registrado."

    lines = []
    cv = cv_data["cv"]

    lines.append("=== DATOS PERSONALES ===")
    lines.append(f"Nombre: {cv['name']}")
    lines.append(f"Email: {cv['email']}")
    lines.append(f"Teléfono: {cv['phone']}")
    lines.append(f"Dirección: {cv['address']}")
    if cv["about"]:
        lines.append(f"Sobre mí: {cv['about']}")
    if cv["porfolio"]:
        lines.append(f"Portafolio: {cv['porfolio']}")
    if cv["linkedin"]:
        lines.append(f"LinkedIn: {cv['linkedin']}")
    lines.append("")

    if cv_data["experience"]:
        lines.append("=== EXPERIENCIA LABORAL ===")
        for e in cv_data["experience"]:
            lines.append(f"## {e['title']} | {e['company']} | {e['start_date']} - {e['end_date']}")
            if e["description"]:
                lines.append(f"Descripción: {e['description']}")
            lines.append("")

    if cv_data["skills"]:
        lines.append("=== HABILIDADES ===")
        for s in cv_data["skills"]:
            lines.append(f"- {s['name']} ({s['level']})")
        lines.append("")

    if cv_data["education"]:
        lines.append("=== FORMACIÓN ACADÉMICA ===")
        for ed in cv_data["education"]:
            lines.append(f"## {ed['degree']} | {ed['institution']} | {ed['start_date']} - {ed['end_date']}")
            if ed["description"]:
                lines.append(f"Descripción: {ed['description']}")
            lines.append("")

    return "\n".join(lines)

from uuid import UUID
from sqlmodel import Session, select
from ..database.DB import get_engine
from ..models.cv import CV
from ..models.experience import Experience
from ..models.skill import Skills
from ..models.education import Education


def get_user_cv(user_id: UUID) -> dict | None:
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
                "name": cv.name,
                "email": cv.email,
                "phone": cv.phone,
                "address": cv.address,
                "about": cv.about,
                "porfolio": cv.porfolio,
                "linkedin": cv.linkedin,
            },
            "experience": [
                {
                    "title": e.title,
                    "company": e.company,
                    "start_date": e.start_date.strftime("%Y-%m-%d") if e.start_date else "N/A",
                    "end_date": e.end_date.strftime("%Y-%m-%d") if e.end_date else "Presente",
                    "description": e.description,
                }
                for e in experiences
            ],
            "skills": [
                {"name": s.name, "level": s.level}
                for s in skills
            ],
            "education": [
                {
                    "degree": ed.degree,
                    "institution": ed.institution,
                    "start_date": ed.start_date.strftime("%Y-%m-%d") if ed.start_date else "N/A",
                    "end_date": ed.end_date.strftime("%Y-%m-%d") if ed.end_date else "Presente",
                    "description": ed.description,
                }
                for ed in education
            ],
        }


def format_cv_as_context(cv_data: dict) -> str:
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

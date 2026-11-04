from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, Field, model_validator


class Experience(BaseModel):
    company: str = ""
    title: str = ""
    start_date: str = ""
    end_date: str | None = None
    description: str = ""


class Education(BaseModel):
    degree: str = ""
    institution: str = ""
    start_date: str = ""
    end_date: str | None = None
    description: str = ""


class Achievement(BaseModel):
    title: str = ""
    description: str = ""


class Language(BaseModel):
    name: str = ""
    level: str = ""


class Skill(BaseModel):
    name: str = ""
    level: str = ""
    type: str = "tech"  # "tech" or "soft"


def _date_text(value: Any) -> str:
    """Normaliza fechas de la base de datos a ISO `YYYY-MM-DD`."""
    if value is None or value == "":
        return ""
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    text = str(value).strip()
    return text[:10] if len(text) >= 10 else text


def _entry_key(company: str, title: str) -> tuple[str, str]:
    """Clave para emparejar una experiencia adaptada con su original."""
    return (company or "").strip().lower(), (title or "").strip().lower()


class CvData(BaseModel):
    """Modelo único de exportación.

    Lo usan los renderers Harvard (DOCX/PDF), la validación post-generación y
    el flujo de Prefect. Se construye desde la base de datos con `from_db`.
    """

    name: str = ""
    email: str = ""
    phone: str = ""
    address: str = ""
    about: str = ""
    linkedin: str = ""
    portfolio: str = ""
    experience: list[Experience] = Field(default_factory=list)
    education: list[Education] = Field(default_factory=list)
    skills: list[Skill] = Field(default_factory=list)
    achievements: list[Achievement] = Field(default_factory=list)
    programs: list[str] = Field(default_factory=list)
    languages: list[Language] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def _coerce_skills(cls, data: Any) -> Any:
        """Acepta `skills: ["Python"]` además de `skills: [{"name": "Python"}]`."""
        if not isinstance(data, dict):
            return data
        skills = data.get("skills")
        if isinstance(skills, list) and any(isinstance(s, str) for s in skills):
            coerced = [{"name": s} if isinstance(s, str) else s for s in skills]
            return {**data, "skills": coerced}
        return data

    @classmethod
    def from_db(cls, cv_data: dict) -> "CvData":
        """Construye el modelo de exportación desde `get_user_cv_data()`."""
        cv = cv_data.get("cv", {})

        experience = [
            Experience(
                company=e.get("company", "") or "",
                title=e.get("title", "") or "",
                start_date=_date_text(e.get("start_date")),
                end_date=_date_text(e.get("end_date")) or None,
                description=e.get("description", "") or "",
            )
            for e in cv_data.get("experience", [])
        ]

        education = [
            Education(
                degree=ed.get("degree", "") or "",
                institution=ed.get("institution", "") or "",
                start_date=_date_text(ed.get("start_date")),
                end_date=_date_text(ed.get("end_date")) or None,
                description=ed.get("description", "") or "",
            )
            for ed in cv_data.get("education", [])
        ]

        skills = [
            Skill(
                name=s.get("name", "") or "",
                level=s.get("level", "") or "",
                type=s.get("type", "tech") or "tech",
            )
            for s in cv_data.get("skills", [])
            if (s.get("name") or "").strip()
        ]

        achievements = [
            Achievement(
                title=a.get("title", "") or "",
                description=a.get("description", "") or "",
            )
            for a in cv_data.get("achievements", [])
            if (a.get("title") or "").strip()
        ]

        programs = [
            p.get("name", "") if isinstance(p, dict) else str(p)
            for p in cv_data.get("programs", [])
        ]
        programs = [p for p in programs if p and p.strip()]

        languages = [
            Language(name=lang.get("name", "") or "", level=lang.get("level", "") or "")
            for lang in cv_data.get("languages", [])
            if (lang.get("name") or "").strip()
        ]

        return cls(
            name=cv.get("name", "") or "",
            email=cv.get("email", "") or "",
            phone=cv.get("phone", "") or "",
            address=cv.get("address", "") or "",
            about=cv.get("about", "") or "",
            linkedin=cv.get("linkedin", "") or "",
            portfolio=cv.get("porfolio", cv.get("portfolio", "")) or "",
            experience=experience,
            education=education,
            skills=skills,
            achievements=achievements,
            programs=programs,
            languages=languages,
        )

    def apply_adaptation(
        self,
        *,
        about: str | None = None,
        experiences: list[dict] | None = None,
        skills: list[dict] | None = None,
    ) -> "CvData":
        """Devuelve una copia con el contenido adaptado a una vacante.

        El CV original no se modifica: la adaptación vive solo en la copia que
        se exporta. Las experiencias se emparejan por empresa + cargo y, si no
        hay coincidencia, por posición; las fechas siempre salen del CV base.
        """
        adapted = self.model_copy(deep=True)

        if about and about.strip():
            adapted.about = about.strip()

        for index, item in enumerate(experiences or []):
            if not isinstance(item, dict):
                continue
            target = None
            key = _entry_key(str(item.get("company") or ""), str(item.get("title") or ""))
            for experience in adapted.experience:
                if _entry_key(experience.company, experience.title) == key:
                    target = experience
                    break
            if target is None and index < len(adapted.experience):
                target = adapted.experience[index]
            description = str(item.get("description") or "").strip()
            if target is not None and description:
                target.description = description

        if skills:
            replacement = [
                Skill(
                    name=str(item.get("name") or "").strip(),
                    level=str(item.get("level") or "").strip(),
                    type=str(item.get("type") or "tech"),
                )
                for item in skills
                if isinstance(item, dict) and str(item.get("name") or "").strip()
            ]
            # Una lista sin ningún nombre válido no debe vaciar las skills:
            # preferimos conservar las originales.
            if replacement:
                adapted.skills = replacement

        return adapted

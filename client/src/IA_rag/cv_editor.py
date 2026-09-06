from uuid import UUID
from datetime import datetime

from sqlmodel import Session, select

from ..database.DB import get_engine
from ..models.cv import CV
from ..models.experience import Experience
from ..models.skill import Skills
from ..models.education import Education


def _get_user_cv(user_id: UUID, session: Session) -> CV | None:
    return session.exec(select(CV).where(CV.idUser == user_id)).first()


def update_cv_field(user_id: UUID, field: str, value: str) -> bool:
    allowed_fields = {"name", "email", "phone", "address", "about", "porfolio", "linkedin"}
    if field not in allowed_fields:
        return False

    engine = get_engine()
    with Session(engine) as session:
        cv = _get_user_cv(user_id, session)
        if not cv:
            return False

        setattr(cv, field, value)
        cv.at_Updated = datetime.utcnow()
        session.add(cv)
        session.commit()
        return True


def add_experience(user_id: UUID, data: dict) -> UUID | None:
    engine = get_engine()
    with Session(engine) as session:
        start_date = _parse_date(data.get("start_date"))
        end_date = _parse_date(data.get("end_date")) if data.get("end_date") else None

        exp = Experience(
            title=data.get("title", ""),
            company=data.get("company", ""),
            start_date=start_date,
            end_date=end_date,
            description=data.get("description", ""),
            idUser=user_id,
        )
        session.add(exp)
        session.commit()
        session.refresh(exp)
        return exp.id


def update_experience(user_id: UUID, experience_id: UUID, data: dict) -> bool:
    engine = get_engine()
    with Session(engine) as session:
        exp = session.exec(
            select(Experience).where(
                Experience.id == experience_id,
                Experience.idUser == user_id,
            )
        ).first()
        if not exp:
            return False

        for field_name in ("title", "company", "description"):
            if field_name in data:
                setattr(exp, field_name, data[field_name])

        if "start_date" in data:
            exp.start_date = _parse_date(data["start_date"])
        if "end_date" in data:
            exp.end_date = _parse_date(data["end_date"]) if data["end_date"] else None

        exp.at_Updated = datetime.utcnow()
        session.add(exp)
        session.commit()
        return True


def delete_experience(user_id: UUID, experience_id: UUID) -> bool:
    engine = get_engine()
    with Session(engine) as session:
        exp = session.exec(
            select(Experience).where(
                Experience.id == experience_id,
                Experience.idUser == user_id,
            )
        ).first()
        if not exp:
            return False

        session.delete(exp)
        session.commit()
        return True


def add_skill(user_id: UUID, name: str, level: str) -> UUID | None:
    engine = get_engine()
    with Session(engine) as session:
        skill = Skills(
            name=name,
            level=level,
            idUser=user_id,
        )
        session.add(skill)
        session.commit()
        session.refresh(skill)
        return skill.id


def delete_skill(user_id: UUID, skill_id: UUID) -> bool:
    engine = get_engine()
    with Session(engine) as session:
        skill = session.exec(
            select(Skills).where(
                Skills.id == skill_id,
                Skills.idUser == user_id,
            )
        ).first()
        if not skill:
            return False

        session.delete(skill)
        session.commit()
        return True


def add_education(user_id: UUID, data: dict) -> UUID | None:
    engine = get_engine()
    with Session(engine) as session:
        start_date = _parse_date(data.get("start_date"))
        end_date = _parse_date(data.get("end_date")) if data.get("end_date") else None

        edu = Education(
            degree=data.get("degree", ""),
            institution=data.get("institution", ""),
            start_date=start_date,
            end_date=end_date,
            description=data.get("description", ""),
            idUser=user_id,
        )
        session.add(edu)
        session.commit()
        session.refresh(edu)
        return edu.id


def delete_education(user_id: UUID, education_id: UUID) -> bool:
    engine = get_engine()
    with Session(engine) as session:
        edu = session.exec(
            select(Education).where(
                Education.id == education_id,
                Education.idUser == user_id,
            )
        ).first()
        if not edu:
            return False

        session.delete(edu)
        session.commit()
        return True


def _parse_date(date_str: str | None) -> datetime | None:
    if not date_str or date_str.lower() == "null":
        return None
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.strptime(date_str.strip(), fmt)
        except ValueError:
            continue
    return None

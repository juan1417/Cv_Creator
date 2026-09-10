from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from sqlmodel import Session, select

from database.DB import get_engine
from models.user import User
from models.cv import CV
from models.experience import Experience
from models.skill import Skills
from models.education import Education
from models.achievement import Achievement
from models.program import Program
from models.language import Language

router = APIRouter(prefix="/api/cv", tags=["cv"])


class CreateCVRequest(BaseModel):
    user_id: UUID
    name: str = ""
    email: str = ""
    phone: str = ""
    address: str = ""
    about: str = ""
    porfolio: str = ""
    linkedin: str | None = None


class UpdateCVRequest(BaseModel):
    name: str | None = None
    email: str | None = None
    phone: str | None = None
    address: str | None = None
    about: str | None = None
    porfolio: str | None = None
    linkedin: str | None = None


class CVResponse(BaseModel):
    id: str
    name: str
    email: str
    phone: str
    address: str
    about: str
    porfolio: str
    linkedin: str | None
    created_at: str
    updated_at: str


class ExperienceResponse(BaseModel):
    id: str
    title: str
    company: str
    start_date: str | None
    end_date: str | None
    description: str


class SkillResponse(BaseModel):
    id: str
    name: str
    level: str
    type: str = "tech"


class EducationResponse(BaseModel):
    id: str
    degree: str
    institution: str
    start_date: str | None
    end_date: str | None
    description: str


class AchievementResponse(BaseModel):
    id: str
    title: str
    description: str


class ProgramResponse(BaseModel):
    id: str
    name: str


class LanguageResponse(BaseModel):
    id: str
    name: str
    level: str


class FullCVResponse(BaseModel):
    cv: CVResponse
    experiences: list[ExperienceResponse]
    skills: list[SkillResponse]
    education: list[EducationResponse]
    achievements: list[AchievementResponse]
    programs: list[ProgramResponse]
    languages: list[LanguageResponse]


def _format_datetime(dt: datetime | None) -> str:
    if dt is None:
        return ""
    return dt.isoformat()


@router.post("", response_model=CVResponse, status_code=201)
async def create_cv(req: CreateCVRequest):
    engine = get_engine()
    with Session(engine) as session:
        user = session.get(User, req.user_id)
        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")

        existing = session.exec(select(CV).where(CV.idUser == req.user_id)).first()
        if existing:
            raise HTTPException(status_code=409, detail="El usuario ya tiene un CV registrado")

        cv = CV(
            name=req.name,
            email=req.email,
            phone=req.phone,
            address=req.address,
            about=req.about,
            porfolio=req.porfolio,
            linkedin=req.linkedin,
            idUser=req.user_id,
        )
        session.add(cv)
        session.commit()
        session.refresh(cv)

        return CVResponse(
            id=str(cv.id),
            name=cv.name or "",
            email=cv.email or "",
            phone=cv.phone or "",
            address=cv.address or "",
            about=cv.about or "",
            porfolio=cv.porfolio or "",
            linkedin=cv.linkedin,
            created_at=_format_datetime(cv.at_Created),
            updated_at=_format_datetime(cv.at_Updated),
        )


@router.get("/{user_id}", response_model=FullCVResponse)
async def get_full_cv(user_id: UUID):
    engine = get_engine()
    with Session(engine) as session:
        cv = session.exec(select(CV).where(CV.idUser == user_id)).first()
        if not cv:
            # Auto-create CV with empty fields
            user = session.get(User, user_id)
            if not user:
                raise HTTPException(status_code=404, detail="Usuario no encontrado")
            cv = CV(
                name=user.username or "",
                email=user.email or "",
                phone="",
                address="",
                about="",
                porfolio="",
                linkedin=None,
                idUser=user_id,
            )
            session.add(cv)
            session.commit()
            session.refresh(cv)

        experiences = list(session.exec(
            select(Experience).where(Experience.idUser == user_id).order_by(Experience.start_date.desc())
        ).all())

        skills = list(session.exec(
            select(Skills).where(Skills.idUser == user_id)
        ).all())

        education = list(session.exec(
            select(Education).where(Education.idUser == user_id).order_by(Education.start_date.desc())
        ).all())

        achievements = list(session.exec(
            select(Achievement).where(Achievement.idUser == user_id)
        ).all())

        programs = list(session.exec(
            select(Program).where(Program.idUser == user_id)
        ).all())

        languages = list(session.exec(
            select(Language).where(Language.idUser == user_id)
        ).all())

        return FullCVResponse(
            cv=CVResponse(
                id=str(cv.id),
                name=cv.name or "",
                email=cv.email or "",
                phone=cv.phone or "",
                address=cv.address or "",
                about=cv.about or "",
                porfolio=cv.porfolio or "",
                linkedin=cv.linkedin,
                created_at=_format_datetime(cv.at_Created),
                updated_at=_format_datetime(cv.at_Updated),
            ),
            experiences=[
                ExperienceResponse(
                    id=str(e.id),
                    title=e.title or "",
                    company=e.company or "",
                    start_date=_format_datetime(e.start_date),
                    end_date=_format_datetime(e.end_date),
                    description=e.description or "",
                )
                for e in experiences
            ],
            skills=[
                SkillResponse(id=str(s.id), name=s.name or "", level=s.level or "", type=s.type or "tech")
                for s in skills
            ],
            education=[
                EducationResponse(
                    id=str(ed.id),
                    degree=ed.degree or "",
                    institution=ed.institution or "",
                    start_date=_format_datetime(ed.start_date),
                    end_date=_format_datetime(ed.end_date),
                    description=ed.description or "",
                )
                for ed in education
            ],
            achievements=[
                AchievementResponse(id=str(a.id), title=a.title or "", description=a.description or "")
                for a in achievements
            ],
            programs=[
                ProgramResponse(id=str(p.id), name=p.name or "")
                for p in programs
            ],
            languages=[
                LanguageResponse(id=str(l.id), name=l.name or "", level=l.level or "")
                for l in languages
            ],
        )


@router.put("/{user_id}", response_model=CVResponse)
async def update_cv(user_id: UUID, req: UpdateCVRequest):
    engine = get_engine()
    with Session(engine) as session:
        cv = session.exec(select(CV).where(CV.idUser == user_id)).first()
        if not cv:
            raise HTTPException(status_code=404, detail="CV no encontrado para este usuario")

        if req.name is not None:
            cv.name = req.name
        if req.email is not None:
            cv.email = req.email
        if req.phone is not None:
            cv.phone = req.phone
        if req.address is not None:
            cv.address = req.address
        if req.about is not None:
            cv.about = req.about
        if req.porfolio is not None:
            cv.porfolio = req.porfolio
        if req.linkedin is not None:
            cv.linkedin = req.linkedin

        cv.at_Updated = datetime.utcnow()
        session.add(cv)
        session.commit()
        session.refresh(cv)

        return CVResponse(
            id=str(cv.id),
            name=cv.name or "",
            email=cv.email or "",
            phone=cv.phone or "",
            address=cv.address or "",
            about=cv.about or "",
            porfolio=cv.porfolio or "",
            linkedin=cv.linkedin,
            created_at=_format_datetime(cv.at_Created),
            updated_at=_format_datetime(cv.at_Updated),
        )


@router.delete("/{user_id}")
async def delete_cv(user_id: UUID):
    engine = get_engine()
    with Session(engine) as session:
        cv = session.exec(select(CV).where(CV.idUser == user_id)).first()
        if not cv:
            raise HTTPException(status_code=404, detail="CV no encontrado para este usuario")

        experiences = session.exec(select(Experience).where(Experience.idUser == user_id)).all()
        for exp in experiences:
            session.delete(exp)

        skills = session.exec(select(Skills).where(Skills.idUser == user_id)).all()
        for skill in skills:
            session.delete(skill)

        education = session.exec(select(Education).where(Education.idUser == user_id)).all()
        for edu in education:
            session.delete(edu)

        achievements = session.exec(select(Achievement).where(Achievement.idUser == user_id)).all()
        for ach in achievements:
            session.delete(ach)

        programs = session.exec(select(Program).where(Program.idUser == user_id)).all()
        for prog in programs:
            session.delete(prog)

        languages = session.exec(select(Language).where(Language.idUser == user_id)).all()
        for lang in languages:
            session.delete(lang)

        session.delete(cv)
        session.commit()

        return {"message": "CV y todos sus datos eliminados correctamente"}

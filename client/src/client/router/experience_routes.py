from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from sqlmodel import Session, select

from ...database.DB import get_engine
from ...models.experience import Experience

router = APIRouter(prefix="/api/experiences", tags=["experiences"])


class ExperienceResponse(BaseModel):
    id: str
    title: str
    company: str
    start_date: str | None
    end_date: str | None
    description: str
    idUser: str
    created_at: str
    updated_at: str


def _format_datetime(dt: datetime | None) -> str:
    if dt is None:
        return ""
    return dt.isoformat()


def _experience_to_response(exp: Experience) -> ExperienceResponse:
    return ExperienceResponse(
        id=str(exp.id),
        title=exp.title or "",
        company=exp.company or "",
        start_date=_format_datetime(exp.start_date),
        end_date=_format_datetime(exp.end_date),
        description=exp.description or "",
        idUser=str(exp.idUser),
        created_at=_format_datetime(exp.at_Created),
        updated_at=_format_datetime(exp.at_Updated),
    )


@router.get("/{user_id}")
async def get_experiences(user_id: UUID):
    engine = get_engine()
    with Session(engine) as session:
        experiences = list(session.exec(
            select(Experience)
            .where(Experience.idUser == user_id)
            .order_by(Experience.start_date.desc())
        ).all())

        return {
            "experiences": [_experience_to_response(e) for e in experiences],
            "total": len(experiences),
        }


@router.get("/detail/{experience_id}", response_model=ExperienceResponse)
async def get_experience(experience_id: UUID):
    engine = get_engine()
    with Session(engine) as session:
        exp = session.get(Experience, experience_id)
        if not exp:
            raise HTTPException(status_code=404, detail="Experiencia no encontrada")
        return _experience_to_response(exp)

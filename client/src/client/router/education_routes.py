from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from sqlmodel import Session, select

from ...database.DB import get_engine
from ...models.education import Education

router = APIRouter(prefix="/api/education", tags=["education"])


class EducationResponse(BaseModel):
    id: str
    degree: str
    institution: str
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


def _education_to_response(edu: Education) -> EducationResponse:
    return EducationResponse(
        id=str(edu.id),
        degree=edu.degree or "",
        institution=edu.institution or "",
        start_date=_format_datetime(edu.start_date),
        end_date=_format_datetime(edu.end_date),
        description=edu.description or "",
        idUser=str(edu.idUser),
        created_at=_format_datetime(edu.at_Created),
        updated_at=_format_datetime(edu.at_Updated),
    )


@router.get("/{user_id}")
async def get_education(user_id: UUID):
    engine = get_engine()
    with Session(engine) as session:
        education = list(session.exec(
            select(Education)
            .where(Education.idUser == user_id)
            .order_by(Education.start_date.desc())
        ).all())

        return {
            "education": [_education_to_response(e) for e in education],
            "total": len(education),
        }


@router.get("/detail/{education_id}", response_model=EducationResponse)
async def get_education_detail(education_id: UUID):
    engine = get_engine()
    with Session(engine) as session:
        edu = session.get(Education, education_id)
        if not edu:
            raise HTTPException(status_code=404, detail="Formación no encontrada")
        return _education_to_response(edu)

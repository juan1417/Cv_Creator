from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from uuid import UUID
from sqlmodel import Session, select

from ...database.DB import get_engine
from ...models.skill import Skills

router = APIRouter(prefix="/api/skills", tags=["skills"])


class SkillResponse(BaseModel):
    id: str
    name: str
    level: str
    idUser: str
    created_at: str
    updated_at: str


def _skill_to_response(skill: Skills) -> SkillResponse:
    return SkillResponse(
        id=str(skill.id),
        name=skill.name or "",
        level=skill.level or "",
        idUser=str(skill.idUser),
        created_at=skill.at_Created.isoformat() if skill.at_Created else "",
        updated_at=skill.at_Updated.isoformat() if skill.at_Updated else "",
    )


@router.get("/{user_id}")
async def get_skills(user_id: UUID):
    engine = get_engine()
    with Session(engine) as session:
        skills = list(session.exec(
            select(Skills).where(Skills.idUser == user_id)
        ).all())

        return {
            "skills": [_skill_to_response(s) for s in skills],
            "total": len(skills),
        }


@router.get("/detail/{skill_id}", response_model=SkillResponse)
async def get_skill(skill_id: UUID):
    engine = get_engine()
    with Session(engine) as session:
        skill = session.get(Skills, skill_id)
        if not skill:
            raise HTTPException(status_code=404, detail="Skill no encontrada")
        return _skill_to_response(skill)

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from uuid import UUID
from sqlmodel import Session, select

from database.DB import get_engine
from models.achievement import Achievement

router = APIRouter(prefix="/api/achievements", tags=["achievements"])


class AchievementResponse(BaseModel):
    id: str
    title: str
    description: str


class AddAchievementRequest(BaseModel):
    user_id: UUID
    title: str
    description: str = ""


class UpdateAchievementRequest(BaseModel):
    title: str | None = None
    description: str | None = None


@router.post("", response_model=AchievementResponse, status_code=201)
async def add_achievement(req: AddAchievementRequest):
    engine = get_engine()
    with Session(engine) as session:
        ach = Achievement(
            title=req.title,
            description=req.description,
            idUser=req.user_id,
        )
        session.add(ach)
        session.commit()
        session.refresh(ach)
        return AchievementResponse(id=str(ach.id), title=ach.title or "", description=ach.description or "")


@router.put("/{achievement_id}", response_model=AchievementResponse)
async def update_achievement(achievement_id: UUID, req: UpdateAchievementRequest):
    engine = get_engine()
    with Session(engine) as session:
        ach = session.get(Achievement, achievement_id)
        if not ach:
            raise HTTPException(status_code=404, detail="Logro no encontrado")
        if req.title is not None:
            ach.title = req.title
        if req.description is not None:
            ach.description = req.description
        session.add(ach)
        session.commit()
        session.refresh(ach)
        return AchievementResponse(id=str(ach.id), title=ach.title or "", description=ach.description or "")


@router.delete("/{achievement_id}")
async def delete_achievement(achievement_id: UUID, user_id: UUID):
    engine = get_engine()
    with Session(engine) as session:
        ach = session.get(Achievement, achievement_id)
        if not ach or ach.idUser != user_id:
            raise HTTPException(status_code=404, detail="Logro no encontrado")
        session.delete(ach)
        session.commit()
        return {"message": "Logro eliminado"}

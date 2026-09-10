from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from uuid import UUID
from sqlmodel import Session, select

from database.DB import get_engine
from models.language import Language

router = APIRouter(prefix="/api/languages", tags=["languages"])


class LanguageResponse(BaseModel):
    id: str
    name: str
    level: str


class AddLanguageRequest(BaseModel):
    user_id: UUID
    name: str
    level: str = ""


class UpdateLanguageRequest(BaseModel):
    name: str | None = None
    level: str | None = None


@router.post("", response_model=LanguageResponse, status_code=201)
async def add_language(req: AddLanguageRequest):
    engine = get_engine()
    with Session(engine) as session:
        lang = Language(name=req.name, level=req.level, idUser=req.user_id)
        session.add(lang)
        session.commit()
        session.refresh(lang)
        return LanguageResponse(id=str(lang.id), name=lang.name or "", level=lang.level or "")


@router.put("/{language_id}", response_model=LanguageResponse)
async def update_language(language_id: UUID, req: UpdateLanguageRequest):
    engine = get_engine()
    with Session(engine) as session:
        lang = session.get(Language, language_id)
        if not lang:
            raise HTTPException(status_code=404, detail="Idioma no encontrado")
        if req.name is not None:
            lang.name = req.name
        if req.level is not None:
            lang.level = req.level
        session.add(lang)
        session.commit()
        session.refresh(lang)
        return LanguageResponse(id=str(lang.id), name=lang.name or "", level=lang.level or "")


@router.delete("/{language_id}")
async def delete_language(language_id: UUID, user_id: UUID):
    engine = get_engine()
    with Session(engine) as session:
        lang = session.get(Language, language_id)
        if not lang or lang.idUser != user_id:
            raise HTTPException(status_code=404, detail="Idioma no encontrado")
        session.delete(lang)
        session.commit()
        return {"message": "Idioma eliminado"}

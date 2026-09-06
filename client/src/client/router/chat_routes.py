from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from sqlmodel import Session, select
import asyncio

from database.DB import get_engine
from models.chat import ChatSession, ChatMessage
from IA_rag.orchestrator import chat as rag_chat
from IA_rag.cv_analyzer import analyze_cv
from IA_rag.cv_editor import (
    update_cv_field,
    add_experience,
    update_experience,
    delete_experience,
    add_skill,
    delete_skill,
    add_education,
    delete_education,
)
from models.cv_analysis import CVAnalysis
from models.cv import CV

router = APIRouter(prefix="/api/chat", tags=["chat"])


# --- Request / Response Models ---

class CreateSessionRequest(BaseModel):
    user_id: UUID
    target_job: str | None = None


class SessionResponse(BaseModel):
    session_id: UUID
    title: str
    target_job: str | None
    created_at: datetime


class SendMessageRequest(BaseModel):
    user_id: UUID
    content: str


class ChatResponse(BaseModel):
    session_id: UUID
    response: str
    target_job: str | None
    action_result: dict | None = None


class SessionListResponse(BaseModel):
    sessions: list[SessionResponse]
    total: int


class MessageResponse(BaseModel):
    id: UUID
    role: str
    content: str
    at_Created: datetime


class MessageListResponse(BaseModel):
    messages: list[MessageResponse]
    total: int


class UpdateCVFieldRequest(BaseModel):
    user_id: UUID
    field: str
    value: str


class AddExperienceRequest(BaseModel):
    user_id: UUID
    title: str
    company: str
    start_date: str | None = None
    end_date: str | None = None
    description: str = ""


class UpdateExperienceRequest(BaseModel):
    user_id: UUID
    title: str | None = None
    company: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    description: str | None = None


class AddSkillRequest(BaseModel):
    user_id: UUID
    name: str
    level: str = ""


class AddEducationRequest(BaseModel):
    user_id: UUID
    degree: str
    institution: str
    start_date: str | None = None
    end_date: str | None = None
    description: str = ""


class EditResultResponse(BaseModel):
    success: bool
    message: str
    new_id: UUID | None = None


# --- Chat Endpoints ---

@router.post("/sessions", response_model=SessionResponse)
async def create_session(req: CreateSessionRequest):
    engine = get_engine()
    with Session(engine) as session:
        chat_session = ChatSession(
            idUser=req.user_id,
            target_job=req.target_job,
        )
        session.add(chat_session)
        session.commit()
        session.refresh(chat_session)

        return SessionResponse(
            session_id=chat_session.id,
            title=chat_session.title,
            target_job=chat_session.target_job,
            created_at=chat_session.at_Created,
        )


@router.post("/sessions/{session_id}/messages", response_model=ChatResponse)
async def send_message(session_id: UUID, req: SendMessageRequest):
    try:
        result = await asyncio.to_thread(
            rag_chat,
            user_id=req.user_id,
            user_message=req.content,
            session_id=session_id,
        )
        return ChatResponse(**result)
    except ValueError as e:
        msg = str(e)
        if "no encontrada" in msg or "CV" in msg:
            raise HTTPException(status_code=400, detail=msg)
        raise HTTPException(status_code=400, detail=msg)
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=502, detail=f"Error del asistente: {str(e)}")


@router.get("/sessions", response_model=SessionListResponse)
async def list_sessions(user_id: UUID):
    engine = get_engine()
    with Session(engine) as session:
        sessions = list(session.exec(
            select(ChatSession)
            .where(ChatSession.idUser == user_id)
            .order_by(ChatSession.at_Updated.desc())
        ).all())

        return SessionListResponse(
            sessions=[
                SessionResponse(
                    session_id=s.id,
                    title=s.title,
                    target_job=s.target_job,
                    created_at=s.at_Created,
                )
                for s in sessions
            ],
            total=len(sessions),
        )


@router.get("/sessions/{session_id}/messages", response_model=MessageListResponse)
async def get_messages(session_id: UUID, user_id: UUID):
    engine = get_engine()
    with Session(engine) as session:
        chat_session = session.exec(
            select(ChatSession).where(
                ChatSession.id == session_id,
                ChatSession.idUser == user_id,
            )
        ).first()

        if not chat_session:
            raise HTTPException(status_code=404, detail="Sesion no encontrada")

        messages = list(session.exec(
            select(ChatMessage)
            .where(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.at_Created.asc())
        ).all())

        return MessageListResponse(
            messages=[
                MessageResponse(
                    id=m.id,
                    role=m.role,
                    content=m.content,
                    at_Created=m.at_Created,
                )
                for m in messages
            ],
            total=len(messages),
        )


@router.delete("/sessions/{session_id}")
async def delete_session(session_id: UUID, user_id: UUID):
    engine = get_engine()
    with Session(engine) as session:
        chat_session = session.exec(
            select(ChatSession).where(
                ChatSession.id == session_id,
                ChatSession.idUser == user_id,
            )
        ).first()

        if not chat_session:
            raise HTTPException(status_code=404, detail="Sesion no encontrada")

        messages = session.exec(
            select(ChatMessage).where(ChatMessage.session_id == session_id)
        ).all()
        for msg in messages:
            session.delete(msg)

        session.delete(chat_session)
        session.commit()

        return {"message": "Sesion eliminada correctamente"}


@router.get("/cv-analysis", response_model=CVAnalysis)
async def cv_analysis(user_id: UUID):
    try:
        result = analyze_cv(user_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al analizar CV: {str(e)}")


# --- CV Edit Endpoints ---

def _verify_cv_ownership(user_id: UUID) -> None:
    engine = get_engine()
    with Session(engine) as session:
        cv = session.exec(select(CV).where(CV.idUser == user_id)).first()
        if not cv:
            raise HTTPException(status_code=404, detail="CV no encontrado para este usuario")


@router.put("/cv/field", response_model=EditResultResponse)
async def edit_cv_field(req: UpdateCVFieldRequest):
    _verify_cv_ownership(req.user_id)

    allowed_fields = {"name", "email", "phone", "address", "about", "porfolio", "linkedin"}
    if req.field not in allowed_fields:
        raise HTTPException(
            status_code=400,
            detail=f"Campo no valido. Campos permitidos: {', '.join(sorted(allowed_fields))}",
        )

    success = update_cv_field(req.user_id, req.field, req.value)
    if not success:
        raise HTTPException(status_code=500, detail="Error al actualizar el campo")

    return EditResultResponse(
        success=True,
        message=f"Campo '{req.field}' actualizado correctamente",
    )


@router.post("/cv/experience", response_model=EditResultResponse)
async def create_experience(req: AddExperienceRequest):
    _verify_cv_ownership(req.user_id)

    data = {
        "title": req.title,
        "company": req.company,
        "start_date": req.start_date,
        "end_date": req.end_date,
        "description": req.description,
    }
    exp_id = add_experience(req.user_id, data)
    if not exp_id:
        raise HTTPException(status_code=500, detail="Error al crear la experiencia")

    return EditResultResponse(
        success=True,
        message="Experiencia creada correctamente",
        new_id=exp_id,
    )


@router.put("/cv/experience/{experience_id}", response_model=EditResultResponse)
async def edit_experience(experience_id: UUID, req: UpdateExperienceRequest):
    _verify_cv_ownership(req.user_id)

    data = {}
    if req.title is not None:
        data["title"] = req.title
    if req.company is not None:
        data["company"] = req.company
    if req.start_date is not None:
        data["start_date"] = req.start_date
    if req.end_date is not None:
        data["end_date"] = req.end_date
    if req.description is not None:
        data["description"] = req.description

    if not data:
        raise HTTPException(status_code=400, detail="No se proporcionaron campos para actualizar")

    success = update_experience(req.user_id, experience_id, data)
    if not success:
        raise HTTPException(status_code=404, detail="Experiencia no encontrada")

    return EditResultResponse(
        success=True,
        message="Experiencia actualizada correctamente",
    )


@router.delete("/cv/experience/{experience_id}", response_model=EditResultResponse)
async def remove_experience(experience_id: UUID, user_id: UUID):
    _verify_cv_ownership(user_id)

    success = delete_experience(user_id, experience_id)
    if not success:
        raise HTTPException(status_code=404, detail="Experiencia no encontrada")

    return EditResultResponse(
        success=True,
        message="Experiencia eliminada correctamente",
    )


@router.post("/cv/skill", response_model=EditResultResponse)
async def create_skill(req: AddSkillRequest):
    _verify_cv_ownership(req.user_id)

    skill_id = add_skill(req.user_id, req.name, req.level)
    if not skill_id:
        raise HTTPException(status_code=500, detail="Error al crear la skill")

    return EditResultResponse(
        success=True,
        message=f"Skill '{req.name}' creada correctamente",
        new_id=skill_id,
    )


@router.delete("/cv/skill/{skill_id}", response_model=EditResultResponse)
async def remove_skill(skill_id: UUID, user_id: UUID):
    _verify_cv_ownership(user_id)

    success = delete_skill(user_id, skill_id)
    if not success:
        raise HTTPException(status_code=404, detail="Skill no encontrada")

    return EditResultResponse(
        success=True,
        message="Skill eliminada correctamente",
    )


@router.post("/cv/education", response_model=EditResultResponse)
async def create_education(req: AddEducationRequest):
    _verify_cv_ownership(req.user_id)

    data = {
        "degree": req.degree,
        "institution": req.institution,
        "start_date": req.start_date,
        "end_date": req.end_date,
        "description": req.description,
    }
    edu_id = add_education(req.user_id, data)
    if not edu_id:
        raise HTTPException(status_code=500, detail="Error al crear la formacion")

    return EditResultResponse(
        success=True,
        message="Formacion creada correctamente",
        new_id=edu_id,
    )


@router.delete("/cv/education/{education_id}", response_model=EditResultResponse)
async def remove_education(education_id: UUID, user_id: UUID):
    _verify_cv_ownership(user_id)

    success = delete_education(user_id, education_id)
    if not success:
        raise HTTPException(status_code=404, detail="Formacion no encontrada")

    return EditResultResponse(
        success=True,
        message="Formacion eliminada correctamente",
    )

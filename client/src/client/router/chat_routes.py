from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from sqlmodel import Session, select

from ...database.DB import get_engine
from ...models.chat import ChatSession, ChatMessage
from ...IA_rag.orchestrator import chat as rag_chat

router = APIRouter(prefix="/api/chat", tags=["chat"])


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
        result = rag_chat(
            user_id=req.user_id,
            user_message=req.content,
            session_id=session_id,
        )
        return ChatResponse(**result)
    except ValueError as e:
        msg = str(e)
        if "no encontrada" in msg:
            raise HTTPException(status_code=404, detail=msg)
        if "CV primero" in msg:
            raise HTTPException(status_code=404, detail=msg)
        raise HTTPException(status_code=400, detail=msg)
    except Exception as e:
        raise HTTPException(status_code=502, detail="Servicio de IA no disponible")


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
            raise HTTPException(status_code=404, detail="Sesión no encontrada")

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
            raise HTTPException(status_code=404, detail="Sesión no encontrada")

        messages = session.exec(
            select(ChatMessage).where(ChatMessage.session_id == session_id)
        ).all()
        for msg in messages:
            session.delete(msg)

        session.delete(chat_session)
        session.commit()

        return {"message": "Sesión eliminada correctamente"}

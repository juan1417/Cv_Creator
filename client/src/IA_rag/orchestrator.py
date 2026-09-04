from uuid import UUID
from datetime import datetime
from sqlmodel import Session, select

from ..database.DB import get_engine
from ..models.chat import ChatSession, ChatMessage
from .retriever import get_user_cv, format_cv_as_context
from .generator import generate_response
from .prompts import SYSTEM_PROMPT

MAX_HISTORY_MESSAGES = 10


def _extract_target_job(user_message: str) -> str | None:
    keywords = [
        "puesto de", "position of", "trabajo de", "postularme a",
        "aplicar a", "apply for", "busco un", "looking for",
        "rol de", "role of", "vacante de",
    ]
    msg_lower = user_message.lower()
    for kw in keywords:
        if kw in msg_lower:
            idx = msg_lower.index(kw) + len(kw)
            rest = user_message[idx:].strip()
            words = rest.split()
            end_words = words[:6] if words else []
            return " ".join(end_words) if end_words else None
    return None


def _build_messages(
    cv_context: str,
    history: list[ChatMessage],
    user_message: str,
) -> list[dict]:
    messages = [
        {"role": "system", "content": f"{SYSTEM_PROMPT}\n\n## CV del Usuario\n{cv_context}"}
    ]
    for msg in history:
        messages.append({"role": msg.role, "content": msg.content})
    messages.append({"role": "user", "content": user_message})
    return messages


def chat(
    user_id: UUID,
    user_message: str,
    session_id: UUID | None = None,
) -> dict:
    engine = get_engine()

    with Session(engine) as session:
        if session_id is not None:
            chat_session = session.exec(
                select(ChatSession).where(
                    ChatSession.id == session_id,
                    ChatSession.idUser == user_id,
                )
            ).first()
            if not chat_session:
                raise ValueError("Sesión no encontrada o no pertenece al usuario")
        else:
            chat_session = ChatSession(idUser=user_id)
            session.add(chat_session)
            session.commit()
            session.refresh(chat_session)

        cv_data = get_user_cv(user_id)
        if not cv_data:
            raise ValueError("Completa tu CV primero para usar el asistente")

        cv_context = format_cv_as_context(cv_data)

        history = list(session.exec(
            select(ChatMessage)
            .where(ChatMessage.session_id == chat_session.id)
            .order_by(ChatMessage.at_Created.desc())
            .limit(MAX_HISTORY_MESSAGES)
        ).all())
        history.reverse()

        llm_messages = _build_messages(cv_context, history, user_message)
        response_text = generate_response(llm_messages)

        user_msg = ChatMessage(
            session_id=chat_session.id,
            role="user",
            content=user_message,
            idUser=user_id,
        )
        session.add(user_msg)

        assistant_msg = ChatMessage(
            session_id=chat_session.id,
            role="assistant",
            content=response_text,
            idUser=user_id,
        )
        session.add(assistant_msg)

        chat_session.at_Updated = datetime.utcnow()
        if not chat_session.target_job:
            detected_job = _extract_target_job(user_message)
            if detected_job:
                chat_session.target_job = detected_job

        if chat_session.title == "Nueva conversación" and len(history) == 0:
            chat_session.title = user_message[:60]

        session.commit()

    return {
        "session_id": str(chat_session.id),
        "response": response_text,
        "target_job": chat_session.target_job,
    }

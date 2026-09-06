from uuid import UUID
from sqlmodel import Session

from database.DB import get_engine
from .retriever import get_user_cv, format_cv_as_context
from .generator import generate_response
from .action_parser import extract_json_action, strip_json_from_response
from .action_executor import execute_action
from .chat_handler import (
    get_or_create_session,
    get_chat_history,
    save_messages,
    update_session_metadata,
    build_messages,
)


def _is_cv_empty(cv_data: dict) -> bool:
    """Detecta si el CV está vacío (recién creado o sin datos)."""
    cv = cv_data.get("cv", {})
    has_name = bool(cv.get("name", "").strip())
    has_email = bool(cv.get("email", "").strip())
    has_experiences = len(cv_data.get("experience", [])) > 0
    has_skills = len(cv_data.get("skills", [])) > 0
    has_education = len(cv_data.get("education", [])) > 0
    return not (has_name or has_email or has_experiences or has_skills or has_education)


def chat(
    user_id: UUID,
    user_message: str,
    session_id: UUID | None = None,
) -> dict:
    engine = get_engine()

    with Session(engine) as db_session:
        chat_session = get_or_create_session(db_session, user_id, session_id)

        cv_data = get_user_cv(user_id)
        if not cv_data:
            raise ValueError("Completa tu CV primero para usar el asistente")

        cv_empty = _is_cv_empty(cv_data)
        cv_context = format_cv_as_context(user_id)

        history = get_chat_history(db_session, chat_session)

        llm_messages = build_messages(cv_context, history, user_message, cv_empty)
        response_text = generate_response(llm_messages)

        action = extract_json_action(response_text)
        action_result = None
        clean_response = response_text

        if action:
            action_result = execute_action(user_id, action)
            clean_response = strip_json_from_response(response_text, action)

            if action.get("action") == "analyze_cv" and action_result:
                score = action_result.get("overall_score", 0)
                summary = action_result.get("summary", "")
                improvements = action_result.get("top_improvements", [])
                analysis_text = f"\n\n---\n**Análisis del CV** (Puntaje: {score}/100)\n\n{summary}\n\n"
                if improvements:
                    analysis_text += "**Mejoras recomendadas:**\n"
                    for imp in improvements:
                        analysis_text += f"- {imp}\n"
                clean_response += analysis_text

        save_messages(db_session, chat_session, user_id, user_message, clean_response)
        update_session_metadata(db_session, chat_session, user_message, history)

        db_session.commit()

        # Capture values before session closes
        session_id_val = chat_session.id
        target_job_val = chat_session.target_job

    return {
        "session_id": str(session_id_val),
        "response": clean_response,
        "target_job": target_job_val,
        "action_result": action_result,
    }

import json
import re
import logging
from uuid import UUID
from datetime import datetime
from sqlmodel import Session, select

from ..database.DB import get_engine
from ..models.chat import ChatSession, ChatMessage
from .retriever import get_user_cv, format_cv_as_context
from .generator import generate_response
from .prompts import SYSTEM_PROMPT
from .cv_analyzer import analyze_cv
from . import cv_editor

logger = logging.getLogger(__name__)

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


def _extract_json_action(text: str) -> dict | None:
    json_patterns = [
        r'```json\s*\n?(.*?)\n?\s*```',
        r'```\s*\n?(.*?)\n?\s*```',
        r'\{[^{}]*"action"\s*:\s*"[^"]*"[^{}]*\}',
    ]

    for pattern in json_patterns:
        matches = re.findall(pattern, text, re.DOTALL)
        for match in matches:
            raw = match.strip()
            try:
                parsed = json.loads(raw)
                if isinstance(parsed, dict) and "action" in parsed:
                    return parsed
            except json.JSONDecodeError:
                continue

    brace_start = text.find("{")
    while brace_start != -1:
        brace_end = text.find("}", brace_start)
        while brace_end != -1:
            candidate = text[brace_start:brace_end + 1]
            try:
                parsed = json.loads(candidate)
                if isinstance(parsed, dict) and "action" in parsed:
                    return parsed
            except json.JSONDecodeError:
                pass
            brace_end = text.find("}", brace_end + 1)
        brace_start = text.find("{", brace_start + 1)

    return None


def _strip_json_from_response(text: str, action: dict) -> str:
    cleaned = text

    for pattern in [
        r'```json\s*\n?.*?\n?\s*```',
        r'```\s*\n?.*?\n?\s*```',
    ]:
        cleaned = re.sub(pattern, "", cleaned, flags=re.DOTALL)

    action_json = json.dumps(action, ensure_ascii=False)
    cleaned = cleaned.replace(action_json, "")

    lines = cleaned.strip().split("\n")
    lines = [l for l in lines if l.strip()]
    return "\n".join(lines).strip()


def _execute_action(user_id: UUID, action: dict) -> dict | None:
    action_type = action.get("action")

    if action_type == "analyze_cv":
        try:
            analysis = analyze_cv(user_id)
            return {
                "type": "analysis",
                "overall_score": analysis.overall_score,
                "summary": analysis.summary,
                "top_improvements": analysis.top_improvements,
            }
        except Exception as e:
            logger.error(f"Error analyzing CV: {e}")
            return {"type": "error", "message": str(e)}

    elif action_type == "update_cv":
        field = action.get("field")
        value = action.get("value")
        if not field or value is None:
            return {"type": "error", "message": "Falta campo o valor para actualizar"}
        success = cv_editor.update_cv_field(user_id, field, value)
        return {
            "type": "edit_result",
            "success": success,
            "message": f"Campo '{field}' actualizado" if success else f"Error al actualizar '{field}'",
        }

    elif action_type == "add_experience":
        data = action.get("data")
        if not data:
            return {"type": "error", "message": "Faltan datos de la experiencia"}
        exp_id = cv_editor.add_experience(user_id, data)
        return {
            "type": "edit_result",
            "success": exp_id is not None,
            "new_id": str(exp_id) if exp_id else None,
            "message": "Experiencia agregada" if exp_id else "Error al agregar experiencia",
        }

    elif action_type == "update_experience":
        exp_id_str = action.get("experience_id")
        data = action.get("data", {})
        if not exp_id_str:
            return {"type": "error", "message": "Falta el ID de la experiencia"}
        try:
            exp_id = UUID(exp_id_str)
        except ValueError:
            return {"type": "error", "message": "ID de experiencia inválido"}
        success = cv_editor.update_experience(user_id, exp_id, data)
        return {
            "type": "edit_result",
            "success": success,
            "message": "Experiencia actualizada" if success else "Experiencia no encontrada",
        }

    elif action_type == "delete_experience":
        exp_id_str = action.get("experience_id")
        if not exp_id_str:
            return {"type": "error", "message": "Falta el ID de la experiencia"}
        try:
            exp_id = UUID(exp_id_str)
        except ValueError:
            return {"type": "error", "message": "ID de experiencia inválido"}
        success = cv_editor.delete_experience(user_id, exp_id)
        return {
            "type": "edit_result",
            "success": success,
            "message": "Experiencia eliminada" if success else "Experiencia no encontrada",
        }

    elif action_type == "add_skill":
        name = action.get("name")
        level = action.get("level")
        if not name:
            return {"type": "error", "message": "Falta el nombre de la skill"}
        skill_id = cv_editor.add_skill(user_id, name, level or "")
        return {
            "type": "edit_result",
            "success": skill_id is not None,
            "new_id": str(skill_id) if skill_id else None,
            "message": f"Skill '{name}' agregada" if skill_id else "Error al agregar skill",
        }

    elif action_type == "delete_skill":
        skill_id_str = action.get("skill_id")
        if not skill_id_str:
            return {"type": "error", "message": "Falta el ID de la skill"}
        try:
            skill_id = UUID(skill_id_str)
        except ValueError:
            return {"type": "error", "message": "ID de skill inválido"}
        success = cv_editor.delete_skill(user_id, skill_id)
        return {
            "type": "edit_result",
            "success": success,
            "message": "Skill eliminada" if success else "Skill no encontrada",
        }

    elif action_type == "add_education":
        data = action.get("data")
        if not data:
            return {"type": "error", "message": "Faltan datos de la formación"}
        edu_id = cv_editor.add_education(user_id, data)
        return {
            "type": "edit_result",
            "success": edu_id is not None,
            "new_id": str(edu_id) if edu_id else None,
            "message": "Formación agregada" if edu_id else "Error al agregar formación",
        }

    elif action_type == "delete_education":
        edu_id_str = action.get("education_id")
        if not edu_id_str:
            return {"type": "error", "message": "Falta el ID de la formación"}
        try:
            edu_id = UUID(edu_id_str)
        except ValueError:
            return {"type": "error", "message": "ID de formación inválido"}
        success = cv_editor.delete_education(user_id, edu_id)
        return {
            "type": "edit_result",
            "success": success,
            "message": "Formación eliminada" if success else "Formación no encontrada",
        }

    return None


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

        action = _extract_json_action(response_text)
        action_result = None
        clean_response = response_text

        if action:
            action_result = _execute_action(user_id, action)
            clean_response = _strip_json_from_response(response_text, action)

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
            content=clean_response,
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
        "response": clean_response,
        "target_job": chat_session.target_job,
        "action_result": action_result,
    }

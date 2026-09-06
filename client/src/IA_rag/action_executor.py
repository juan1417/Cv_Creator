import logging
from uuid import UUID

from .cv_analyzer import analyze_cv
from . import cv_editor

logger = logging.getLogger(__name__)


def execute_action(user_id: UUID, action: dict) -> dict | None:
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

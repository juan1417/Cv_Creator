from uuid import UUID
from database.get_user_cv import get_user_cv_data, get_user_cv_formatted


def get_user_cv(user_id: UUID) -> dict | None:
    """Obtiene los datos del CV de un usuario."""
    return get_user_cv_data(user_id)


def format_cv_as_context(user_id: UUID) -> str:
    """Obtiene el CV formateado como texto para el contexto del RAG."""
    return get_user_cv_formatted(user_id)

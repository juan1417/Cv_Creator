from datetime import datetime

import pytest

from IA_rag.metrics import analyze_ats, analyze_completeness, analyze_content, analyze_structure
from Cv_made import CvData


@pytest.fixture
def cv_data() -> dict:
    """CV de ejemplo con la forma exacta de `get_user_cv_data()`."""
    return {
        "cv": {
            "name": "Ana Pérez",
            "email": "ana@example.com",
            "phone": "+54 11 5555-1234",
            "address": "Buenos Aires, Argentina",
            "about": (
                "Desarrolladora backend con 6 años de experiencia en Python y "
                "PostgreSQL, enfocada en APIs y datos."
            ),
            "porfolio": "github.com/anaperez",
            "linkedin": "linkedin.com/in/anaperez",
        },
        "experience": [
            {
                "title": "Backend Developer",
                "company": "Acme",
                "start_date": datetime(2021, 3, 1),
                "end_date": None,
                "description": (
                    "Desarrollé APIs en Python con FastAPI.\n"
                    "Reduje la latencia 30% y lideré la migración a PostgreSQL."
                ),
            },
            {
                "title": "Junior Developer",
                "company": "Beta",
                "start_date": datetime(2019, 1, 1),
                "end_date": datetime(2021, 2, 1),
                "description": "Implementé servicios internos y automatizaciones ETL.",
            },
        ],
        "skills": [
            {"name": "Python", "level": "Avanzado", "type": "tech"},
            {"name": "PostgreSQL", "level": "Avanzado", "type": "tech"},
            {"name": "Comunicación", "level": "Alto", "type": "soft"},
        ],
        "education": [
            {
                "degree": "Ingeniería en Sistemas",
                "institution": "UNLP",
                "start_date": datetime(2014, 3, 1),
                "end_date": datetime(2019, 12, 1),
                "description": "",
            },
        ],
        "achievements": [{"title": "Hackathon", "description": "Primer puesto entre 40 equipos."}],
        "programs": [{"name": "Git"}, {"name": "Linux"}],
        "languages": [{"name": "Inglés", "level": "B2"}],
    }


@pytest.fixture
def cv() -> CvData:
    """CvData equivalente, listo para renderizar."""
    return CvData(
        name="Ana Pérez",
        email="ana@example.com",
        phone="+54 11 5555-1234",
        address="Buenos Aires, Argentina",
        about="Desarrolladora backend con 6 años de experiencia en Python y PostgreSQL.",
        linkedin="linkedin.com/in/anaperez",
        portfolio="github.com/anaperez",
        experience=[
            {
                "company": "Acme",
                "title": "Backend Developer",
                "start_date": "2021-03-01",
                "description": (
                    "Desarrollé APIs en Python con FastAPI.\n"
                    "Reduje la latencia 30% y lideré la migración a PostgreSQL."
                ),
            },
            {
                "company": "Beta",
                "title": "Junior Developer",
                "start_date": "2019-01-01",
                "end_date": "2021-02-01",
                "description": "Implementé servicios internos y automatizaciones ETL.",
            },
        ],
        education=[
            {
                "degree": "Ingeniería en Sistemas",
                "institution": "UNLP",
                "start_date": "2014-03-01",
                "end_date": "2019-12-01",
            },
        ],
        skills=[
            {"name": "Python", "level": "Avanzado", "type": "tech"},
            {"name": "PostgreSQL", "level": "Avanzado", "type": "tech"},
            {"name": "Comunicación", "level": "Alto", "type": "soft"},
        ],
        achievements=[{"title": "Hackathon", "description": "Primer puesto entre 40 equipos."}],
        programs=["Git", "Linux"],
        languages=[{"name": "Inglés", "level": "B2"}],
    )


__all__ = ["cv_data", "cv", "analyze_ats", "analyze_completeness", "analyze_content", "analyze_structure"]

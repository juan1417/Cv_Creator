from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from client.router import chat_routes
from models.cv_analysis import CVAnalysis


@pytest.fixture
def client(monkeypatch):
    received: dict = {}

    def fake_analyze_cv(user_id, job_description=None):
        received["user_id"] = user_id
        received["job_description"] = job_description
        return CVAnalysis(overall_score=77.0, summary="resumen")

    monkeypatch.setattr(chat_routes, "analyze_cv", fake_analyze_cv)

    app = FastAPI()
    app.include_router(chat_routes.router)
    with TestClient(app) as test_client:
        test_client.received = received
        yield test_client


def test_cv_analysis_accepts_job_description(client):
    user_id = uuid4()
    response = client.post(
        f"/api/chat/cv-analysis?user_id={user_id}",
        json={"job_description": "Backend con Python y PostgreSQL"},
    )
    assert response.status_code == 200
    assert response.json()["overall_score"] == 77.0
    assert client.received["job_description"] == "Backend con Python y PostgreSQL"
    assert client.received["user_id"] == user_id


def test_cv_analysis_without_body_has_no_job_description(client):
    response = client.post(f"/api/chat/cv-analysis?user_id={uuid4()}")
    assert response.status_code == 200
    assert client.received["job_description"] is None


def test_cv_analysis_rejects_legacy_sections_array(client):
    """El shape viejo (array de secciones) ya no es válido: se responde 422
    explícito en vez de ignorar silenciosamente una opción del caller."""
    response = client.post(
        f"/api/chat/cv-analysis?user_id={uuid4()}",
        json=["experience", "skills"],
    )
    assert response.status_code == 422

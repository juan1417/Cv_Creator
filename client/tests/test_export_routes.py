from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from client.router import cv_routes


@pytest.fixture
def client(cv_data, monkeypatch):
    user_id = uuid4()
    monkeypatch.setattr(cv_routes, "get_user_cv_data", lambda uid: cv_data if uid == user_id else None)

    app = FastAPI()
    app.include_router(cv_routes.router)
    with TestClient(app) as test_client:
        test_client.user_id = user_id
        yield test_client


def test_export_pdf_returns_file_and_headers(client, cv_data):
    response = client.post(
        "/api/cv/export",
        json={"user_id": str(client.user_id), "format": "pdf"},
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.content.startswith(b"%PDF")
    assert 'filename="CV_Ana_Perez.pdf"' in response.headers["content-disposition"]
    assert response.headers["x-export-pages"] == "1"
    assert response.headers["x-export-adapted"] == "false"
    assert int(response.headers["x-export-characters"]) > 0
    # El CV base no se toca.
    assert cv_data["cv"]["about"].startswith("Desarrolladora backend")


def test_export_docx_returns_file_and_headers(client):
    response = client.post(
        "/api/cv/export",
        json={"user_id": str(client.user_id), "format": "docx"},
    )
    assert response.status_code == 200
    assert response.content.startswith(b"PK")
    assert 'filename="CV_Ana_Perez.docx"' in response.headers["content-disposition"]


def test_export_adapted_uses_separate_filename(client, cv_data):
    base_about = cv_data["cv"]["about"]
    response = client.post(
        "/api/cv/export",
        json={
            "user_id": str(client.user_id),
            "format": "pdf",
            "adapted_about": "Perfil adaptado para la vacante.",
            "adapted_experiences": [
                {"company": "Acme", "title": "Backend Developer", "description": "Desc adaptada."}
            ],
            "adapted_skills": [{"name": "FastAPI", "level": "Avanzado"}],
        },
    )
    assert response.status_code == 200
    assert 'filename="CV_Ana_Perez_adapted.pdf"' in response.headers["content-disposition"]
    assert response.headers["x-export-adapted"] == "true"
    # La adaptación no se persiste en el CV base.
    assert cv_data["cv"]["about"] == base_about


def test_export_unknown_user_returns_404(client):
    response = client.post(
        "/api/cv/export",
        json={"user_id": str(uuid4()), "format": "pdf"},
    )
    assert response.status_code == 404


def test_export_rejects_unknown_format(client):
    response = client.post(
        "/api/cv/export",
        json={"user_id": str(client.user_id), "format": "xlsx"},
    )
    assert response.status_code == 422


def test_ats_report_returns_deterministic_metrics_and_export_check(client):
    job = "Backend Developer con Python, FastAPI y PostgreSQL."
    payload = {"user_id": str(client.user_id), "job_description": job}

    first = client.post("/api/cv/ats-report", json=payload)
    second = client.post("/api/cv/ats-report", json=payload)

    assert first.status_code == 200
    body = first.json()
    assert 0 <= body["ats"]["score"] <= 100
    assert body["ats"]["keyword_coverage"]["job_description_provided"] is True
    assert "Python" in body["ats"]["keyword_coverage"]["matched"]
    assert body["export_check"]["ok"] is True
    assert body["export_check"]["format"] == "docx"
    # Mismo CV + misma vacante = mismo puntaje.
    assert body["ats"]["score"] == second.json()["ats"]["score"]


def test_ats_report_without_job_description(client):
    response = client.post(
        "/api/cv/ats-report",
        json={"user_id": str(client.user_id)},
    )
    assert response.status_code == 200
    coverage = response.json()["ats"]["keyword_coverage"]
    assert coverage["job_description_provided"] is False

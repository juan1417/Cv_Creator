import Cv_made.cv_models as cv_models
from Cv_made import CvData


def test_apply_adaptation_returns_new_instance(cv):
    adapted = cv.apply_adaptation(about="Nuevo perfil adaptado a la vacante.")
    assert adapted.about == "Nuevo perfil adaptado a la vacante."
    assert cv.about != adapted.about
    assert adapted.name == cv.name


def test_apply_adaptation_matches_experience_by_company_and_title(cv):
    adapted = cv.apply_adaptation(
        experiences=[
            {"company": "acme", "title": "backend developer", "description": "Descripción adaptada."},
            {"company": "Beta", "title": "Junior Developer", "description": "Otra adaptada."},
        ]
    )
    assert adapted.experience[0].description == "Descripción adaptada."
    assert adapted.experience[1].description == "Otra adaptada."
    # Las fechas siempre vienen del CV base.
    assert adapted.experience[0].start_date == cv.experience[0].start_date
    assert cv.experience[0].description != "Descripción adaptada."


def test_apply_adaptation_replaces_skills_only_when_provided(cv):
    with_skills = cv.apply_adaptation(skills=[{"name": "FastAPI", "level": "Avanzado"}])
    assert [s.name for s in with_skills.skills] == ["FastAPI"]
    unchanged = cv.apply_adaptation(about="x")
    assert len(unchanged.skills) == len(cv.skills)


def test_apply_adaptation_ignores_empty_entries(cv):
    adapted = cv.apply_adaptation(
        experiences=[{"company": "Acme", "title": "Backend Developer", "description": "   "}],
        skills=[{"name": "  "}],
    )
    assert adapted.experience[0].description == cv.experience[0].description
    assert adapted.skills == cv.skills


def test_slug_and_filename():
    assert cv_models._entry_key("Acme S.A.", "Dev") == ("acme s.a.", "dev")

    # Sufijo _adapted y nombre sin acentos ni caracteres raros.
    from client.router.cv_routes import _export_filename, _slug

    assert _slug("Ana Pérez") == "Ana_Perez"
    assert _slug("") == "CV"
    assert _export_filename("Ana Pérez", "pdf", adapted=False) == "CV_Ana_Perez.pdf"
    assert _export_filename("Ana Pérez", "docx", adapted=True) == "CV_Ana_Perez_adapted.docx"

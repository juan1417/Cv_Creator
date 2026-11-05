from datetime import date

from IA_rag.metrics import analyze_ats, analyze_completeness, analyze_content, analyze_structure


JOB = (
    "Backend Developer con Python, FastAPI y PostgreSQL. Se valora Docker y "
    "conocimientos de Kubernetes en la nube."
)


def test_ats_score_is_deterministic(cv_data):
    first = analyze_ats(cv_data, JOB)
    second = analyze_ats(cv_data, JOB)
    assert first.score == second.score
    assert first.keyword_coverage.matched == second.keyword_coverage.matched


def test_ats_score_is_bounded_and_summed_from_details(cv_data):
    ats = analyze_ats(cv_data, JOB)
    assert 0.0 <= ats.score <= 100.0
    assert len(ats.details) == 4
    assert all(0.0 <= d.score <= d.max_score for d in ats.details)
    assert ats.keyword_coverage.max_score == 25.0


def test_ats_without_job_description_does_not_penalize(cv_data):
    ats = analyze_ats(cv_data, None)
    assert ats.keyword_coverage.job_description_provided is False
    # Sin vacante no hay keyword block: el score se normaliza sobre 75 puntos.
    keyword_detail = next(d for d in ats.details if "palabras clave" in d.name)
    assert keyword_detail.score == 0.0
    assert 60.0 <= ats.score <= 100.0


def test_ats_contact_requires_valid_email(cv_data):
    cv_data["cv"]["email"] = "sin-arroba"
    ats = analyze_ats(cv_data, JOB)
    contact = next(d for d in ats.details if d.name == "Datos de contacto")
    assert contact.score < contact.max_score
    assert any("email" in suggestion.lower() for suggestion in contact.suggestions)


def test_ats_missing_standard_sections_lowers_score(cv_data):
    cv_data["skills"] = []
    cv_data["cv"]["about"] = ""
    ats = analyze_ats(cv_data, JOB)
    sections = next(d for d in ats.details if d.name == "Secciones estándar")
    assert sections.score < sections.max_score
    assert sections.suggestions


def test_ats_handles_date_objects_instead_of_datetime(cv_data):
    cv_data["experience"][0]["start_date"] = date(2021, 3, 1)
    cv_data["education"][0]["start_date"] = date(2014, 3, 1)
    assert 0.0 <= analyze_ats(cv_data, JOB).score <= 100.0
    assert 0.0 <= analyze_structure(cv_data).score <= 100.0


def test_completeness_content_and_structure_are_deterministic(cv_data):
    runs = [
        (analyze_completeness(cv_data), analyze_content(cv_data), analyze_structure(cv_data)),
        (analyze_completeness(cv_data), analyze_content(cv_data), analyze_structure(cv_data)),
    ]
    first, second = runs
    assert first[0].score == second[0].score
    assert first[1].score == second[1].score
    assert first[2].score == second[2].score
    assert 0.0 <= first[0].score <= 100.0
    assert 0.0 <= first[1].score <= 100.0
    assert 0.0 <= first[2].score <= 100.0

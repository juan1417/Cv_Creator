from IA_rag.metrics.keywords import extract_keywords, keyword_coverage, normalize


def test_normalize_strips_accents_and_case():
    assert normalize("Experiencia EN Python") == "experiencia en python"
    assert normalize("  Áéíóú   ÜÑ  ") == "aeiou un"


def test_extract_keywords_drops_boilerplate():
    text = (
        "Buscamos candidato para puesto de trabajo. Requisitos: Python y Docker "
        "con experiencia de 3 años. Ofrecemos beneficios."
    )
    keywords = [k.lower() for k in extract_keywords(text)]
    assert "python" in keywords
    assert "docker" in keywords
    # Palabras funcionales y boilerplate de ofertas no son keywords.
    assert "buscamos" not in keywords
    assert "puesto" not in keywords
    assert "experiencia" not in keywords
    assert "años" not in keywords


def test_keyword_coverage_reports_matched_and_missing(cv_data):
    job = "Backend Developer con Python, FastAPI, PostgreSQL y Kubernetes"
    coverage = keyword_coverage(
        "\n".join([cv_data["cv"]["name"], cv_data["cv"]["about"]]),
        job,
    )
    assert coverage.job_description_provided is True
    assert "Python" in coverage.matched
    assert "Kubernetes" in coverage.missing
    assert coverage.total == len(coverage.matched) + len(coverage.missing)
    assert 0 <= coverage.score <= coverage.max_score
    assert coverage.score < coverage.max_score


def test_keyword_coverage_without_description_is_empty():
    coverage = keyword_coverage("texto", "")
    assert coverage.job_description_provided is False
    assert coverage.total == 0
    assert coverage.matched == []

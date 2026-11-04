import json
from pathlib import Path
from typing import List

from prefect import flow, task

from .cv_models import Achievement, CvData, Education, Experience, Language
from .harvard import render_docx, render_pdf


def _safe_filename(name: str) -> str:
    cleaned = "".join(
        char if char.isalnum() or char in ("-", "_") else "_" for char in name.strip()
    )
    return cleaned or "cv"


@task
def validate_cv_data(cv_data: CvData) -> CvData:
    if not cv_data.name or not cv_data.name.strip():
        raise ValueError("El campo 'name' es obligatorio")
    if not cv_data.email or not cv_data.email.strip():
        raise ValueError("El campo 'email' es obligatorio")
    return cv_data


@task
def create_cv_docx(cv_data: CvData, output_dir: str = "output") -> Path:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    file_path = output_path / f"{_safe_filename(cv_data.name)}_cv.docx"
    file_path.write_bytes(render_docx(cv_data))
    return file_path


@task
def create_cv_pdf(cv_data: CvData, output_dir: str = "output") -> Path:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    file_path = output_path / f"{_safe_filename(cv_data.name)}_cv.pdf"
    file_path.write_bytes(render_pdf(cv_data))
    return file_path


@flow(name="generate-cvs", log_prints=True)
def generate_cvs(cv_data_list: List[CvData], output_dir: str = "output") -> List[Path]:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    results = []
    for cv_data in cv_data_list:
        validated = validate_cv_data(cv_data)
        docx_path = create_cv_docx(validated, output_dir)
        pdf_path = create_cv_pdf(validated, output_dir)
        results.append(docx_path)
        results.append(pdf_path)
        print(f"Generados: {docx_path.name}, {pdf_path.name}")

    return results


def load_cv_from_json(json_path: str) -> CvData:
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    experience = [
        Experience(
            title=e.get("title", ""),
            company=e.get("company", ""),
            start_date=e.get("start_date", ""),
            end_date=e.get("end_date"),
            description=e.get("description", ""),
        )
        for e in data.get("experience", [])
    ]

    education = [
        Education(
            degree=e.get("degree", ""),
            institution=e.get("institution", ""),
            start_date=e.get("start_date", ""),
            end_date=e.get("end_date"),
            description=e.get("description", ""),
        )
        for e in data.get("education", [])
    ]

    achievements = [
        Achievement(
            title=a.get("title", ""),
            description=a.get("description", ""),
        )
        for a in data.get("achievements", [])
    ]

    languages = [
        Language(
            name=l.get("name", ""),
            level=l.get("level", ""),
        )
        for l in data.get("languages", [])
    ]

    return CvData(
        name=data.get("name", ""),
        email=data.get("email", ""),
        phone=data.get("phone", ""),
        address=data.get("address", ""),
        about=data.get("about", ""),
        experience=experience,
        skills=data.get("skills", []),
        education=education,
        linkedin=data.get("linkedin", ""),
        portfolio=data.get("portfolio", data.get("porfolio", "")),
        achievements=achievements,
        programs=data.get("programs", []),
        languages=languages,
    )


if __name__ == "__main__":
    example_path = Path(__file__).parent / "example_cv.json"
    if example_path.exists():
        cv = load_cv_from_json(str(example_path))
        results = generate_cvs([cv], output_dir="output")
        print("Archivos generados:")
        for r in results:
            print(f"  {r}")

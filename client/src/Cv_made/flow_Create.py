import json
from pathlib import Path
from typing import List

from prefect import flow, task

from .cv_models import CvData, Experience, Education, Achievement, Language
from .docx_creator import create_docx
from .pdf_creator import create_pdf


@task
def validate_cv_data(cv_data: CvData) -> CvData:
    if not cv_data.name or not cv_data.name.strip():
        raise ValueError("El campo 'name' es obligatorio")
    if not cv_data.email or not cv_data.email.strip():
        raise ValueError("El campo 'email' es obligatorio")
    if not cv_data.phone or not cv_data.phone.strip():
        raise ValueError("El campo 'phone' es obligatorio")
    if not cv_data.address or not cv_data.address.strip():
        raise ValueError("El campo 'address' es obligatorio")
    if not cv_data.about or not cv_data.about.strip():
        raise ValueError("El campo 'about' es obligatorio")
    return cv_data


@task
def create_cv_docx(cv_data: CvData, output_dir: str = "output") -> Path:
    return create_docx(cv_data, output_dir)


@task
def create_cv_pdf(cv_data: CvData, output_dir: str = "output") -> Path:
    return create_pdf(cv_data, output_dir)


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
        portfolio=data.get("portfolio", ""),
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
    else:
        print(f"No se encontro {example_path}")

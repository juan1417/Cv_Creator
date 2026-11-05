from sqlmodel import SQLModel
from typing import List


class MetricDetail(SQLModel):
    name: str = ""
    score: float = 0.0
    max_score: float = 0.0
    status: str = ""
    message: str = ""
    suggestions: List[str] = []


class CompletenessMetrics(SQLModel):
    score: float = 0.0
    details: List[MetricDetail] = []


class ContentMetrics(SQLModel):
    score: float = 0.0
    details: List[MetricDetail] = []


class KeywordCoverage(SQLModel):
    """Resultado determinista de comparar las keywords de la vacante con el CV."""

    score: float = 0.0
    max_score: float = 25.0
    matched: List[str] = []
    missing: List[str] = []
    total: int = 0
    job_description_provided: bool = False
    message: str = ""


class ATSMetrics(SQLModel):
    score: float = 0.0
    details: List[MetricDetail] = []
    keyword_coverage: KeywordCoverage | None = None


class StructureMetrics(SQLModel):
    score: float = 0.0
    details: List[MetricDetail] = []


class CVAnalysis(SQLModel):
    overall_score: float = 0.0
    completeness: CompletenessMetrics = CompletenessMetrics()
    content: ContentMetrics = ContentMetrics()
    ats_compatibility: ATSMetrics = ATSMetrics()
    structure: StructureMetrics = StructureMetrics()
    summary: str = ""
    top_improvements: List[str] = []

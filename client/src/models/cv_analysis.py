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


class ATSMetrics(SQLModel):
    score: float = 0.0
    details: List[MetricDetail] = []


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

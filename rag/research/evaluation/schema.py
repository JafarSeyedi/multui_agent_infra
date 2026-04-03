from typing import List, Dict
from pydantic import BaseModel


class Evidence(BaseModel):

    id: str
    text: str
    source: str


class ResearchAnswer(BaseModel):

    query: str
    answer: str
    citations: List[str]
    reasoning_steps: List[str]
    evidences: List[Evidence]


class EvaluationResult(BaseModel):

    retrieval_quality: float
    citation_accuracy: float
    hallucination_rate: float
    reasoning_score: float
    completeness_score: float
    coverage_score: float

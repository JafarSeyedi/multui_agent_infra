from pydantic import BaseModel
from typing import List, Optional

from .common import Evidence, ReasoningTrace
from .learning_objects import (
    LearningObjective, Question, Lesson
)
from agents.orchestration.models import OrchestrationRequest, OrchestrationResult


# -------------------------------------------------------
# Shared evaluation models
# -------------------------------------------------------

class EvaluationCriterion(BaseModel):

    name: str

    description: Optional[str]

    weight: Optional[float]


class EvaluationScore(BaseModel):

    criterion: str

    score: float

    max_score: float = 1.0

    explanation: Optional[str]


class EvaluationIssue(BaseModel):

    issue_type: str

    description: str

    severity: Optional[str]

    evidence: Optional[List[Evidence]]


class AlignmentResult(BaseModel):

    is_aligned: bool

    confidence: Optional[float]

    explanation: Optional[str]


class ConsistencyError(BaseModel):

    description: str

    conflicting_outputs: List[str]

    severity: Optional[str]


class CoverageGap(BaseModel):

    concept_id: str

    concept_name: Optional[str]

    gap_description: Optional[str]

    severity: Optional[str]


# -------------------------------------------------------
# Agent 41 — Question Quality Evaluator
# -------------------------------------------------------

class QuestionQualityEvaluationInput(OrchestrationRequest):

    question: Question

    related_objectives: Optional[List[LearningObjective]]

    evaluation_criteria: Optional[List[EvaluationCriterion]]


class QuestionQualityEvaluationOutput(OrchestrationResult):

    overall_score: float

    scores: List[EvaluationScore]

    issues: Optional[List[EvaluationIssue]]

    suggestions: Optional[List[str]]

    reasoning: Optional[ReasoningTrace]


# -------------------------------------------------------
# Agent 42 — Explanation Quality Evaluator
# -------------------------------------------------------

class ExplanationQualityEvaluationInput(OrchestrationRequest):

    explanation_text: str

    target_concepts: Optional[List[str]]

    evaluation_criteria: Optional[List[EvaluationCriterion]]


class ExplanationQualityEvaluationOutput(OrchestrationResult):

    clarity_score: float

    completeness_score: float

    overall_score: float

    issues: Optional[List[EvaluationIssue]]

    recommendations: Optional[List[str]]

    reasoning: Optional[ReasoningTrace]


# -------------------------------------------------------
# Agent 43 — Pedagogical Alignment Evaluator
# -------------------------------------------------------

class PedagogicalAlignmentInput(OrchestrationRequest):

    content_text: str

    learning_objectives: List[LearningObjective]


class PedagogicalAlignmentOutput(OrchestrationResult):

    alignment_result: AlignmentResult

    issues: Optional[List[EvaluationIssue]]

    reasoning: Optional[ReasoningTrace]


# -------------------------------------------------------
# Agent 44 — Multi-Agent Output Consistency Evaluator
# -------------------------------------------------------

class ConsistencyEvaluationInput(OrchestrationRequest):

    outputs: List[str]

    agent_names: Optional[List[str]]


class ConsistencyEvaluationOutput(OrchestrationResult):

    consistency_score: float

    inconsistencies: Optional[List[ConsistencyError]]

    reasoning: Optional[ReasoningTrace]


# -------------------------------------------------------
# Agent 45 — Curriculum Coverage Evaluator
# -------------------------------------------------------

class CurriculumCoverageInput(OrchestrationRequest):

    lessons: List[Lesson]

    required_objectives: List[LearningObjective]


class CurriculumCoverageOutput(OrchestrationResult):

    coverage_percentage: float

    missing_concepts: Optional[List[CoverageGap]]

    reasoning: Optional[ReasoningTrace]

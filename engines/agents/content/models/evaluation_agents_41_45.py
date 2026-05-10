from pydantic import BaseModel

from ...models import AgentInput
from ...models import AgentOutput
from .common import Evidence
from .common import ReasoningTrace
from .learning_objects import LearningObjective
from .learning_objects import Lesson
from .learning_objects import Question


# -------------------------------------------------------
# Shared evaluation models
# -------------------------------------------------------

class EvaluationCriterion(BaseModel):

    name: str

    description: str | None

    weight: float | None


class EvaluationScore(BaseModel):

    criterion: str

    score: float

    max_score: float = 1.0

    explanation: str | None


class EvaluationIssue(BaseModel):

    issue_type: str

    description: str

    severity: str | None

    evidence: list[Evidence] | None


class AlignmentResult(BaseModel):

    is_aligned: bool

    confidence: float | None

    explanation: str | None


class ConsistencyError(BaseModel):

    description: str

    conflicting_outputs: list[str]

    severity: str | None


class CoverageGap(BaseModel):

    concept_id: str

    concept_name: str | None

    gap_description: str | None

    severity: str | None


# -------------------------------------------------------
# Agent 41 — Question Quality Evaluator
# -------------------------------------------------------

class QuestionQualityEvaluationInput(AgentInput):

    question: Question

    related_objectives: list[LearningObjective] | None

    evaluation_criteria: list[EvaluationCriterion] | None


class QuestionQualityEvaluationOutput(AgentOutput):

    overall_score: float

    scores: list[EvaluationScore]

    issues: list[EvaluationIssue] | None

    suggestions: list[str] | None

    reasoning: ReasoningTrace | None


# -------------------------------------------------------
# Agent 42 — Explanation Quality Evaluator
# -------------------------------------------------------

class ExplanationQualityEvaluationInput(AgentInput):

    explanation_text: str

    target_concepts: list[str] | None

    evaluation_criteria: list[EvaluationCriterion] | None


class ExplanationQualityEvaluationOutput(AgentOutput):

    clarity_score: float

    completeness_score: float

    overall_score: float

    issues: list[EvaluationIssue] | None

    recommendations: list[str] | None

    reasoning: ReasoningTrace | None


# -------------------------------------------------------
# Agent 43 — Pedagogical Alignment Evaluator
# -------------------------------------------------------

class PedagogicalAlignmentInput(AgentInput):

    content_text: str

    learning_objectives: list[LearningObjective]


class PedagogicalAlignmentOutput(AgentOutput):

    alignment_result: AlignmentResult

    issues: list[EvaluationIssue] | None

    reasoning: ReasoningTrace | None


# -------------------------------------------------------
# Agent 44 — Multi-Agent Output Consistency Evaluator
# -------------------------------------------------------

class ConsistencyEvaluationInput(AgentInput):

    outputs: list[str]

    agent_names: list[str] | None


class ConsistencyEvaluationOutput(AgentOutput):

    consistency_score: float

    inconsistencies: list[ConsistencyError] | None

    reasoning: ReasoningTrace | None


# -------------------------------------------------------
# Agent 45 — Curriculum Coverage Evaluator
# -------------------------------------------------------

class CurriculumCoverageInput(AgentInput):

    lessons: list[Lesson]

    required_objectives: list[LearningObjective]


class CurriculumCoverageOutput(AgentOutput):

    coverage_percentage: float

    missing_concepts: list[CoverageGap] | None

    reasoning: ReasoningTrace | None

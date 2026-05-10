from datetime import datetime
from typing import Literal

from pydantic import BaseModel
from pydantic import Field

from ...models import AgentInput
from ...models import AgentOutput


# --------------------------------------------------
# Shared Types
# --------------------------------------------------

QuestionType = Literal[
    "mcq",
    "short_answer",
    "long_answer",
    "true_false",
    "fill_in_blank"
]

DifficultyLevel = Literal[1, 2, 3, 4, 5]


# --------------------------------------------------
# Agent 21
# Quiz Builder
# --------------------------------------------------

class QuizBuilderInput(AgentInput):

    topic: str

    lesson_context: str

    num_questions: int = Field(
        description="Number of questions to generate"
    )

    question_types: list[QuestionType] | None = None

    difficulty_distribution: dict[DifficultyLevel, int] | None = None

    learning_objectives: list[str] | None = None

    subject: str | None = None


class QuizQuestion(BaseModel):

    question_id: str

    question_text: str

    question_type: QuestionType

    options: list[str] | None = None

    correct_answer: str

    difficulty: DifficultyLevel

    explanation: str | None = None


class QuizBuilderOutput(AgentOutput):

    quiz_title: str

    questions: list[QuizQuestion]

    estimated_time_minutes: int | None

    created_at: datetime


# --------------------------------------------------
# Agent 22
# Answer Evaluator
# --------------------------------------------------

class AnswerEvaluationInput(AgentInput):

    question_id: str | None

    question_text: str

    student_answer: str

    correct_answer: str | None

    rubric: dict | None

    subject: str | None


class AnswerEvaluationOutput(AgentOutput):

    score: float

    max_score: float

    correctness: bool

    evaluation_reason: str

    evaluated_at: datetime


# --------------------------------------------------
# Agent 23
# Feedback Generator
# --------------------------------------------------

class FeedbackGenerationInput(AgentInput):

    question_text: str

    student_answer: str

    correct_answer: str | None

    evaluation_score: float

    max_score: float | None

    student_profile: dict | None


class FeedbackGenerationOutput(AgentOutput):

    feedback_text: str

    encouragement: str | None

    suggested_review_topics: list[str] | None

    generated_at: datetime


# --------------------------------------------------
# Agent 24
# Rubric Generator
# --------------------------------------------------

class RubricGenerationInput(AgentInput):

    assignment_description: str

    grading_criteria: list[str] | None

    max_score: int


class RubricCriterion(BaseModel):

    criterion: str

    description: str

    max_points: int


class RubricGenerationOutput(AgentOutput):

    rubric: list[RubricCriterion]

    generated_at: datetime


# --------------------------------------------------
# Agent 25
# Misconception Analyzer
# --------------------------------------------------

class MisconceptionAnalysisInput(AgentInput):

    student_answers: list[str]

    question_set: list[str]

    topic: str


class MisconceptionPattern(BaseModel):

    misconception: str

    frequency: int

    suggested_intervention: str


class MisconceptionAnalysisOutput(AgentOutput):

    detected_patterns: list[MisconceptionPattern]

    analyzed_at: datetime


# --------------------------------------------------
# Agent 26
# Skill Mastery Estimator
# --------------------------------------------------

class SkillMasteryInput(AgentInput):

    student_id: str

    skill: str

    past_scores: list[float]

    attempt_history: list[dict] | None


class SkillMasteryOutput(AgentOutput):

    mastery_probability: float

    mastery_level: Literal[
        "not_started",
        "developing",
        "proficient",
        "mastered"
    ]

    recommended_next_action: str

    estimated_at: datetime


# --------------------------------------------------
# Agent 27
# Learning Gap Detector
# --------------------------------------------------

class LearningGapInput(AgentInput):

    student_performance: dict

    curriculum_skills: list[str]


class LearningGap(BaseModel):

    skill: str

    gap_severity: float

    recommended_lessons: list[str]


class LearningGapOutput(AgentOutput):

    gaps: list[LearningGap]

    analyzed_at: datetime


# --------------------------------------------------
# Agent 28
# Knowledge Graph Updater
# --------------------------------------------------

class KnowledgeGraphUpdateInput(AgentInput):

    concept: str

    related_concepts: list[str]

    source: str | None


class KnowledgeGraphUpdateOutput(AgentOutput):

    nodes_added: list[str]

    edges_added: list[dict]

    update_summary: str

    updated_at: datetime


# --------------------------------------------------
# Agent 29
# Concept Difficulty Estimator
# --------------------------------------------------

class ConceptDifficultyInput(AgentInput):

    concept: str

    student_attempts: list[dict] | None


class ConceptDifficultyOutput(AgentOutput):

    estimated_difficulty: float

    confidence_score: float

    evaluated_at: datetime


# --------------------------------------------------
# Agent 30
# Curriculum Mapper
# --------------------------------------------------

class CurriculumMappingInput(AgentInput):

    lesson_content: str

    curriculum_standard: str


class CurriculumMapping(BaseModel):

    standard_id: str

    description: str


class CurriculumMappingOutput(AgentOutput):

    mapped_standards: list[CurriculumMapping]

    mapped_at: datetime

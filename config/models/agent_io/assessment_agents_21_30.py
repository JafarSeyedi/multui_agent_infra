from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Literal
from datetime import datetime


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

class QuizBuilderInput(OrchestrationRequest):

    topic: str

    lesson_context: str

    num_questions: int = Field(
        description="Number of questions to generate"
    )

    question_types: Optional[List[QuestionType]] = None

    difficulty_distribution: Optional[Dict[DifficultyLevel, int]] = None

    learning_objectives: Optional[List[str]] = None

    subject: Optional[str] = None


class QuizQuestion(BaseModel):

    question_id: str

    question_text: str

    question_type: QuestionType

    options: Optional[List[str]] = None

    correct_answer: str

    difficulty: DifficultyLevel

    explanation: Optional[str] = None


class QuizBuilderOutput(OrchestrationResult):

    quiz_title: str

    questions: List[QuizQuestion]

    estimated_time_minutes: Optional[int]

    created_at: datetime


# --------------------------------------------------
# Agent 22
# Answer Evaluator
# --------------------------------------------------

class AnswerEvaluationInput(OrchestrationRequest):

    question_id: Optional[str]

    question_text: str

    student_answer: str

    correct_answer: Optional[str]

    rubric: Optional[Dict]

    subject: Optional[str]


class AnswerEvaluationOutput(OrchestrationResult):

    score: float

    max_score: float

    correctness: bool

    evaluation_reason: str

    evaluated_at: datetime


# --------------------------------------------------
# Agent 23
# Feedback Generator
# --------------------------------------------------

class FeedbackGenerationInput(OrchestrationRequest):

    question_text: str

    student_answer: str

    correct_answer: Optional[str]

    evaluation_score: float

    max_score: Optional[float]

    student_profile: Optional[Dict]


class FeedbackGenerationOutput(OrchestrationResult):

    feedback_text: str

    encouragement: Optional[str]

    suggested_review_topics: Optional[List[str]]

    generated_at: datetime


# --------------------------------------------------
# Agent 24
# Rubric Generator
# --------------------------------------------------

class RubricGenerationInput(OrchestrationRequest):

    assignment_description: str

    grading_criteria: Optional[List[str]]

    max_score: int


class RubricCriterion(BaseModel):

    criterion: str

    description: str

    max_points: int


class RubricGenerationOutput(OrchestrationResult):

    rubric: List[RubricCriterion]

    generated_at: datetime


# --------------------------------------------------
# Agent 25
# Misconception Analyzer
# --------------------------------------------------

class MisconceptionAnalysisInput(OrchestrationRequest):

    student_answers: List[str]

    question_set: List[str]

    topic: str


class MisconceptionPattern(BaseModel):

    misconception: str

    frequency: int

    suggested_intervention: str


class MisconceptionAnalysisOutput(OrchestrationResult):

    detected_patterns: List[MisconceptionPattern]

    analyzed_at: datetime


# --------------------------------------------------
# Agent 26
# Skill Mastery Estimator
# --------------------------------------------------

class SkillMasteryInput(OrchestrationRequest):

    student_id: str

    skill: str

    past_scores: List[float]

    attempt_history: Optional[List[Dict]]


class SkillMasteryOutput(OrchestrationResult):

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

class LearningGapInput(OrchestrationRequest):

    student_performance: Dict

    curriculum_skills: List[str]


class LearningGap(BaseModel):

    skill: str

    gap_severity: float

    recommended_lessons: List[str]


class LearningGapOutput(OrchestrationResult):

    gaps: List[LearningGap]

    analyzed_at: datetime


# --------------------------------------------------
# Agent 28
# Knowledge Graph Updater
# --------------------------------------------------

class KnowledgeGraphUpdateInput(OrchestrationRequest):

    concept: str

    related_concepts: List[str]

    source: Optional[str]


class KnowledgeGraphUpdateOutput(OrchestrationResult):

    nodes_added: List[str]

    edges_added: List[Dict]

    update_summary: str

    updated_at: datetime


# --------------------------------------------------
# Agent 29
# Concept Difficulty Estimator
# --------------------------------------------------

class ConceptDifficultyInput(OrchestrationRequest):

    concept: str

    student_attempts: Optional[List[Dict]]


class ConceptDifficultyOutput(OrchestrationResult):

    estimated_difficulty: float

    confidence_score: float

    evaluated_at: datetime


# --------------------------------------------------
# Agent 30
# Curriculum Mapper
# --------------------------------------------------

class CurriculumMappingInput(OrchestrationRequest):

    lesson_content: str

    curriculum_standard: str


class CurriculumMapping(BaseModel):

    standard_id: str

    description: str


class CurriculumMappingOutput(OrchestrationResult):

    mapped_standards: List[CurriculumMapping]

    mapped_at: datetime

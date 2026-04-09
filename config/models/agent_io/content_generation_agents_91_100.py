from typing import List, Optional
from .common import ConfidenceScore, Recommendation
from .learning_objects import Lesson, LearningObjective
from agents.orchestration.models import OrchestrationRequest, OrchestrationResult

# -------------------------------------------------
# Agent 91 — Example Generator
# -------------------------------------------------

class ExampleGeneratorInput(OrchestrationRequest):
    concept: str
    difficulty_level: Optional[str]


class ExampleGeneratorOutput(OrchestrationResult):
    examples: List[str]
    confidence: Optional[ConfidenceScore]


# -------------------------------------------------
# Agent 92 — Exercise Creator
# -------------------------------------------------

class ExerciseCreatorInput(OrchestrationRequest):
    concept: str
    learning_objective: Optional[LearningObjective]
    difficulty: Optional[str]


class ExerciseCreatorOutput(OrchestrationResult):
    exercises: List[str]
    recommendations: Optional[List[Recommendation]]


# -------------------------------------------------
# Agent 93 — StoryBasedLessonCreator
# -------------------------------------------------

class StoryLessonCreatorInput(OrchestrationRequest):
    topic: str
    target_age: int


class StoryLessonCreatorOutput(OrchestrationResult):
    story_text: str
    moral_message: Optional[str]


# -------------------------------------------------
# Agent 94 — ConceptExplanationGenerator
# -------------------------------------------------

class ConceptExplanationInput(OrchestrationRequest):
    concept: str
    student_level: Optional[str]


class ConceptExplanationOutput(OrchestrationResult):
    explanation: str
    confidence: Optional[ConfidenceScore]


# -------------------------------------------------
# Agent 95 — PracticeQuestionGenerator
# -------------------------------------------------

class PracticeQuestionGeneratorInput(OrchestrationRequest):
    lesson: Lesson
    question_count: int = 5


class PracticeQuestionGeneratorOutput(OrchestrationResult):
    questions: List[str]


# -------------------------------------------------
# Agent 96 — AdaptiveQuestionGenerator
# -------------------------------------------------

class AdaptiveQuestionGeneratorInput(OrchestrationRequest):
    recent_performance_score: float
    target_concept: str


class AdaptiveQuestionGeneratorOutput(OrchestrationResult):
    generated_questions: List[str]
    difficulty_level: str


# -------------------------------------------------
# Agent 97 — ExplanationRewriter
# -------------------------------------------------

class ExplanationRewriterInput(OrchestrationRequest):
    original_explanation: str
    target_level: str


class ExplanationRewriterOutput(OrchestrationResult):
    rewritten_explanation: str


# -------------------------------------------------
# Agent 98 — SummaryGenerator
# -------------------------------------------------

class SummaryGeneratorInput(OrchestrationRequest):
    lesson_text: str


class SummaryGeneratorOutput(OrchestrationResult):
    summary: str


# -------------------------------------------------
# Agent 99 — ContentSimplifier
# -------------------------------------------------

class ContentSimplifierInput(OrchestrationRequest):
    text: str
    target_level: str


class ContentSimplifierOutput(OrchestrationResult):
    simplified_text: str


# -------------------------------------------------
# Agent 100 — AssessmentQuestionGenerator
# -------------------------------------------------

class AssessmentQuestionGeneratorInput(OrchestrationRequest):
    learning_objectives: List[LearningObjective]
    question_types: Optional[List[str]]


class AssessmentQuestionGeneratorOutput(OrchestrationResult):
    generated_questions: List[str]
    confidence: Optional[ConfidenceScore]

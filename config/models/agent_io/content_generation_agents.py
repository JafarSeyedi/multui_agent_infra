from pydantic import BaseModel
from typing import List, Optional
from .common import ConfidenceScore, Recommendation
from config.models.core.learning_objects import Lesson, LearningObjective


# -------------------------------------------------
# Agent 91 — Example Generator
# -------------------------------------------------

class ExampleGeneratorInput(BaseModel):
    concept: str
    difficulty_level: Optional[str]


class ExampleGeneratorOutput(BaseModel):
    examples: List[str]
    confidence: Optional[ConfidenceScore]


# -------------------------------------------------
# Agent 92 — Exercise Creator
# -------------------------------------------------

class ExerciseCreatorInput(BaseModel):
    concept: str
    learning_objective: Optional[LearningObjective]
    difficulty: Optional[str]


class ExerciseCreatorOutput(BaseModel):
    exercises: List[str]
    recommendations: Optional[List[Recommendation]]


# -------------------------------------------------
# Agent 93 — StoryBasedLessonCreator
# -------------------------------------------------

class StoryLessonCreatorInput(BaseModel):
    topic: str
    target_age: int


class StoryLessonCreatorOutput(BaseModel):
    story_text: str
    moral_message: Optional[str]


# -------------------------------------------------
# Agent 94 — ConceptExplanationGenerator
# -------------------------------------------------

class ConceptExplanationInput(BaseModel):
    concept: str
    student_level: Optional[str]


class ConceptExplanationOutput(BaseModel):
    explanation: str
    confidence: Optional[ConfidenceScore]


# -------------------------------------------------
# Agent 95 — PracticeQuestionGenerator
# -------------------------------------------------

class PracticeQuestionGeneratorInput(BaseModel):
    lesson: Lesson
    question_count: int = 5


class PracticeQuestionGeneratorOutput(BaseModel):
    questions: List[str]


# -------------------------------------------------
# Agent 96 — AdaptiveQuestionGenerator
# -------------------------------------------------

class AdaptiveQuestionGeneratorInput(BaseModel):
    recent_performance_score: float
    target_concept: str


class AdaptiveQuestionGeneratorOutput(BaseModel):
    generated_questions: List[str]
    difficulty_level: str


# -------------------------------------------------
# Agent 97 — ExplanationRewriter
# -------------------------------------------------

class ExplanationRewriterInput(BaseModel):
    original_explanation: str
    target_level: str


class ExplanationRewriterOutput(BaseModel):
    rewritten_explanation: str


# -------------------------------------------------
# Agent 98 — SummaryGenerator
# -------------------------------------------------

class SummaryGeneratorInput(BaseModel):
    lesson_text: str


class SummaryGeneratorOutput(BaseModel):
    summary: str


# -------------------------------------------------
# Agent 99 — ContentSimplifier
# -------------------------------------------------

class ContentSimplifierInput(BaseModel):
    text: str
    target_level: str


class ContentSimplifierOutput(BaseModel):
    simplified_text: str


# -------------------------------------------------
# Agent 100 — AssessmentQuestionGenerator
# -------------------------------------------------

class AssessmentQuestionGeneratorInput(BaseModel):
    learning_objectives: List[LearningObjective]
    question_types: Optional[List[str]]


class AssessmentQuestionGeneratorOutput(BaseModel):
    generated_questions: List[str]
    confidence: Optional[ConfidenceScore]

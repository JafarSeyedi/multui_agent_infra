from typing import List, Optional
from .common import ConfidenceScore, Recommendation
from .learning_objects import Lesson, LearningObjective
from ...models import AgentInput, AgentOutput

# -------------------------------------------------
# Agent 91 — Example Generator
# -------------------------------------------------

class ExampleGeneratorInput(AgentInput):
    concept: str
    difficulty_level: Optional[str]


class ExampleGeneratorOutput(AgentOutput):
    examples: List[str]
    confidence: Optional[ConfidenceScore]


# -------------------------------------------------
# Agent 92 — Exercise Creator
# -------------------------------------------------

class ExerciseCreatorInput(AgentInput):
    concept: str
    learning_objective: Optional[LearningObjective]
    difficulty: Optional[str]


class ExerciseCreatorOutput(AgentOutput):
    exercises: List[str]
    recommendations: Optional[List[Recommendation]]


# -------------------------------------------------
# Agent 93 — StoryBasedLessonCreator
# -------------------------------------------------

class StoryLessonCreatorInput(AgentInput):
    topic: str
    target_age: int


class StoryLessonCreatorOutput(AgentOutput):
    story_text: str
    moral_message: Optional[str]


# -------------------------------------------------
# Agent 94 — ConceptExplanationGenerator
# -------------------------------------------------

class ConceptExplanationInput(AgentInput):
    concept: str
    student_level: Optional[str]


class ConceptExplanationOutput(AgentOutput):
    explanation: str
    confidence: Optional[ConfidenceScore]


# -------------------------------------------------
# Agent 95 — PracticeQuestionGenerator
# -------------------------------------------------

class PracticeQuestionGeneratorInput(AgentInput):
    lesson: Lesson
    question_count: int = 5


class PracticeQuestionGeneratorOutput(AgentOutput):
    questions: List[str]


# -------------------------------------------------
# Agent 96 — AdaptiveQuestionGenerator
# -------------------------------------------------

class AdaptiveQuestionGeneratorInput(AgentInput):
    recent_performance_score: float
    target_concept: str


class AdaptiveQuestionGeneratorOutput(AgentOutput):
    generated_questions: List[str]
    difficulty_level: str


# -------------------------------------------------
# Agent 97 — ExplanationRewriter
# -------------------------------------------------

class ExplanationRewriterInput(AgentInput):
    original_explanation: str
    target_level: str


class ExplanationRewriterOutput(AgentOutput):
    rewritten_explanation: str


# -------------------------------------------------
# Agent 98 — SummaryGenerator
# -------------------------------------------------

class SummaryGeneratorInput(AgentInput):
    lesson_text: str


class SummaryGeneratorOutput(AgentOutput):
    summary: str


# -------------------------------------------------
# Agent 99 — ContentSimplifier
# -------------------------------------------------

class ContentSimplifierInput(AgentInput):
    text: str
    target_level: str


class ContentSimplifierOutput(AgentOutput):
    simplified_text: str


# -------------------------------------------------
# Agent 100 — AssessmentQuestionGenerator
# -------------------------------------------------

class AssessmentQuestionGeneratorInput(AgentInput):
    learning_objectives: List[LearningObjective]
    question_types: Optional[List[str]]


class AssessmentQuestionGeneratorOutput(AgentOutput):
    generated_questions: List[str]
    confidence: Optional[ConfidenceScore]

from ...models import AgentInput
from ...models import AgentOutput
from .common import ConfidenceScore
from .common import Recommendation
from .learning_objects import LearningObjective
from .learning_objects import Lesson

# -------------------------------------------------
# Agent 91 — Example Generator
# -------------------------------------------------

class ExampleGeneratorInput(AgentInput):
    concept: str
    difficulty_level: str | None


class ExampleGeneratorOutput(AgentOutput):
    examples: list[str]
    confidence: ConfidenceScore | None


# -------------------------------------------------
# Agent 92 — Exercise Creator
# -------------------------------------------------

class ExerciseCreatorInput(AgentInput):
    concept: str
    learning_objective: LearningObjective | None
    difficulty: str | None


class ExerciseCreatorOutput(AgentOutput):
    exercises: list[str]
    recommendations: list[Recommendation] | None


# -------------------------------------------------
# Agent 93 — StoryBasedLessonCreator
# -------------------------------------------------

class StoryLessonCreatorInput(AgentInput):
    topic: str
    target_age: int


class StoryLessonCreatorOutput(AgentOutput):
    story_text: str
    moral_message: str | None


# -------------------------------------------------
# Agent 94 — ConceptExplanationGenerator
# -------------------------------------------------

class ConceptExplanationInput(AgentInput):
    concept: str
    student_level: str | None


class ConceptExplanationOutput(AgentOutput):
    explanation: str
    confidence: ConfidenceScore | None


# -------------------------------------------------
# Agent 95 — PracticeQuestionGenerator
# -------------------------------------------------

class PracticeQuestionGeneratorInput(AgentInput):
    lesson: Lesson
    question_count: int = 5


class PracticeQuestionGeneratorOutput(AgentOutput):
    questions: list[str]


# -------------------------------------------------
# Agent 96 — AdaptiveQuestionGenerator
# -------------------------------------------------

class AdaptiveQuestionGeneratorInput(AgentInput):
    recent_performance_score: float
    target_concept: str


class AdaptiveQuestionGeneratorOutput(AgentOutput):
    generated_questions: list[str]
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
    learning_objectives: list[LearningObjective]
    question_types: list[str] | None


class AssessmentQuestionGeneratorOutput(AgentOutput):
    generated_questions: list[str]
    confidence: ConfidenceScore | None

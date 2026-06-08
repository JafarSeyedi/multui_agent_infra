from typing import Literal

from ...models import AgentInput
from ...models import AgentOutput

# --- Agent Models 9 ---
class QuestionRefineInput(AgentInput):
    raw_question: str
    lesson_context: str
    grade_level: str | None

class QuestionRefineOutput(AgentOutput):
    refined_question: str
    clarification_notes: str | None

# --- Agent Models 10: Question Generator ---
QuestionType = Literal["mcq", "short_answer", "long_answer", "true_false", "fill_in_blank"]
DifficultyLevel = Literal[1, 2, 3, 4, 5] # 1: Easy, 5: Hard

class QuestionGenerationInput(AgentInput):
    topic: str
    lesson_context: str
    num_questions: int = 1
    question_types: list[QuestionType] | None = None
    difficulty_range: tuple[DifficultyLevel, DifficultyLevel] | None = (2, 4)
    learning_objectives: list[str] | None = None
    subject: str | None

class QuestionGenerationOutput(AgentOutput):
    questions: list[dict] # Dictionary for flexibility, can be converted to Question model later

# --- مدل‌های عامل 11: تولیدکننده راهنمایی (Hint Generator) ---
class HintGenerationInput(AgentInput):
    question_text: str
    user_answer: str | None = None
    correct_answer: str | None = None
    lessen_context: str # Lesson context or problem statement
    hint_level: int = 1 # Number of hints requested

class HintGenerationOutput(AgentOutput):
    hints: list[str]

# --- مدل‌های عامل 12: تولیدکننده توضیح (Explanation Generator) ---
class ExplanationGenerationInput(AgentInput):
    concept: str | None = None
    question_text: str | None = None
    user_answer: str | None = None
    correct_answer: str | None = None
    lesson_context: str
    explanation_depth: Literal["brief", "detailed", "expert"] = "detailed"
    target_audience: str | None = "student" # e.g., "beginner", "advanced", "student"

class ExplanationGenerationOutput(AgentOutput):
    explanation: str
    related_concepts: list[str] | None = None
    further_reading: list[str] | None = None

# --- مدل‌های عامل 13: تطبیق‌دهنده سطح دشواری (Difficulty Adapter) ---
class DifficultyAdaptationInput(AgentInput):
    content_item: dict # Can be a lesson, question, or assignment
    current_difficulty: DifficultyLevel
    target_difficulty: DifficultyLevel
    student_profile: dict | None # Reference to StudentProfile model

class DifficultyAdaptationOutput(AgentOutput):
    adapted_content_item: dict # Modified content item
    adaptation_details: str

# --- مدل‌های عامل 14: آشکارساز برداشت نادرست (Misconception Detector) ---
class MisconceptionDetectionInput(AgentInput):
    user_response: str
    topic: str
    lesson_context: str
    common_misconceptions: list[str] | None = None

class Misconception(AgentOutput):
    identified_misconception: str
    evidence: str
    suggested_correction: str

class MisconceptionDetectionOutput(AgentOutput):
    misconceptions: list[Misconception]
    confidence_score: float

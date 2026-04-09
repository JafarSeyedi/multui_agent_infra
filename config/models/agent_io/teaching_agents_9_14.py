from pydantic import BaseModel
from agents.orchestration.models import OrchestrationRequest, OrchestrationResult
from typing import List, Optional, Dict, Literal

# --- مدل‌های عامل 9 ---
class QuestionRefineInput(OrchestrationRequest):
    raw_question: str
    lesson_context: str
    grade_level: Optional[str]

class QuestionRefineOutput(OrchestrationResult):
    refined_question: str
    clarification_notes: Optional[str]

# --- مدل‌های عامل 10: پرسش‌ساز (Question Generator) ---
QuestionType = Literal["mcq", "short_answer", "long_answer", "true_false", "fill_in_blank"]
DifficultyLevel = Literal[1, 2, 3, 4, 5] # 1: Easy, 5: Hard

class QuestionGenerationInput(OrchestrationRequest):
    topic: str
    lesson_context: str
    num_questions: int = 1
    question_types: Optional[List[QuestionType]] = None
    difficulty_range: Optional[tuple[DifficultyLevel, DifficultyLevel]] = (2, 4)
    learning_objectives: Optional[List[str]] = None
    subject: Optional[str]

class QuestionGenerationOutput(OrchestrationResult):
    questions: List[Dict] # Dictionary for flexibility, can be converted to Question model later

# --- مدل‌های عامل 11: تولیدکننده راهنمایی (Hint Generator) ---
class HintGenerationInput(OrchestrationRequest):
    question_text: str
    user_answer: Optional[str] = None
    correct_answer: Optional[str] = None
    lessen_context: str # Lesson context or problem statement
    hint_level: int = 1 # Number of hints requested

class HintGenerationOutput(OrchestrationResult):
    hints: List[str]

# --- مدل‌های عامل 12: تولیدکننده توضیح (Explanation Generator) ---
class ExplanationGenerationInput(OrchestrationRequest):
    concept: Optional[str] = None
    question_text: Optional[str] = None
    user_answer: Optional[str] = None
    correct_answer: Optional[str] = None
    lesson_context: str
    explanation_depth: Literal["brief", "detailed", "expert"] = "detailed"
    target_audience: Optional[str] = "student" # e.g., "beginner", "advanced", "student"

class ExplanationGenerationOutput(OrchestrationResult):
    explanation: str
    related_concepts: Optional[List[str]] = None
    further_reading: Optional[List[str]] = None

# --- مدل‌های عامل 13: تطبیق‌دهنده سطح دشواری (Difficulty Adapter) ---
class DifficultyAdaptationInput(OrchestrationRequest):
    content_item: Dict # Can be a lesson, question, or assignment
    current_difficulty: DifficultyLevel
    target_difficulty: DifficultyLevel
    student_profile: Optional[Dict] # Reference to StudentProfile model

class DifficultyAdaptationOutput(OrchestrationResult):
    adapted_content_item: Dict # Modified content item
    adaptation_details: str

# --- مدل‌های عامل 14: آشکارساز برداشت نادرست (Misconception Detector) ---
class MisconceptionDetectionInput(OrchestrationRequest):
    user_response: str
    topic: str
    lesson_context: str
    common_misconceptions: Optional[List[str]] = None

class Misconception(OrchestrationResult):
    identified_misconception: str
    evidence: str
    suggested_correction: str

class MisconceptionDetectionOutput(OrchestrationResult):
    misconceptions: List[Misconception]
    confidence_score: float

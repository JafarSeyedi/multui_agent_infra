# agents/content/models/learning_objects.py
from datetime import datetime
from enum import Enum
from typing import Literal

from pydantic import BaseModel
from pydantic import Field


# --------------------------------------------------
# Core Identity Models
# --------------------------------------------------

class StudentProfile(BaseModel):
    student_id: str
    name: str | None
    grade_level: str | None
    learning_style: str | None
    interests: list[str] | None
    preferred_language: str | None


class InstructorProfile(BaseModel):
    instructor_id: str
    name: str | None
    subject_specialization: list[str] | None

# -------------------------------
# LearningStyle CLASS
# -------------------------------
# -------------------------------
# ENUMS
# -------------------------------

class VAKRStyle(str, Enum):
    """VARK Model - most common classification"""
    VISUAL      = "visual"       # Image, diagram, color
    AUDITORY    = "auditory"     # شنیداری، توضیح کلامی
    READING     = "reading"      # متن، فهرست، یادداشت
    KINESTHETIC = "kinesthetic"  # مثال عملی، آزمایش، تمرین


class PacePreference(str, Enum):
    SLOW     = "slow"     # توضیح مفصل، گام به گام
    MODERATE = "moderate"
    FAST     = "fast"     # خلاصه، نکات کلیدی

class AbstractionLevel(str, Enum):
    CONCRETE  = "concrete"   # مثال‌های واقعی، کاربردی
    BALANCED  = "balanced"
    ABSTRACT  = "abstract"   # مفاهیم نظری، فرمول‌ها

class FeedbackPreference(str, Enum):
    IMMEDIATE = "immediate"  # بازخورد فوری بعد از هر قدم
    PERIODIC  = "periodic"   # بعد از هر بخش
    FINAL     = "final"      # فقط در پایان

class LearningStyle(BaseModel):
    """
    پروفایل سبک یادگیری یک کاربر.
    همه فیلدها optional هستند تا بتوان به‌تدریج از تعاملات کاربر پر کرد.
    """

    # سبک اصلی (VARK)
    primary_style: VAKRStyle = VAKRStyle.READING

    # سبک ثانویه (اختیاری - بعضی‌ها ترکیبی یاد می‌گیرند)
    secondary_style: VAKRStyle | None = None

    # سرعت پیشرفت
    pace: PacePreference = PacePreference.MODERATE

    # سطح انتزاع مطلوب
    abstraction_level: AbstractionLevel = AbstractionLevel.BALANCED

    # ترجیح بازخورد
    feedback_preference: FeedbackPreference = FeedbackPreference.PERIODIC

    # آیا مثال‌های کد/عملی می‌خواهد؟
    prefers_examples: bool = True

    # آیا تمرین تعاملی می‌خواهد؟
    prefers_exercises: bool = False

    # آیا خلاصه در پایان می‌خواهد؟
    prefers_summary: bool = True

    # زبان ترجیحی توضیحات
    language: str = "fa"

    # امتیاز اطمینان به هر بُعد (0.0 تا 1.0) - برای adaptive learning
    # هر چه بیشتر با کاربر تعامل شود، این مقادیر دقیق‌تر می‌شوند
    confidence_scores: dict[str, float] = Field(
        default_factory=lambda: {
            "primary_style":      0.5,
            "pace":               0.5,
            "abstraction_level":  0.5,
        }
    )

    # Metadata - منبع تشخیص سبک
    detected_from: str | None = None  # e.g., "quiz", "interaction_history", "manual"

# --------------------------------------------------
# Learning Content Models
# --------------------------------------------------




class LearningObjective(BaseModel):
    objective_id: str
    description: str
    skill_tag: str | None
    grade_level: str
    subject: str


class Lesson(BaseModel):
    lesson_id: str
    title: str
    subject: str
    grade_level: str
    content_summary: str | None
    learning_objectives: list[LearningObjective] | None
    prerequisites: list[str] = []           # وابستگی‌ها
    metadata: dict[str, str] = {}           # اضافات


class ConceptNode(BaseModel):
    concept_id: str
    name: str
    description: str | None
    related_concepts: list[str] | None
    difficulty_estimate: float | None


class GlossaryEntry(BaseModel):
    term: str
    definition: str
    grade_level: str
    examples: list[str] = []
    related_lessons: list[str] = []


# --------------------------------------------------
# Assessment & Question Models
# --------------------------------------------------

QuestionType = Literal[
    "mcq", "true_false", "short_answer", "long_answer", "fill_in_blank", "true_false"
]

DifficultyLevel = Literal[
    "easy", "medium", "hard", "very_hard"
]

class Question(BaseModel):
    question_id: str
    lesson_id: str
    text: str
    question_type: QuestionType
    difficulty: DifficultyLevel
    options: list[str] | None = None
    correct_answer: str | None = None
    concept_tags: list[str] | None


class StudentAnswer(BaseModel):
    question_id: str
    student_id: str
    answer_text: str
    is_correct: bool | None
    attempt_timestamp: datetime

class AssessmentResult(BaseModel):
    assessment_id: str
    student_id: str
    title: str
    lesson_id: str
    questions: list[Question]
    adaptive: bool = False       # آیا آزمون تطبیقی است؟
    created_at: datetime
    total_score: float
    max_score: float
    start_time: datetime
    end_time: datetime
    detailed_scores: dict[str, float] | None  # question_id: score

class Assignment(BaseModel):
    id: str
    title: str
    lesson_id: str
    questions: list[Question]
    due_date: datetime | None = None
    created_at: datetime


class LearningEvent(BaseModel):
    event_id: str
    student_id: str
    event_type: Literal[
        "lesson_view",
        "quiz_attempt",
        "video_watch",
        "content_reading",
        "interaction"
    ]
    timestamp: datetime
    metadata: dict | None


# --------------------------------------------------
# Performance & Progress Models
# --------------------------------------------------

class SkillPerformance(BaseModel):
    skill_id: str
    student_id: str
    performance_score: float
    mastery_level: Literal["low", "medium", "high"]


class LearningProgress(BaseModel):
    student_id: str
    completed_lessons: list[str]
    recent_scores: list[float] | None
    overall_mastery: float | None
    last_activity_ts: datetime
    objective: str
    status: Literal["on_track", "needs_improvement", "mastered", "struggling"]
    score_trend: list[float] | None = None
    confidence_level: float | None = None


# --------------------------------------------------
# Resource Models
# --------------------------------------------------

class LearningResource(BaseModel):
    resource_id: str
    title: str
    url: str | None
    resource_type: Literal["video", "article", "exercise", "simulation"]
    associated_concepts: list[str] | None

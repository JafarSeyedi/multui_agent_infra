# config/models/agent_io/learning_objects.py

from typing import List, Optional, Dict, Literal
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field


# --------------------------------------------------
# Core Identity Models
# --------------------------------------------------

class StudentProfile(BaseModel):
    student_id: str
    name: Optional[str]
    grade_level: Optional[str]
    learning_style: Optional[str]
    interests: Optional[List[str]]
    preferred_language: Optional[str]


class InstructorProfile(BaseModel):
    instructor_id: str
    name: Optional[str]
    subject_specialization: Optional[List[str]]

# -------------------------------
# LearningStyle CLASS
# -------------------------------
# -------------------------------
# ENUMS
# -------------------------------

class VAKRStyle(str, Enum):
    """مدل VARK - رایج‌ترین دسته‌بندی"""
    VISUAL      = "visual"       # تصویر، نمودار، رنگ
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
    secondary_style: Optional[VAKRStyle] = None

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
    confidence_scores: Dict[str, float] = Field(
        default_factory=lambda: {
            "primary_style":      0.5,
            "pace":               0.5,
            "abstraction_level":  0.5,
        }
    )

    # متادیتا - منبع تشخیص سبک
    detected_from: Optional[str] = None  # e.g., "quiz", "interaction_history", "manual"

# --------------------------------------------------
# Learning Content Models
# --------------------------------------------------




class LearningObjective(BaseModel):
    objective_id: str
    description: str
    skill_tag: Optional[str]
    grade_level: str
    subject: str


class Lesson(BaseModel):
    lesson_id: str
    title: str
    subject: str
    grade_level: str
    content_summary: Optional[str]
    learning_objectives: Optional[List[LearningObjective]]
    prerequisites: List[str] = []           # وابستگی‌ها
    metadata: Dict[str, str] = {}           # اضافات


class ConceptNode(BaseModel):
    concept_id: str
    name: str
    description: Optional[str]
    related_concepts: Optional[List[str]]
    difficulty_estimate: Optional[float]


class GlossaryEntry(BaseModel):
    term: str
    definition: str
    grade_level: str
    examples: List[str] = []
    related_lessons: List[str] = []


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
    options: Optional[List[str]] = None
    correct_answer: Optional[str] = None
    concept_tags: Optional[List[str]]


class StudentAnswer(BaseModel):
    question_id: str
    student_id: str
    answer_text: str
    is_correct: Optional[bool]
    attempt_timestamp: datetime

class AssessmentResult(BaseModel):
    assessment_id: str
    student_id: str
    title: str
    lesson_id: str
    questions: List[Question]
    adaptive: bool = False       # آیا آزمون تطبیقی است؟
    created_at: datetime
    total_score: float
    max_score: float
    start_time: datetime
    end_time: datetime
    detailed_scores: Optional[Dict[str, float]]  # question_id: score

class Assignment(BaseModel):
    id: str
    title: str
    lesson_id: str
    questions: List[Question]
    due_date: Optional[datetime] = None
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
    metadata: Optional[Dict]


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
    completed_lessons: List[str]
    recent_scores: Optional[List[float]]
    overall_mastery: Optional[float]
    last_activity_ts: datetime
    objective: str
    status: Literal["on_track", "needs_improvement", "mastered", "struggling"]
    score_trend: Optional[List[float]] = None
    confidence_level: Optional[float] = None


# --------------------------------------------------
# Resource Models
# --------------------------------------------------

class LearningResource(BaseModel):
    resource_id: str
    title: str
    url: Optional[str]
    resource_type: Literal["video", "article", "exercise", "simulation"]
    associated_concepts: Optional[List[str]]

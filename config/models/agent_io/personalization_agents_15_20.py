from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Literal
from datetime import datetime
from .user_models import LearningStyle, StudentProfile # Import from user_models

# --- مدل‌های عامل 15: مدرس دیالوگ (Dialogue Tutor) ---
class DialogueTutorInput(OrchestrationRequest):
    user_query: str
    conversation_history: List[Dict] # History of user messages and tutor responses
    student_profile: StudentProfile # Full student profile
    current_lesson_context: Optional[str] = None

class TutorResponse(BaseModel):
    response_text: str
    actions: Optional[List[str]] = None # e.g., "ask_clarification", "suggest_resource"

class DialogueTutorOutput(OrchestrationResult):
    tutor_response: TutorResponse
    next_step_recommendation: Optional[str] = None

# --- مدل‌های عامل 16: سازگار کننده سبک یادگیری (Learning Style Adapter) ---
class StyleAdaptationInput(OrchestrationRequest):
    content: str # Lesson content, explanation, etc.
    learning_style: LearningStyle
    content_type: str # e.g., "lesson", "explanation", "exercise"

class AdaptedContent(BaseModel):
    adapted_text: Optional[str] = None
    suggested_visuals: Optional[List[str]] = None # e.g., image prompts
    suggested_activities: Optional[List[str]] = None # e.g., hands-on exercises

class StyleAdaptationOutput(OrchestrationResult):
    adapted_content: AdaptedContent
    adaptation_effectiveness_score: float

# --- مدل‌های عامل 17: تحلیلگر پیشرفت (Progress Analyzer) ---
class ProgressAnalysisInput(OrchestrationRequest):
    student_id: str
    performance_data: Dict # e.g., assessment scores, quiz results, interaction logs
    learning_objectives: Optional[List[str]] = None
    time_period: Optional[str] = None # e.g., "last_week", "semester"

class LearningProgress(BaseModel):
    objective: str
    status: Literal["on_track", "needs_improvement", "mastered", "struggling"]
    score_trend: Optional[List[float]] = None
    confidence_level: Optional[float] = None

class ProgressAnalysisOutput(OrchestrationResult):
    overall_progress: float
    key_strengths: List[str]
    areas_for_improvement: List[str]
    detailed_progress: List[LearningProgress]
    recommendations: List[str]

# --- مدل‌های عامل 18: سازنده مسیر یادگیری (Learning Path Creator) ---
class LearningPathCreationInput(OrchestrationRequest):
    student_profile: StudentProfile
    learning_goals: List[str]
    available_content: List[str] # IDs or titles of available lessons/modules
    current_knowledge_level: Optional[Dict] = None

class LearningStep(BaseModel):
    item_id: str
    type: str # e.g., "lesson", "quiz", "assignment", "external_resource"
    sequence: int
    estimated_time: Optional[str] = None

class LearningPathCreationOutput(OrchestrationResult):
    learning_path: List[LearningStep]
    path_rationale: str

# --- مدل‌های عامل 19: پیشنهاد دهنده منابع (Resource Recommender) ---
class ResourceRecommendationInput(OrchestrationRequest):
    student_profile: StudentProfile
    current_topic: str
    learning_goal: Optional[str] = None
    performance_data: Optional[Dict] = None # e.g., recent struggles

class RecommendedResource(BaseModel):
    resource_id: str
    resource_type: str # e.g., "lesson", "video", "article", "practice_problem"
    title: str
    relevance_score: float
    reason: str

class ResourceRecommendationOutput(OrchestrationResult):
    recommendations: List[RecommendedResource]

# --- مدل‌های عامل 20: تحلیلگر سبک تعامل (Interaction Style Analyzer) ---
class InteractionStyleAnalysisInput(OrchestrationRequest):
    user_id: str
    interaction_logs: List[Dict] # Logs of user interactions with the system

class InteractionPattern(BaseModel):
    pattern_name: str
    description: str
    frequency: int

class InteractionStyleAnalysisOutput(OrchestrationResult):
    dominant_interaction_style: str
    identified_patterns: List[InteractionPattern]
    suggested_system_adjustments: List[str]

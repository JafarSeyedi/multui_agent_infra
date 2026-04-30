from pydantic import BaseModel
from typing import List, Optional, Dict, Literal
from ...models import AgentInput, AgentOutput
from .learning_objects import LearningStyle, StudentProfile, LearningProgress

# --- مدل‌های عامل 15: مدرس دیالوگ (Dialogue Tutor) ---
class DialogueTutorInput(AgentInput):
    user_query: str
    conversation_history: List[Dict] # History of user messages and tutor responses
    student_profile: StudentProfile # Full student profile
    current_lesson_context: Optional[str] = None

class TutorResponse(BaseModel):
    response_text: str
    actions: Optional[List[str]] = None # e.g., "ask_clarification", "suggest_resource"

class DialogueTutorOutput(AgentOutput):
    tutor_response: TutorResponse
    next_step_recommendation: Optional[str] = None

# --- مدل‌های عامل 16: سازگار کننده سبک یادگیری (Learning Style Adapter) ---
class StyleAdaptationInput(AgentInput):
    content: str # Lesson content, explanation, etc.
    learning_style: LearningStyle
    content_type: str # e.g., "lesson", "explanation", "exercise"

class AdaptedContent(BaseModel):
    adapted_text: Optional[str] = None
    suggested_visuals: Optional[List[str]] = None # e.g., image prompts
    suggested_activities: Optional[List[str]] = None # e.g., hands-on exercises

class StyleAdaptationOutput(AgentOutput):
    adapted_content: AdaptedContent
    adaptation_effectiveness_score: float

# --- مدل‌های عامل 17: تحلیلگر پیشرفت (Progress Analyzer) ---
class ProgressAnalysisInput(AgentInput):
    student_id: str
    performance_data: Dict # e.g., assessment scores, quiz results, interaction logs
    learning_objectives: Optional[List[str]] = None
    time_period: Optional[str] = None # e.g., "last_week", "semester"

class ProgressAnalysisOutput(AgentOutput):
    overall_progress: float
    key_strengths: List[str]
    areas_for_improvement: List[str]
    detailed_progress: List[LearningProgress]
    recommendations: List[str]

# --- مدل‌های عامل 18: سازنده مسیر یادگیری (Learning Path Creator) ---
class LearningPathCreationInput(AgentInput):
    student_profile: StudentProfile
    learning_goals: List[str]
    available_content: List[str] # IDs or titles of available lessons/modules
    current_knowledge_level: Optional[Dict] = None

class LearningStep(BaseModel):
    item_id: str
    type: str # e.g., "lesson", "quiz", "assignment", "external_resource"
    sequence: int
    estimated_time: Optional[str] = None

class LearningPathCreationOutput(AgentOutput):
    learning_path: List[LearningStep]
    path_rationale: str

# --- مدل‌های عامل 19: پیشنهاد دهنده منابع (Resource Recommender) ---
class ResourceRecommendationInput(AgentInput):
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

class ResourceRecommendationOutput(AgentOutput):
    recommendations: List[RecommendedResource]

# --- مدل‌های عامل 20: تحلیلگر سبک تعامل (Interaction Style Analyzer) ---
class InteractionStyleAnalysisInput(AgentInput):
    user_id: str
    interaction_logs: List[Dict] # Logs of user interactions with the system

class InteractionPattern(BaseModel):
    pattern_name: str
    description: str
    frequency: int

class InteractionStyleAnalysisOutput(AgentOutput):
    dominant_interaction_style: str
    identified_patterns: List[InteractionPattern]
    suggested_system_adjustments: List[str]

from pydantic import BaseModel

from ...models import AgentInput
from ...models import AgentOutput
from .learning_objects import LearningProgress
from .learning_objects import LearningStyle
from .learning_objects import StudentProfile

# --- مدل‌های عامل 15: مدرس دیالوگ (Dialogue Tutor) ---
class DialogueTutorInput(AgentInput):
    user_query: str
    conversation_history: list[dict] # History of user messages and tutor responses
    student_profile: StudentProfile # Full student profile
    current_lesson_context: str | None = None

class TutorResponse(BaseModel):
    response_text: str
    actions: list[str] | None = None # e.g., "ask_clarification", "suggest_resource"

class DialogueTutorOutput(AgentOutput):
    tutor_response: TutorResponse
    next_step_recommendation: str | None = None

# --- مدل‌های عامل 16: سازگار کننده سبک یادگیری (Learning Style Adapter) ---
class StyleAdaptationInput(AgentInput):
    content: str # Lesson content, explanation, etc.
    learning_style: LearningStyle
    content_type: str # e.g., "lesson", "explanation", "exercise"

class AdaptedContent(BaseModel):
    adapted_text: str | None = None
    suggested_visuals: list[str] | None = None # e.g., image prompts
    suggested_activities: list[str] | None = None # e.g., hands-on exercises

class StyleAdaptationOutput(AgentOutput):
    adapted_content: AdaptedContent
    adaptation_effectiveness_score: float

# --- مدل‌های عامل 17: تحلیلگر پیشرفت (Progress Analyzer) ---
class ProgressAnalysisInput(AgentInput):
    student_id: str
    performance_data: dict # e.g., assessment scores, quiz results, interaction logs
    learning_objectives: list[str] | None = None
    time_period: str | None = None # e.g., "last_week", "semester"

class ProgressAnalysisOutput(AgentOutput):
    overall_progress: float
    key_strengths: list[str]
    areas_for_improvement: list[str]
    detailed_progress: list[LearningProgress]
    recommendations: list[str]

# --- مدل‌های عامل 18: سازنده مسیر یادگیری (Learning Path Creator) ---
class LearningPathCreationInput(AgentInput):
    student_profile: StudentProfile
    learning_goals: list[str]
    available_content: list[str] # IDs or titles of available lessons/modules
    current_knowledge_level: dict | None = None

class LearningStep(BaseModel):
    item_id: str
    type: str # e.g., "lesson", "quiz", "assignment", "external_resource"
    sequence: int
    estimated_time: str | None = None

class LearningPathCreationOutput(AgentOutput):
    learning_path: list[LearningStep]
    path_rationale: str

# --- مدل‌های عامل 19: پیشنهاد دهنده منابع (Resource Recommender) ---
class ResourceRecommendationInput(AgentInput):
    student_profile: StudentProfile
    current_topic: str
    learning_goal: str | None = None
    performance_data: dict | None = None # e.g., recent struggles

class RecommendedResource(BaseModel):
    resource_id: str
    resource_type: str # e.g., "lesson", "video", "article", "practice_problem"
    title: str
    relevance_score: float
    reason: str

class ResourceRecommendationOutput(AgentOutput):
    recommendations: list[RecommendedResource]

# --- مدل‌های عامل 20: تحلیلگر سبک تعامل (Interaction Style Analyzer) ---
class InteractionStyleAnalysisInput(AgentInput):
    user_id: str
    interaction_logs: list[dict] # Logs of user interactions with the system

class InteractionPattern(BaseModel):
    pattern_name: str
    description: str
    frequency: int

class InteractionStyleAnalysisOutput(AgentOutput):
    dominant_interaction_style: str
    identified_patterns: list[InteractionPattern]
    suggested_system_adjustments: list[str]

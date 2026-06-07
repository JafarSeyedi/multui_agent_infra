from ...models import AgentInput
from ...models import AgentOutput
from .common import ConfidenceScore


# -------------------------------------------------
# Agent 101 — TextToSpeechAgent
# -------------------------------------------------

class TextToSpeechInput(AgentInput):
    text: str
    voice_style: str | None


class TextToSpeechOutput(AgentOutput):
    audio_file_url: str


# -------------------------------------------------
# Agent 102 — SpeechToTextAgent
# -------------------------------------------------

class SpeechToTextInput(AgentInput):
    audio_file_url: str
    language: str | None


class SpeechToTextOutput(AgentOutput):
    transcript: str
    confidence: ConfidenceScore | None


# -------------------------------------------------
# Agent 103 — VisualIllustrationGenerator
# -------------------------------------------------

class VisualIllustrationInput(AgentInput):
    concept: str
    style: str | None


class VisualIllustrationOutput(AgentOutput):
    image_url: str
    caption: str | None


# -------------------------------------------------
# Agent 104 — BoardDrawingAgent
# -------------------------------------------------

class BoardDrawingInput(AgentInput):
    equation_or_diagram: str


class BoardDrawingOutput(AgentOutput):
    drawing_url: str


# -------------------------------------------------
# Agent 105 — EmotionAnalysisAgent
# -------------------------------------------------

class EmotionAnalysisInput(AgentInput):
    video_frame_urls: list[str]


class EmotionAnalysisOutput(AgentOutput):
    detected_emotions: dict[str, float]  # e.g., {"bored":0.1, "focused":0.8}
    dominant_emotion: str | None


# -------------------------------------------------
# Agent 106 — EngagementDetector
# -------------------------------------------------

class EngagementDetectorInput(AgentInput):
    student_behavior_events: list[str]


class EngagementDetectorOutput(AgentOutput):
    engagement_score: float


# -------------------------------------------------
# Agent 107 — VisualFeedbackAgent
# -------------------------------------------------

class VisualFeedbackInput(AgentInput):
    student_emotion: str
    lesson_state: str


class VisualFeedbackOutput(AgentOutput):
    feedback_image_url: str


# -------------------------------------------------
# Agent 108 — GestureRecognitionAgent
# -------------------------------------------------

class GestureRecognitionInput(AgentInput):
    video_clip_url: str


class GestureRecognitionOutput(AgentOutput):
    recognized_gestures: list[str]


# -------------------------------------------------
# Agent 109 — AudioFeedbackAgent
# -------------------------------------------------

class AudioFeedbackInput(AgentInput):
    detected_emotion: str
    student_id: str | None


class AudioFeedbackOutput(AgentOutput):
    audio_response_url: str


# -------------------------------------------------
# Agent 110 — InteractiveLessonOrchestrator
# -------------------------------------------------

class InteractiveLessonOrchestratorInput(AgentInput):
    multimodal_context: dict  # combination of audio, visual, and text state


class InteractiveLessonOrchestratorOutput(AgentOutput):
    orchestrated_actions: list[str]
    confidence: ConfidenceScore | None

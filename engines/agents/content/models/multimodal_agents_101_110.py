from typing import List, Optional, Dict
from engines.agents.models import AgentInput, AgentOutput
from .common import ConfidenceScore


# -------------------------------------------------
# Agent 101 — TextToSpeechAgent
# -------------------------------------------------

class TextToSpeechInput(AgentInput):
    text: str
    voice_style: Optional[str]


class TextToSpeechOutput(AgentOutput):
    audio_file_url: str


# -------------------------------------------------
# Agent 102 — SpeechToTextAgent
# -------------------------------------------------

class SpeechToTextInput(AgentInput):
    audio_file_url: str
    language: Optional[str]


class SpeechToTextOutput(AgentOutput):
    transcript: str
    confidence: Optional[ConfidenceScore]


# -------------------------------------------------
# Agent 103 — VisualIllustrationGenerator
# -------------------------------------------------

class VisualIllustrationInput(AgentInput):
    concept: str
    style: Optional[str]


class VisualIllustrationOutput(AgentOutput):
    image_url: str
    caption: Optional[str]


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
    video_frame_urls: List[str]


class EmotionAnalysisOutput(AgentOutput):
    detected_emotions: Dict[str, float]  # e.g., {"bored":0.1, "focused":0.8}
    dominant_emotion: Optional[str]


# -------------------------------------------------
# Agent 106 — EngagementDetector
# -------------------------------------------------

class EngagementDetectorInput(AgentInput):
    student_behavior_events: List[str]


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
    recognized_gestures: List[str]


# -------------------------------------------------
# Agent 109 — AudioFeedbackAgent
# -------------------------------------------------

class AudioFeedbackInput(AgentInput):
    detected_emotion: str
    student_id: Optional[str]


class AudioFeedbackOutput(AgentOutput):
    audio_response_url: str


# -------------------------------------------------
# Agent 110 — InteractiveLessonOrchestrator
# -------------------------------------------------

class InteractiveLessonOrchestratorInput(AgentInput):
    multimodal_context: Dict  # combination of audio, visual, and text state


class InteractiveLessonOrchestratorOutput(AgentOutput):
    orchestrated_actions: List[str]
    confidence: Optional[ConfidenceScore]

from pydantic import BaseModel
from typing import List, Optional, Dict
from .common import ConfidenceScore, Evidence


# -------------------------------------------------
# Agent 101 — TextToSpeechAgent
# -------------------------------------------------

class TextToSpeechInput(OrchestrationRequest):
    text: str
    voice_style: Optional[str]


class TextToSpeechOutput(OrchestrationResult):
    audio_file_url: str


# -------------------------------------------------
# Agent 102 — SpeechToTextAgent
# -------------------------------------------------

class SpeechToTextInput(OrchestrationRequest):
    audio_file_url: str
    language: Optional[str]


class SpeechToTextOutput(OrchestrationResult):
    transcript: str
    confidence: Optional[ConfidenceScore]


# -------------------------------------------------
# Agent 103 — VisualIllustrationGenerator
# -------------------------------------------------

class VisualIllustrationInput(OrchestrationRequest):
    concept: str
    style: Optional[str]


class VisualIllustrationOutput(OrchestrationResult):
    image_url: str
    caption: Optional[str]


# -------------------------------------------------
# Agent 104 — BoardDrawingAgent
# -------------------------------------------------

class BoardDrawingInput(OrchestrationRequest):
    equation_or_diagram: str


class BoardDrawingOutput(OrchestrationResult):
    drawing_url: str


# -------------------------------------------------
# Agent 105 — EmotionAnalysisAgent
# -------------------------------------------------

class EmotionAnalysisInput(OrchestrationRequest):
    video_frame_urls: List[str]


class EmotionAnalysisOutput(OrchestrationResult):
    detected_emotions: Dict[str, float]  # e.g., {"bored":0.1, "focused":0.8}
    dominant_emotion: Optional[str]


# -------------------------------------------------
# Agent 106 — EngagementDetector
# -------------------------------------------------

class EngagementDetectorInput(OrchestrationRequest):
    student_behavior_events: List[str]


class EngagementDetectorOutput(OrchestrationResult):
    engagement_score: float


# -------------------------------------------------
# Agent 107 — VisualFeedbackAgent
# -------------------------------------------------

class VisualFeedbackInput(OrchestrationRequest):
    student_emotion: str
    lesson_state: str


class VisualFeedbackOutput(OrchestrationResult):
    feedback_image_url: str


# -------------------------------------------------
# Agent 108 — GestureRecognitionAgent
# -------------------------------------------------

class GestureRecognitionInput(OrchestrationRequest):
    video_clip_url: str


class GestureRecognitionOutput(OrchestrationResult):
    recognized_gestures: List[str]


# -------------------------------------------------
# Agent 109 — AudioFeedbackAgent
# -------------------------------------------------

class AudioFeedbackInput(OrchestrationRequest):
    detected_emotion: str
    student_id: Optional[str]


class AudioFeedbackOutput(OrchestrationResult):
    audio_response_url: str


# -------------------------------------------------
# Agent 110 — InteractiveLessonOrchestrator
# -------------------------------------------------

class InteractiveLessonOrchestratorInput(OrchestrationRequest):
    multimodal_context: Dict  # combination of audio, visual, and text state


class InteractiveLessonOrchestratorOutput(OrchestrationResult):
    orchestrated_actions: List[str]
    confidence: Optional[ConfidenceScore]

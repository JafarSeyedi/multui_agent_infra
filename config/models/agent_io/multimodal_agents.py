from pydantic import BaseModel
from typing import List, Optional, Dict
from .common import ConfidenceScore, Evidence


# -------------------------------------------------
# Agent 101 — TextToSpeechAgent
# -------------------------------------------------

class TextToSpeechInput(BaseModel):
    text: str
    voice_style: Optional[str]


class TextToSpeechOutput(BaseModel):
    audio_file_url: str


# -------------------------------------------------
# Agent 102 — SpeechToTextAgent
# -------------------------------------------------

class SpeechToTextInput(BaseModel):
    audio_file_url: str
    language: Optional[str]


class SpeechToTextOutput(BaseModel):
    transcript: str
    confidence: Optional[ConfidenceScore]


# -------------------------------------------------
# Agent 103 — VisualIllustrationGenerator
# -------------------------------------------------

class VisualIllustrationInput(BaseModel):
    concept: str
    style: Optional[str]


class VisualIllustrationOutput(BaseModel):
    image_url: str
    caption: Optional[str]


# -------------------------------------------------
# Agent 104 — BoardDrawingAgent
# -------------------------------------------------

class BoardDrawingInput(BaseModel):
    equation_or_diagram: str


class BoardDrawingOutput(BaseModel):
    drawing_url: str


# -------------------------------------------------
# Agent 105 — EmotionAnalysisAgent
# -------------------------------------------------

class EmotionAnalysisInput(BaseModel):
    video_frame_urls: List[str]


class EmotionAnalysisOutput(BaseModel):
    detected_emotions: Dict[str, float]  # e.g., {"bored":0.1, "focused":0.8}
    dominant_emotion: Optional[str]


# -------------------------------------------------
# Agent 106 — EngagementDetector
# -------------------------------------------------

class EngagementDetectorInput(BaseModel):
    student_behavior_events: List[str]


class EngagementDetectorOutput(BaseModel):
    engagement_score: float


# -------------------------------------------------
# Agent 107 — VisualFeedbackAgent
# -------------------------------------------------

class VisualFeedbackInput(BaseModel):
    student_emotion: str
    lesson_state: str


class VisualFeedbackOutput(BaseModel):
    feedback_image_url: str


# -------------------------------------------------
# Agent 108 — GestureRecognitionAgent
# -------------------------------------------------

class GestureRecognitionInput(BaseModel):
    video_clip_url: str


class GestureRecognitionOutput(BaseModel):
    recognized_gestures: List[str]


# -------------------------------------------------
# Agent 109 — AudioFeedbackAgent
# -------------------------------------------------

class AudioFeedbackInput(BaseModel):
    detected_emotion: str
    student_id: Optional[str]


class AudioFeedbackOutput(BaseModel):
    audio_response_url: str


# -------------------------------------------------
# Agent 110 — InteractiveLessonOrchestrator
# -------------------------------------------------

class InteractiveLessonOrchestratorInput(BaseModel):
    multimodal_context: Dict  # combination of audio, visual, and text state


class InteractiveLessonOrchestratorOutput(BaseModel):
    orchestrated_actions: List[str]
    confidence: Optional[ConfidenceScore]

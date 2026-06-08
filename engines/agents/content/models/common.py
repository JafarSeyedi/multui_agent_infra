from datetime import datetime

from pydantic import BaseModel


class ContentVersion(BaseModel):

    content_id: str

    lesson_id: str
    version: str

    type: str                 # raw / rewritten / narrative / structured / ...
    language_level: str       # Language level
    body: str                 # Content text
    created_at: datetime

    created_by_agent: str | None

    change_summary: str | None

# --------------------------------------------------
# Generic scoring & confidence
# --------------------------------------------------

class ConfidenceScore(BaseModel):

    score: float

    explanation: str | None


class ScoreRange(BaseModel):

    min_score: float

    max_score: float

    average: float | None


# --------------------------------------------------
# Evidence / reasoning structures
# --------------------------------------------------

class Evidence(BaseModel):

    source: str | None

    description: str | None

    confidence: float | None


class ReasoningTrace(BaseModel):

    summary: str

    evidence: list[Evidence] | None


# --------------------------------------------------
# Recommendation structures
# --------------------------------------------------

class Recommendation(BaseModel):

    title: str

    description: str | None

    priority: str | None


class ActionSuggestion(BaseModel):

    action_type: str

    description: str

    expected_impact: str | None


# --------------------------------------------------
# Concept & resource references
# --------------------------------------------------

class ConceptReference(BaseModel):

    concept_id: str

    concept_name: str | None

    weight: float | None


class ResourceReference(BaseModel):

    resource_id: str

    title: str | None

    resource_type: str | None

    relevance_score: float | None


# --------------------------------------------------
# Issue & validation structures
# --------------------------------------------------

class DetectedIssue(BaseModel):

    issue_type: str

    description: str

    severity: str | None

    related_concepts: list[str] | None


# --------------------------------------------------
# Pattern detection structures
# --------------------------------------------------

class Pattern(BaseModel):

    name: str

    description: str | None

    confidence: float | None


# --------------------------------------------------
# Prediction structures
# --------------------------------------------------

class Prediction(BaseModel):

    predicted_value: float

    confidence: float | None

    explanation: str | None


# --------------------------------------------------
# Time related utilities
# --------------------------------------------------

class TimeWindow(BaseModel):

    start_time: datetime | None

    end_time: datetime | None

    duration_days: int | None

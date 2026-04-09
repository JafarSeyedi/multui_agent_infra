from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


# --------------------------------------------------
# Generic scoring & confidence
# --------------------------------------------------

class ConfidenceScore(BaseModel):

    score: float

    explanation: Optional[str]


class ScoreRange(BaseModel):

    min_score: float

    max_score: float

    average: Optional[float]


# --------------------------------------------------
# Evidence / reasoning structures
# --------------------------------------------------

class Evidence(BaseModel):

    source: Optional[str]

    description: Optional[str]

    confidence: Optional[float]


class ReasoningTrace(BaseModel):

    summary: str

    evidence: Optional[List[Evidence]]


# --------------------------------------------------
# Recommendation structures
# --------------------------------------------------

class Recommendation(BaseModel):

    title: str

    description: Optional[str]

    priority: Optional[str]


class ActionSuggestion(BaseModel):

    action_type: str

    description: str

    expected_impact: Optional[str]


# --------------------------------------------------
# Concept & resource references
# --------------------------------------------------

class ConceptReference(BaseModel):

    concept_id: str

    concept_name: Optional[str]

    weight: Optional[float]


class ResourceReference(BaseModel):

    resource_id: str

    title: Optional[str]

    resource_type: Optional[str]

    relevance_score: Optional[float]


# --------------------------------------------------
# Issue & validation structures
# --------------------------------------------------

class DetectedIssue(BaseModel):

    issue_type: str

    description: str

    severity: Optional[str]

    related_concepts: Optional[List[str]]


# --------------------------------------------------
# Pattern detection structures
# --------------------------------------------------

class Pattern(BaseModel):

    name: str

    description: Optional[str]

    confidence: Optional[float]


# --------------------------------------------------
# Prediction structures
# --------------------------------------------------

class Prediction(BaseModel):

    predicted_value: float

    confidence: Optional[float]

    explanation: Optional[str]


# --------------------------------------------------
# Time related utilities
# --------------------------------------------------

class TimeWindow(BaseModel):

    start_time: Optional[datetime]

    end_time: Optional[datetime]

    duration_days: Optional[int]

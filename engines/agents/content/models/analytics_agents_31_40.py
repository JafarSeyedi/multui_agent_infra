from pydantic import BaseModel
from ...models import AgentInput, AgentOutput
from typing import List, Optional, Dict
from datetime import datetime

from .learning_objects import (
    LearningEvent,
    AssessmentResult,
    LearningProgress,
    SkillPerformance
)


# --------------------------------------------------
# Agent 31
# Student Behavior Analyzer
# --------------------------------------------------

class StudentBehaviorAnalysisInput(AgentInput):

    student_id: str

    events: List[LearningEvent]

    time_window_days: Optional[int] = 30


class BehaviorPattern(BaseModel):

    pattern_name: str

    description: str

    confidence: float


class StudentBehaviorAnalysisOutput(AgentOutput):

    detected_patterns: List[BehaviorPattern]

    engagement_score: Optional[float]

    analyzed_at: datetime


# --------------------------------------------------
# Agent 32
# Engagement Detector
# --------------------------------------------------

class EngagementDetectionInput(AgentInput):

    student_id: str

    recent_events: List[LearningEvent]


class EngagementDetectionOutput(AgentOutput):

    engagement_level: str

    engagement_score: float

    indicators: Optional[List[str]]

    detected_at: datetime


# --------------------------------------------------
# Agent 33
# Motivation Analyzer
# --------------------------------------------------

class MotivationAnalysisInput(AgentInput):

    student_id: str

    events: List[LearningEvent]

    performance_history: Optional[List[AssessmentResult]]


class MotivationAnalysisOutput(AgentOutput):

    motivation_level: str

    key_factors: Optional[List[str]]

    recommended_interventions: Optional[List[str]]

    analyzed_at: datetime


# --------------------------------------------------
# Agent 34
# Dropout Risk Predictor
# --------------------------------------------------

class DropoutRiskPredictionInput(AgentInput):

    student_id: str

    learning_progress: LearningProgress

    recent_events: List[LearningEvent]

    assessment_results: Optional[List[AssessmentResult]]


class DropoutRiskPredictionOutput(AgentOutput):

    risk_score: float

    risk_level: str

    risk_factors: Optional[List[str]]

    recommended_actions: Optional[List[str]]

    predicted_at: datetime


# --------------------------------------------------
# Agent 35
# Study Pattern Miner
# --------------------------------------------------

class StudyPatternMiningInput(AgentInput):

    student_id: str

    events: List[LearningEvent]


class StudyPattern(BaseModel):

    pattern_name: str

    description: str

    frequency: int


class StudyPatternMiningOutput(AgentOutput):

    patterns: List[StudyPattern]

    preferred_study_times: Optional[List[str]]

    analyzed_at: datetime


# --------------------------------------------------
# Agent 36
# Performance Trend Analyzer
# --------------------------------------------------

class PerformanceTrendAnalysisInput(AgentInput):

    student_id: str

    assessment_results: List[AssessmentResult]


class PerformanceTrend(BaseModel):

    trend_direction: str

    confidence: float

    description: Optional[str]


class PerformanceTrendAnalysisOutput(AgentOutput):

    trend: PerformanceTrend

    predicted_next_score: Optional[float]

    analyzed_at: datetime


# --------------------------------------------------
# Agent 37
# Learning Outcome Predictor
# --------------------------------------------------

class LearningOutcomePredictionInput(AgentInput):

    student_id: str

    skill_performance: List[SkillPerformance]

    recent_assessments: Optional[List[AssessmentResult]]


class LearningOutcomePredictionOutput(AgentOutput):

    predicted_mastery_levels: Dict[str, float]

    predicted_course_completion_probability: Optional[float]

    generated_at: datetime


# --------------------------------------------------
# Agent 38
# Classroom Analytics Agent
# --------------------------------------------------

class ClassroomAnalyticsInput(AgentInput):

    class_id: str

    student_progress_data: List[LearningProgress]


class ClassroomAnalyticsOutput(AgentOutput):

    average_mastery: float

    struggling_students: List[str]

    top_performing_students: List[str]

    generated_at: datetime


# --------------------------------------------------
# Agent 39
# Cohort Comparison Agent
# --------------------------------------------------

class CohortComparisonInput(AgentInput):

    cohort_a_id: str

    cohort_b_id: str

    cohort_a_results: List[AssessmentResult]

    cohort_b_results: List[AssessmentResult]


class CohortComparisonOutput(AgentOutput):

    cohort_a_average: float

    cohort_b_average: float

    performance_difference: float

    interpretation: Optional[str]

    generated_at: datetime


# --------------------------------------------------
# Agent 40
# Teacher Dashboard Aggregator
# --------------------------------------------------

class TeacherDashboardAggregationInput(AgentInput):

    class_id: str

    student_progress: List[LearningProgress]

    assessment_results: Optional[List[AssessmentResult]]

    engagement_data: Optional[Dict]


class TeacherDashboardAggregationOutput(AgentOutput):

    class_average_score: Optional[float]

    engagement_overview: Optional[Dict]

    risk_students: Optional[List[str]]

    suggested_actions: Optional[List[str]]

    generated_at: datetime

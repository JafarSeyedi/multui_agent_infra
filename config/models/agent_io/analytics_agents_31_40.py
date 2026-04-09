from pydantic import BaseModel
from agents.orchestration.models import OrchestrationRequest, OrchestrationResult
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

class StudentBehaviorAnalysisInput(OrchestrationRequest):

    student_id: str

    events: List[LearningEvent]

    time_window_days: Optional[int] = 30


class BehaviorPattern(BaseModel):

    pattern_name: str

    description: str

    confidence: float


class StudentBehaviorAnalysisOutput(OrchestrationResult):

    detected_patterns: List[BehaviorPattern]

    engagement_score: Optional[float]

    analyzed_at: datetime


# --------------------------------------------------
# Agent 32
# Engagement Detector
# --------------------------------------------------

class EngagementDetectionInput(OrchestrationRequest):

    student_id: str

    recent_events: List[LearningEvent]


class EngagementDetectionOutput(OrchestrationResult):

    engagement_level: str

    engagement_score: float

    indicators: Optional[List[str]]

    detected_at: datetime


# --------------------------------------------------
# Agent 33
# Motivation Analyzer
# --------------------------------------------------

class MotivationAnalysisInput(OrchestrationRequest):

    student_id: str

    events: List[LearningEvent]

    performance_history: Optional[List[AssessmentResult]]


class MotivationAnalysisOutput(OrchestrationResult):

    motivation_level: str

    key_factors: Optional[List[str]]

    recommended_interventions: Optional[List[str]]

    analyzed_at: datetime


# --------------------------------------------------
# Agent 34
# Dropout Risk Predictor
# --------------------------------------------------

class DropoutRiskPredictionInput(OrchestrationRequest):

    student_id: str

    learning_progress: LearningProgress

    recent_events: List[LearningEvent]

    assessment_results: Optional[List[AssessmentResult]]


class DropoutRiskPredictionOutput(OrchestrationResult):

    risk_score: float

    risk_level: str

    risk_factors: Optional[List[str]]

    recommended_actions: Optional[List[str]]

    predicted_at: datetime


# --------------------------------------------------
# Agent 35
# Study Pattern Miner
# --------------------------------------------------

class StudyPatternMiningInput(OrchestrationRequest):

    student_id: str

    events: List[LearningEvent]


class StudyPattern(BaseModel):

    pattern_name: str

    description: str

    frequency: int


class StudyPatternMiningOutput(OrchestrationResult):

    patterns: List[StudyPattern]

    preferred_study_times: Optional[List[str]]

    analyzed_at: datetime


# --------------------------------------------------
# Agent 36
# Performance Trend Analyzer
# --------------------------------------------------

class PerformanceTrendAnalysisInput(OrchestrationRequest):

    student_id: str

    assessment_results: List[AssessmentResult]


class PerformanceTrend(BaseModel):

    trend_direction: str

    confidence: float

    description: Optional[str]


class PerformanceTrendAnalysisOutput(OrchestrationResult):

    trend: PerformanceTrend

    predicted_next_score: Optional[float]

    analyzed_at: datetime


# --------------------------------------------------
# Agent 37
# Learning Outcome Predictor
# --------------------------------------------------

class LearningOutcomePredictionInput(OrchestrationRequest):

    student_id: str

    skill_performance: List[SkillPerformance]

    recent_assessments: Optional[List[AssessmentResult]]


class LearningOutcomePredictionOutput(OrchestrationResult):

    predicted_mastery_levels: Dict[str, float]

    predicted_course_completion_probability: Optional[float]

    generated_at: datetime


# --------------------------------------------------
# Agent 38
# Classroom Analytics Agent
# --------------------------------------------------

class ClassroomAnalyticsInput(OrchestrationRequest):

    class_id: str

    student_progress_data: List[LearningProgress]


class ClassroomAnalyticsOutput(OrchestrationResult):

    average_mastery: float

    struggling_students: List[str]

    top_performing_students: List[str]

    generated_at: datetime


# --------------------------------------------------
# Agent 39
# Cohort Comparison Agent
# --------------------------------------------------

class CohortComparisonInput(OrchestrationRequest):

    cohort_a_id: str

    cohort_b_id: str

    cohort_a_results: List[AssessmentResult]

    cohort_b_results: List[AssessmentResult]


class CohortComparisonOutput(OrchestrationResult):

    cohort_a_average: float

    cohort_b_average: float

    performance_difference: float

    interpretation: Optional[str]

    generated_at: datetime


# --------------------------------------------------
# Agent 40
# Teacher Dashboard Aggregator
# --------------------------------------------------

class TeacherDashboardAggregationInput(OrchestrationRequest):

    class_id: str

    student_progress: List[LearningProgress]

    assessment_results: Optional[List[AssessmentResult]]

    engagement_data: Optional[Dict]


class TeacherDashboardAggregationOutput(OrchestrationResult):

    class_average_score: Optional[float]

    engagement_overview: Optional[Dict]

    risk_students: Optional[List[str]]

    suggested_actions: Optional[List[str]]

    generated_at: datetime

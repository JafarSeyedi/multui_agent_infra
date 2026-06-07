from datetime import datetime

from pydantic import BaseModel

from ...models import AgentInput
from ...models import AgentOutput
from .learning_objects import AssessmentResult
from .learning_objects import LearningEvent
from .learning_objects import LearningProgress
from .learning_objects import SkillPerformance


# --------------------------------------------------
# Agent 31
# Student Behavior Analyzer
# --------------------------------------------------

class StudentBehaviorAnalysisInput(AgentInput):

    student_id: str

    events: list[LearningEvent]

    time_window_days: int | None = 30


class BehaviorPattern(BaseModel):

    pattern_name: str

    description: str

    confidence: float


class StudentBehaviorAnalysisOutput(AgentOutput):

    detected_patterns: list[BehaviorPattern]

    engagement_score: float | None

    analyzed_at: datetime


# --------------------------------------------------
# Agent 32
# Engagement Detector
# --------------------------------------------------

class EngagementDetectionInput(AgentInput):

    student_id: str

    recent_events: list[LearningEvent]


class EngagementDetectionOutput(AgentOutput):

    engagement_level: str

    engagement_score: float

    indicators: list[str] | None

    detected_at: datetime


# --------------------------------------------------
# Agent 33
# Motivation Analyzer
# --------------------------------------------------

class MotivationAnalysisInput(AgentInput):

    student_id: str

    events: list[LearningEvent]

    performance_history: list[AssessmentResult] | None


class MotivationAnalysisOutput(AgentOutput):

    motivation_level: str

    key_factors: list[str] | None

    recommended_interventions: list[str] | None

    analyzed_at: datetime


# --------------------------------------------------
# Agent 34
# Dropout Risk Predictor
# --------------------------------------------------

class DropoutRiskPredictionInput(AgentInput):

    student_id: str

    learning_progress: LearningProgress

    recent_events: list[LearningEvent]

    assessment_results: list[AssessmentResult] | None


class DropoutRiskPredictionOutput(AgentOutput):

    risk_score: float

    risk_level: str

    risk_factors: list[str] | None

    recommended_actions: list[str] | None

    predicted_at: datetime


# --------------------------------------------------
# Agent 35
# Study Pattern Miner
# --------------------------------------------------

class StudyPatternMiningInput(AgentInput):

    student_id: str

    events: list[LearningEvent]


class StudyPattern(BaseModel):

    pattern_name: str

    description: str

    frequency: int


class StudyPatternMiningOutput(AgentOutput):

    patterns: list[StudyPattern]

    preferred_study_times: list[str] | None

    analyzed_at: datetime


# --------------------------------------------------
# Agent 36
# Performance Trend Analyzer
# --------------------------------------------------

class PerformanceTrendAnalysisInput(AgentInput):

    student_id: str

    assessment_results: list[AssessmentResult]


class PerformanceTrend(BaseModel):

    trend_direction: str

    confidence: float

    description: str | None


class PerformanceTrendAnalysisOutput(AgentOutput):

    trend: PerformanceTrend

    predicted_next_score: float | None

    analyzed_at: datetime


# --------------------------------------------------
# Agent 37
# Learning Outcome Predictor
# --------------------------------------------------

class LearningOutcomePredictionInput(AgentInput):

    student_id: str

    skill_performance: list[SkillPerformance]

    recent_assessments: list[AssessmentResult] | None


class LearningOutcomePredictionOutput(AgentOutput):

    predicted_mastery_levels: dict[str, float]

    predicted_course_completion_probability: float | None

    generated_at: datetime


# --------------------------------------------------
# Agent 38
# Classroom Analytics Agent
# --------------------------------------------------

class ClassroomAnalyticsInput(AgentInput):

    class_id: str

    student_progress_data: list[LearningProgress]


class ClassroomAnalyticsOutput(AgentOutput):

    average_mastery: float

    struggling_students: list[str]

    top_performing_students: list[str]

    generated_at: datetime


# --------------------------------------------------
# Agent 39
# Cohort Comparison Agent
# --------------------------------------------------

class CohortComparisonInput(AgentInput):

    cohort_a_id: str

    cohort_b_id: str

    cohort_a_results: list[AssessmentResult]

    cohort_b_results: list[AssessmentResult]


class CohortComparisonOutput(AgentOutput):

    cohort_a_average: float

    cohort_b_average: float

    performance_difference: float

    interpretation: str | None

    generated_at: datetime


# --------------------------------------------------
# Agent 40
# Teacher Dashboard Aggregator
# --------------------------------------------------

class TeacherDashboardAggregationInput(AgentInput):

    class_id: str

    student_progress: list[LearningProgress]

    assessment_results: list[AssessmentResult] | None

    engagement_data: dict | None


class TeacherDashboardAggregationOutput(AgentOutput):

    class_average_score: float | None

    engagement_overview: dict | None

    risk_students: list[str] | None

    suggested_actions: list[str] | None

    generated_at: datetime

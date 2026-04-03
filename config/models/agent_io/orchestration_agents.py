from pydantic import BaseModel
from typing import List, Optional, Dict

from .common import ConfidenceScore, Recommendation


# -------------------------------------------------
# Agent 61 — Learning Session Planner
# -------------------------------------------------

class LearningSessionPlannerInput(BaseModel):

    student_id: str

    learning_goals: List[str]

    available_time_minutes: Optional[int]


class LearningSessionPlannerOutput(BaseModel):

    session_plan: List[str]

    estimated_duration: Optional[int]


# -------------------------------------------------
# Agent 62 — Agent Workflow Planner
# -------------------------------------------------

class AgentWorkflowPlannerInput(BaseModel):

    task_description: str

    available_agents: List[str]


class AgentWorkflowPlannerOutput(BaseModel):

    workflow_steps: List[str]

    reasoning: Optional[str]


# -------------------------------------------------
# Agent 63 — Task Decomposer
# -------------------------------------------------

class TaskDecomposerInput(BaseModel):

    complex_task: str


class TaskDecomposerOutput(BaseModel):

    subtasks: List[str]


# -------------------------------------------------
# Agent 64 — Agent Selector
# -------------------------------------------------

class AgentSelectorInput(BaseModel):

    task: str

    candidate_agents: List[str]


class AgentSelectorOutput(BaseModel):

    selected_agent: str

    confidence: Optional[ConfidenceScore]


# -------------------------------------------------
# Agent 65 — Agent Router
# -------------------------------------------------

class AgentRouterInput(BaseModel):

    task: str

    metadata: Optional[Dict]


class AgentRouterOutput(BaseModel):

    routed_agent: str

    routing_reason: Optional[str]


# -------------------------------------------------
# Agent 66 — Context Manager
# -------------------------------------------------

class ContextManagerInput(BaseModel):

    conversation_history: List[str]

    current_task: str


class ContextManagerOutput(BaseModel):

    condensed_context: str


# -------------------------------------------------
# Agent 67 — Workflow State Tracker
# -------------------------------------------------

class WorkflowStateTrackerInput(BaseModel):

    workflow_id: str

    completed_steps: List[str]

    pending_steps: List[str]


class WorkflowStateTrackerOutput(BaseModel):

    next_step: Optional[str]

    workflow_complete: bool


# -------------------------------------------------
# Agent 68 — Failure Recovery Agent
# -------------------------------------------------

class FailureRecoveryInput(BaseModel):

    failed_step: str

    error_message: str


class FailureRecoveryOutput(BaseModel):

    recovery_action: str

    retry_possible: bool


# -------------------------------------------------
# Agent 69 — Retry Strategy Planner
# -------------------------------------------------

class RetryStrategyInput(BaseModel):

    failed_task: str

    retry_count: int


class RetryStrategyOutput(BaseModel):

    retry_strategy: str


# -------------------------------------------------
# Agent 70 — Short-Term Memory Manager
# -------------------------------------------------

class ShortTermMemoryInput(BaseModel):

    session_id: str

    new_information: str


class ShortTermMemoryOutput(BaseModel):

    updated_memory_summary: str


# -------------------------------------------------
# Agent 71 — Long-Term Memory Manager
# -------------------------------------------------

class LongTermMemoryInput(BaseModel):

    student_id: str

    knowledge_update: str


class LongTermMemoryOutput(BaseModel):

    stored: bool

    memory_reference: Optional[str]


# -------------------------------------------------
# Agent 72 — Workflow Optimizer
# -------------------------------------------------

class WorkflowOptimizerInput(BaseModel):

    workflow_steps: List[str]

    performance_metrics: Optional[Dict]


class WorkflowOptimizerOutput(BaseModel):

    optimized_steps: List[str]

    improvement_reason: Optional[str]


# -------------------------------------------------
# Agent 73 — Cost Efficiency Analyzer
# -------------------------------------------------

class CostEfficiencyAnalyzerInput(BaseModel):

    workflow_steps: List[str]

    token_usage: Optional[Dict]


class CostEfficiencyAnalyzerOutput(BaseModel):

    cost_score: float

    optimization_recommendations: Optional[List[Recommendation]]


# -------------------------------------------------
# Agent 74 — Agent Performance Monitor
# -------------------------------------------------

class AgentPerformanceMonitorInput(BaseModel):

    agent_name: str

    execution_logs: List[str]


class AgentPerformanceMonitorOutput(BaseModel):

    performance_score: float

    detected_issues: Optional[List[str]]


# -------------------------------------------------
# Agent 75 — System Health Evaluator
# -------------------------------------------------

class SystemHealthEvaluatorInput(BaseModel):

    active_agents: List[str]

    system_metrics: Optional[Dict]


class SystemHealthEvaluatorOutput(BaseModel):

    health_score: float

    issues: Optional[List[str]]

    recommendations: Optional[List[Recommendation]]

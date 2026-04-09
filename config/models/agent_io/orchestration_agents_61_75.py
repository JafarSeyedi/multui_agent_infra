from typing import List, Optional, Dict
from agents.orchestration.models import OrchestrationRequest, OrchestrationResult

from .common import ConfidenceScore, Recommendation


# -------------------------------------------------
# Agent 61 — Learning Session Planner
# -------------------------------------------------

class LearningSessionPlannerInput(OrchestrationRequest):

    student_id: str

    learning_goals: List[str]

    available_time_minutes: Optional[int]


class LearningSessionPlannerOutput(OrchestrationResult):

    session_plan: List[str]

    estimated_duration: Optional[int]


# -------------------------------------------------
# Agent 62 — Agent Workflow Planner
# -------------------------------------------------

class AgentWorkflowPlannerInput(OrchestrationRequest):

    task_description: str

    available_agents: List[str]


class AgentWorkflowPlannerOutput(OrchestrationResult):

    workflow_steps: List[str]

    reasoning: Optional[str]


# -------------------------------------------------
# Agent 63 — Task Decomposer
# -------------------------------------------------

class TaskDecomposerInput(OrchestrationRequest):

    complex_task: str


class TaskDecomposerOutput(OrchestrationResult):

    subtasks: List[str]


# -------------------------------------------------
# Agent 64 — Agent Selector
# -------------------------------------------------

class AgentSelectorInput(OrchestrationRequest):

    task: str

    candidate_agents: List[str]


class AgentSelectorOutput(OrchestrationResult):

    selected_agent: str

    confidence: Optional[ConfidenceScore]


# # -------------------------------------------------
# # Agent 65 — Agent Router
# # -------------------------------------------------

# class AgentRouterInput(OrchestrationRequest):

#     task: str

#     metadata: Optional[Dict]


# class AgentRouterOutput(OrchestrationResult):

#     routed_agent: str

#     routing_reason: Optional[str]


# -------------------------------------------------
# Agent 66 — Context Manager
# -------------------------------------------------

class ContextManagerInput(OrchestrationRequest):

    conversation_history: List[str]

    current_task: str


class ContextManagerOutput(OrchestrationResult):

    condensed_context: str


# -------------------------------------------------
# Agent 67 — Workflow State Tracker
# -------------------------------------------------

class WorkflowStateTrackerInput(OrchestrationRequest):

    workflow_id: str

    completed_steps: List[str]

    pending_steps: List[str]


class WorkflowStateTrackerOutput(OrchestrationResult):

    next_step: Optional[str]

    workflow_complete: bool


# -------------------------------------------------
# Agent 68 — Failure Recovery Agent
# -------------------------------------------------

class FailureRecoveryInput(OrchestrationRequest):

    failed_step: str

    error_message: str


class FailureRecoveryOutput(OrchestrationResult):

    recovery_action: str

    retry_possible: bool


# -------------------------------------------------
# Agent 69 — Retry Strategy Planner
# -------------------------------------------------

class RetryStrategyInput(OrchestrationRequest):

    failed_task: str

    retry_count: int


class RetryStrategyOutput(OrchestrationResult):

    retry_strategy: str


# -------------------------------------------------
# Agent 70 — Short-Term Memory Manager
# -------------------------------------------------

class ShortTermMemoryInput(OrchestrationRequest):

    session_id: str

    new_information: str


class ShortTermMemoryOutput(OrchestrationResult):

    updated_memory_summary: str


# -------------------------------------------------
# Agent 71 — Long-Term Memory Manager
# -------------------------------------------------

class LongTermMemoryInput(OrchestrationRequest):

    student_id: str

    knowledge_update: str


class LongTermMemoryOutput(OrchestrationResult):

    stored: bool

    memory_reference: Optional[str]


# -------------------------------------------------
# Agent 72 — Workflow Optimizer
# -------------------------------------------------

class WorkflowOptimizerInput(OrchestrationRequest):

    workflow_steps: List[str]

    performance_metrics: Optional[Dict]


class WorkflowOptimizerOutput(OrchestrationResult):

    optimized_steps: List[str]

    improvement_reason: Optional[str]


# -------------------------------------------------
# Agent 73 — Cost Efficiency Analyzer
# -------------------------------------------------

class CostEfficiencyAnalyzerInput(OrchestrationRequest):

    workflow_steps: List[str]

    token_usage: Optional[Dict]


class CostEfficiencyAnalyzerOutput(OrchestrationResult):

    cost_score: float

    optimization_recommendations: Optional[List[Recommendation]]


# -------------------------------------------------
# Agent 74 — Agent Performance Monitor
# -------------------------------------------------

class AgentPerformanceMonitorInput(OrchestrationRequest):

    agent_name: str

    execution_logs: List[str]


class AgentPerformanceMonitorOutput(OrchestrationResult):

    performance_score: float

    detected_issues: Optional[List[str]]


# -------------------------------------------------
# Agent 75 — System Health Evaluator
# -------------------------------------------------

class SystemHealthEvaluatorInput(OrchestrationRequest):

    active_agents: List[str]

    system_metrics: Optional[Dict]


class SystemHealthEvaluatorOutput(OrchestrationResult):

    health_score: float

    issues: Optional[List[str]]

    recommendations: Optional[List[Recommendation]]

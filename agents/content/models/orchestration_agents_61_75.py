from typing import List, Optional, Dict
from agents.base_agents.models import AgentInput, AgentOutput

from .common import ConfidenceScore, Recommendation


# -------------------------------------------------
# Agent 61 — Learning Session Planner
# -------------------------------------------------

class LearningSessionPlannerInput(AgentInput):

    student_id: str

    learning_goals: List[str]

    available_time_minutes: Optional[int]


class LearningSessionPlannerOutput(AgentOutput):

    session_plan: List[str]

    estimated_duration: Optional[int]


# -------------------------------------------------
# Agent 62 — Agent Workflow Planner
# -------------------------------------------------

class AgentWorkflowPlannerInput(AgentInput):

    task_description: str

    available_agents: List[str]


class AgentWorkflowPlannerOutput(AgentOutput):

    workflow_steps: List[str]

    reasoning: Optional[str]


# -------------------------------------------------
# Agent 63 — Task Decomposer
# -------------------------------------------------

class TaskDecomposerInput(AgentInput):

    complex_task: str


class TaskDecomposerOutput(AgentOutput):

    subtasks: List[str]


# -------------------------------------------------
# Agent 64 — Agent Selector
# -------------------------------------------------

class AgentSelectorInput(AgentInput):

    task: str

    candidate_agents: List[str]


class AgentSelectorOutput(AgentOutput):

    selected_agent: str

    confidence: Optional[ConfidenceScore]


# # -------------------------------------------------
# # Agent 65 — Agent Router
# # -------------------------------------------------

# class AgentRouterInput(AgentInput):

#     task: str

#     metadata: Optional[Dict]


# class AgentRouterOutput(AgentOutput):

#     routed_agent: str

#     routing_reason: Optional[str]


# -------------------------------------------------
# Agent 66 — Context Manager
# -------------------------------------------------

class ContextManagerInput(AgentInput):

    conversation_history: List[str]

    current_task: str


class ContextManagerOutput(AgentOutput):

    condensed_context: str


# -------------------------------------------------
# Agent 67 — Workflow State Tracker
# -------------------------------------------------

class WorkflowStateTrackerInput(AgentInput):

    workflow_id: str

    completed_steps: List[str]

    pending_steps: List[str]


class WorkflowStateTrackerOutput(AgentOutput):

    next_step: Optional[str]

    workflow_complete: bool


# -------------------------------------------------
# Agent 68 — Failure Recovery Agent
# -------------------------------------------------

class FailureRecoveryInput(AgentInput):

    failed_step: str

    error_message: str


class FailureRecoveryOutput(AgentOutput):

    recovery_action: str

    retry_possible: bool


# -------------------------------------------------
# Agent 69 — Retry Strategy Planner
# -------------------------------------------------

class RetryStrategyInput(AgentInput):

    failed_task: str

    retry_count: int


class RetryStrategyOutput(AgentOutput):

    retry_strategy: str


# -------------------------------------------------
# Agent 70 — Short-Term Memory Manager
# -------------------------------------------------

class ShortTermMemoryInput(AgentInput):

    session_id: str

    new_information: str


class ShortTermMemoryOutput(AgentOutput):

    updated_memory_summary: str


# -------------------------------------------------
# Agent 71 — Long-Term Memory Manager
# -------------------------------------------------

class LongTermMemoryInput(AgentInput):

    student_id: str

    knowledge_update: str


class LongTermMemoryOutput(AgentOutput):

    stored: bool

    memory_reference: Optional[str]


# -------------------------------------------------
# Agent 72 — Workflow Optimizer
# -------------------------------------------------

class WorkflowOptimizerInput(AgentInput):

    workflow_steps: List[str]

    performance_metrics: Optional[Dict]


class WorkflowOptimizerOutput(AgentOutput):

    optimized_steps: List[str]

    improvement_reason: Optional[str]


# -------------------------------------------------
# Agent 73 — Cost Efficiency Analyzer
# -------------------------------------------------

class CostEfficiencyAnalyzerInput(AgentInput):

    workflow_steps: List[str]

    token_usage: Optional[Dict]


class CostEfficiencyAnalyzerOutput(AgentOutput):

    cost_score: float

    optimization_recommendations: Optional[List[Recommendation]]


# -------------------------------------------------
# Agent 74 — Agent Performance Monitor
# -------------------------------------------------

class AgentPerformanceMonitorInput(AgentInput):

    agent_name: str

    execution_logs: List[str]


class AgentPerformanceMonitorOutput(AgentOutput):

    performance_score: float

    detected_issues: Optional[List[str]]


# -------------------------------------------------
# Agent 75 — System Health Evaluator
# -------------------------------------------------

class SystemHealthEvaluatorInput(AgentInput):

    active_agents: List[str]

    system_metrics: Optional[Dict]


class SystemHealthEvaluatorOutput(AgentOutput):

    health_score: float

    issues: Optional[List[str]]

    recommendations: Optional[List[Recommendation]]

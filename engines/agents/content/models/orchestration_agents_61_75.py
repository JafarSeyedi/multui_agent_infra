from ...models import AgentInput
from ...models import AgentOutput
from .common import ConfidenceScore
from .common import Recommendation


# -------------------------------------------------
# Agent 61 — Learning Session Planner
# -------------------------------------------------

class LearningSessionPlannerInput(AgentInput):

    student_id: str

    learning_goals: list[str]

    available_time_minutes: int | None


class LearningSessionPlannerOutput(AgentOutput):

    session_plan: list[str]

    estimated_duration: int | None


# -------------------------------------------------
# Agent 62 — Agent Workflow Planner
# -------------------------------------------------

class AgentWorkflowPlannerInput(AgentInput):

    task_description: str

    available_agents: list[str]


class AgentWorkflowPlannerOutput(AgentOutput):

    workflow_steps: list[str]

    reasoning: str | None


# -------------------------------------------------
# Agent 63 — Task Decomposer
# -------------------------------------------------

class TaskDecomposerInput(AgentInput):

    complex_task: str


class TaskDecomposerOutput(AgentOutput):

    subtasks: list[str]


# -------------------------------------------------
# Agent 64 — Agent Selector
# -------------------------------------------------

class AgentSelectorInput(AgentInput):

    task: str

    candidate_agents: list[str]


class AgentSelectorOutput(AgentOutput):

    selected_agent: str

    confidence: ConfidenceScore | None


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

    conversation_history: list[str]

    current_task: str


class ContextManagerOutput(AgentOutput):

    condensed_context: str


# -------------------------------------------------
# Agent 67 — Workflow State Tracker
# -------------------------------------------------

class WorkflowStateTrackerInput(AgentInput):

    workflow_id: str

    completed_steps: list[str]

    pending_steps: list[str]


class WorkflowStateTrackerOutput(AgentOutput):

    next_step: str | None

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

    memory_reference: str | None


# -------------------------------------------------
# Agent 72 — Workflow Optimizer
# -------------------------------------------------

class WorkflowOptimizerInput(AgentInput):

    workflow_steps: list[str]

    performance_metrics: dict | None


class WorkflowOptimizerOutput(AgentOutput):

    optimized_steps: list[str]

    improvement_reason: str | None


# -------------------------------------------------
# Agent 73 — Cost Efficiency Analyzer
# -------------------------------------------------

class CostEfficiencyAnalyzerInput(AgentInput):

    workflow_steps: list[str]

    token_usage: dict | None


class CostEfficiencyAnalyzerOutput(AgentOutput):

    cost_score: float

    optimization_recommendations: list[Recommendation] | None


# -------------------------------------------------
# Agent 74 — Agent Performance Monitor
# -------------------------------------------------

class AgentPerformanceMonitorInput(AgentInput):

    agent_name: str

    execution_logs: list[str]


class AgentPerformanceMonitorOutput(AgentOutput):

    performance_score: float

    detected_issues: list[str] | None


# -------------------------------------------------
# Agent 75 — System Health Evaluator
# -------------------------------------------------

class SystemHealthEvaluatorInput(AgentInput):

    active_agents: list[str]

    system_metrics: dict | None


class SystemHealthEvaluatorOutput(AgentOutput):

    health_score: float

    issues: list[str] | None

    recommendations: list[Recommendation] | None

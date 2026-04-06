# agents/orchestration/interaction/sequential_strategy.py

from datetime import datetime
from typing import List, Dict, Any

from agents.orchestration.models import (
    OrchestrationRequest,
    OrchestrationResult,
    OrchestrationExecution,
    PipelineStep,
    AgentMessage,
)
from agents.orchestration.interaction.base_strategy import InteractionStrategy


class SequentialStrategy(InteractionStrategy):

    async def execute(self, request: OrchestrationRequest) -> OrchestrationResult:
        started_at = datetime.utcnow()
        shared_context = dict(request.shared_context)
        steps: List[PipelineStep] = []
        executions: List[OrchestrationExecution] = []
        messages: List[AgentMessage] = []

        for sequence, task in enumerate(request.tasks, start=1):
            await self._execute_task(
                task, request.workflow_id, sequence,
                shared_context, steps, executions, messages,
            )

        return OrchestrationResult(
            workflow_id=request.workflow_id,
            scenario=request.scenario,
            backend_used="native",
            status=self._aggregate_status(executions),
            started_at=started_at,
            completed_at=datetime.utcnow(),
            shared_context=shared_context,
            steps=steps,
            executions=executions,
            messages=messages,
            notes=[],
        )

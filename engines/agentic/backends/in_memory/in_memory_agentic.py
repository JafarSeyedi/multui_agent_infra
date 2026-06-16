# engines/agentic/backends/in_memory/in_memory_agentic.py
from __future__ import annotations

import uuid
from typing import Any

from ...models.agentic_models import WorkflowRun
from ...plugin import IAgentOrchestrator, IAgentDelegate


class InMemoryAgentOrchestrator(IAgentOrchestrator):
    name = "in_memory"

    def __init__(self) -> None:
        self._runs: dict[str, WorkflowRun] = {}

    async def run_workflow(self, workflow: str, inputs: dict[str, Any]) -> dict[str, Any]:
        wf_id = str(uuid.uuid4())
        run = WorkflowRun(workflow_id=wf_id, workflow=workflow, inputs=inputs, status="completed")
        self._runs[wf_id] = run
        return {"workflow_id": wf_id, "status": "completed", "outputs": {"result": f"ran {workflow}"}}

    async def get_status(self, workflow_id: str) -> str:
        run = self._runs.get(workflow_id)
        return run.status if run else "unknown"


class InMemoryAgentDelegate(IAgentDelegate):
    name = "in_memory"

    def __init__(self) -> None:
        self._delegations: list[dict[str, Any]] = []

    async def delegate(self, task: str, context: dict[str, Any]) -> dict[str, Any]:
        self._delegations.append({"task": task, "context": context})
        return {"status": "delegated", "task": task, "result": f"handled {task}"}

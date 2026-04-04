from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from config.models.system.interaction_models import AgentMessage, PipelineStep

from .models import OrchestrationExecution, OrchestrationRequest, OrchestrationResult, OrchestrationTask


class NativeOrchestrationBackend:
    def __init__(self, registry, message_bus=None):
        self.registry = registry
        self.message_bus = message_bus

    async def run(self, request: OrchestrationRequest) -> OrchestrationResult:
        started_at = datetime.utcnow()
        shared_context = dict(request.shared_context)
        steps: List[PipelineStep] = []
        executions: List[OrchestrationExecution] = []
        messages: List[AgentMessage] = []
        notes: List[str] = []

        if request.scenario == "sequential":
            await self._run_sequential(request, shared_context, steps, executions, messages)
        elif request.scenario == "broadcast":
            await self._run_broadcast(request, shared_context, steps, executions, messages)
        elif request.scenario == "round_robin":
            await self._run_round_robin(request, shared_context, steps, executions, messages)
        elif request.scenario == "selector":
            await self._run_selector(request, shared_context, steps, executions, messages, notes)
        elif request.scenario == "group_chat":
            notes.append("Native backend emulates group chat as round-robin structured execution.")
            await self._run_round_robin(request, shared_context, steps, executions, messages)
        else:
            raise ValueError(f"Unsupported orchestration scenario: {request.scenario}")

        status = self._aggregate_status(executions)
        return OrchestrationResult(
            workflow_id=request.workflow_id,
            scenario=request.scenario,
            backend_used="native",
            status=status,
            started_at=started_at,
            completed_at=datetime.utcnow(),
            shared_context=shared_context,
            steps=steps,
            executions=executions,
            messages=messages,
            notes=notes,
        )

    async def _run_sequential(self, request, shared_context, steps, executions, messages):
        for sequence, task in enumerate(request.tasks, start=1):
            await self._execute_task(task, request.workflow_id, sequence, shared_context, steps, executions, messages)

    async def _run_broadcast(self, request, shared_context, steps, executions, messages):
        broadcast_payload = dict(shared_context)
        if request.tasks:
            broadcast_payload.update(request.tasks[0].input_payload)
        for sequence, task in enumerate(request.tasks, start=1):
            broadcast_task = OrchestrationTask(
                agent_name=task.agent_name,
                input_payload=dict(broadcast_payload),
                task_id=task.task_id,
                description=task.description,
            )
            await self._execute_task(broadcast_task, request.workflow_id, sequence, shared_context, steps, executions, messages)

    async def _run_round_robin(self, request, shared_context, steps, executions, messages):
        rounds = max(1, request.max_rounds)
        sequence = 1
        latest_output: Dict[str, Any] = {}
        for round_index in range(rounds):
            shared_context["round_index"] = round_index
            for task in request.tasks:
                payload = dict(task.input_payload)
                if latest_output:
                    payload.setdefault("previous_output", latest_output)
                result = await self._execute_task(
                    OrchestrationTask(
                        agent_name=task.agent_name,
                        input_payload=payload,
                        task_id=task.task_id,
                        description=task.description,
                    ),
                    request.workflow_id,
                    sequence,
                    shared_context,
                    steps,
                    executions,
                    messages,
                )
                if result.output_payload:
                    latest_output = result.output_payload
                    shared_context[f"last_output:{task.agent_name}"] = result.output_payload
                sequence += 1

    async def _run_selector(self, request, shared_context, steps, executions, messages, notes):
        selected_agent = request.selected_agent or shared_context.get("selected_agent")
        selected_task = None
        if selected_agent:
            for task in request.tasks:
                if task.agent_name == selected_agent:
                    selected_task = task
                    break
        if selected_task is None and request.tasks:
            selected_task = request.tasks[0]
            notes.append(f"No selected agent provided; defaulted to {selected_task.agent_name}.")
        if selected_task is None:
            notes.append("Selector scenario received no tasks.")
            return
        await self._execute_task(selected_task, request.workflow_id, 1, shared_context, steps, executions, messages)

    async def _execute_task(self, task, workflow_id, sequence, shared_context, steps, executions, messages):
        task_id = task.task_id or f"{workflow_id}:{sequence}:{task.agent_name}:{uuid.uuid4().hex[:8]}"
        step = PipelineStep(
            step_id=task_id,
            pipeline_name=workflow_id,
            step_name=task.agent_name,
            sequence=sequence,
            status="running",
            metadata={"description": task.description or "", "agent_name": task.agent_name},
            started_at=datetime.utcnow(),
        )
        steps.append(step)

        message = AgentMessage(
            message_id=str(uuid.uuid4()),
            sender="OrchestratorAgent",
            recipient=task.agent_name,
            message_type="task_dispatch",
            payload={"task_id": task_id, "input_payload": task.input_payload, "shared_context": shared_context},
        )
        messages.append(message)
        if self.message_bus is not None:
            await self.message_bus.publish(message)

        try:
            payload = dict(task.input_payload)
            payload.setdefault("workflow_context", dict(shared_context))
            output_model = await self.registry.run(task.agent_name, payload)
            if hasattr(output_model, "model_dump"):
                output_payload = output_model.model_dump()
            else:
                output_payload = output_model.dict()
            step.status = "completed"
            step.completed_at = datetime.utcnow()
            execution = OrchestrationExecution(
                task_id=task_id,
                agent_name=task.agent_name,
                status="success",
                output_payload=output_payload,
            )
            executions.append(execution)
            shared_context[f"task:{task.agent_name}"] = output_payload
            return execution
        except Exception as exc:
            step.status = "failed"
            step.completed_at = datetime.utcnow()
            execution = OrchestrationExecution(
                task_id=task_id,
                agent_name=task.agent_name,
                status="failure",
                error_message=str(exc),
            )
            executions.append(execution)
            return execution

    def _aggregate_status(self, executions: List[OrchestrationExecution]) -> str:
        if not executions:
            return "failure"
        statuses = {item.status for item in executions}
        if statuses == {"success"}:
            return "success"
        if "success" in statuses:
            return "partial_success"
        return "failure"


class AutoGenOrchestrationBackend:
    """AutoGen wrapper that preserves our orchestration contract.

    When AutoGen is unavailable, this backend transparently falls back to the native
    backend and records the reason in the result notes.
    """

    def __init__(self, registry, message_bus=None):
        self.registry = registry
        self.message_bus = message_bus
        self.native_backend = NativeOrchestrationBackend(registry=registry, message_bus=message_bus)

    def is_available(self) -> bool:
        try:
            import autogen  # noqa: F401
            return True
        except Exception:
            return False

    async def run(self, request: OrchestrationRequest) -> OrchestrationResult:
        if not self.is_available():
            result = await self.native_backend.run(request)
            result.backend_used = "native"
            result.notes.append("AutoGen requested but package is not installed; native backend used instead.")
            return result

        # Structured educational agents in this repo are typed execution units, not raw chat agents.
        # So even when AutoGen is installed, we keep our orchestration contract and use the native
        # executor for deterministic task execution while surfacing AutoGen readiness for future
        # group-chat / tool-agent scenarios.
        result = await self.native_backend.run(request)
        result.backend_used = "autogen-wrapper"
        result.notes.append(
            "AutoGen is available; this wrapper keeps the repo's typed orchestration contract and can be extended to GroupChat or routed conversation scenarios."
        )
        return result

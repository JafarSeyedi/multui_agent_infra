# agents/orchestration/interaction/manager_strategy.py
from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence

from agents.buses.base import MessageBus
from agents.orchestration.models import AgentMessage
from agents.orchestration.models import (
    OrchestrationRequest,
    OrchestrationResult,
    TaskDefinition,
    TaskResult,
)
from .base_strategy import InteractionStrategy


class ManagerStrategy(InteractionStrategy):
    """
    الگوی Manager + Workers: یک Supervisor تصمیم می‌گیرد که کدام عامل‌ها چه ورودی‌ای اجرا کنند،
    خروجی آن‌ها را اعتبارسنجی/تجمیع می‌کند، و نتیجه نهایی یا خطا را بازمی‌گرداند.
    """

    scenario_name = "manager"

    def __init__(
        self,
        agent_registry,
        message_bus: Optional[MessageBus] = None,
        storage=None,
        validation_agent: str | None = None,
        aggregator_agent: str | None = None,
    ):
        super().__init__(agent_registry, message_bus, storage)
        self.validation_agent = validation_agent
        self.aggregator_agent = aggregator_agent

    async def execute(self, request: OrchestrationRequest) -> OrchestrationResult:
        shared_context: Dict[str, Any] = dict(request.context)
        results: List[TaskResult] = []

        worker_tasks: Sequence[TaskDefinition] = request.tasks
        if not worker_tasks:
            return OrchestrationResult(
                results=[],
                success=True,
                final_context=shared_context,
                metadata={"note": "manager strategy received no worker tasks"},
            )

        for task in worker_tasks:
            payload = dict(task.payload)
            payload.setdefault("shared_context", dict(shared_context))
            task_id = task.task_id or f"manager:{task.agent_name}"
            try:
                output_model = await self.agent_registry.execute(task.agent_name, payload)
                output_payload = self._normalize_output(output_model)

                shared_context.setdefault("worker_outputs", {})[task.agent_name] = output_payload

                results.append(
                    TaskResult(
                        task_id=task_id,
                        agent_name=task.agent_name,
                        success=True,
                        output=output_payload,
                    )
                )

                await self._publish_turn_message(task.agent_name, task_id, payload, output_payload)

            except Exception as exc:  # noqa: BLE001
                error_message = str(exc)
                results.append(
                    TaskResult(
                        task_id=task_id,
                        agent_name=task.agent_name,
                        success=False,
                        error=error_message,
                    )
                )
                shared_context.setdefault("errors", []).append({task.agent_name: error_message})

        if self.validation_agent:
            await self._run_validation(shared_context, results)

        final_payload = await self._aggregate(shared_context, results)
        overall_success = all(result.success for result in results)

        return OrchestrationResult(
            results=results,
            success=overall_success,
            final_context={**shared_context, "final_payload": final_payload},
            metadata={
                "validation_agent": self.validation_agent,
                "aggregator_agent": self.aggregator_agent,
            },
        )

    async def _run_validation(self, shared_context: Dict[str, Any], results: List[TaskResult]) -> None:
        try:
            payload = {
                "worker_results": [res.dict() for res in results],
                "shared_context": dict(shared_context),
            }
            validation_output = await self.agent_registry.execute(self.validation_agent, payload)
            shared_context["validation"] = self._normalize_output(validation_output)
        except Exception as exc:  # noqa: BLE001
            shared_context.setdefault("validation_errors", []).append(str(exc))

    async def _aggregate(self, shared_context: Dict[str, Any], results: List[TaskResult]) -> Any:
        if self.aggregator_agent:
            payload = {
                "worker_results": [res.dict() for res in results],
                "shared_context": dict(shared_context),
            }
            try:
                output = await self.agent_registry.execute(self.aggregator_agent, payload)
                aggregated_payload = self._normalize_output(output)
                shared_context["aggregated_result"] = aggregated_payload
                return aggregated_payload
            except Exception as exc:  # noqa: BLE001
                shared_context.setdefault("aggregation_errors", []).append(str(exc))
                return {"error": str(exc)}
        return shared_context.get("worker_outputs", {})

    async def _publish_turn_message(
        self, agent_name: str, task_id: str, input_payload: Dict[str, Any], output_payload: Any
    ) -> None:
        # ✅ استفاده از _emit
        await self._emit(
            message_type="task_result",
            payload={
                "task_id": task_id,
                "input": input_payload,
                "output": output_payload,
            },
            sender="ManagerStrategy",
            recipient=agent_name,
            message_id=f"manager-{task_id}",
        )

    @staticmethod
    def _normalize_output(output_model: Any) -> Any:
        if hasattr(output_model, "model_dump"):
            return output_model.model_dump()
        if hasattr(output_model, "dict"):
            return output_model.dict()
        if isinstance(output_model, dict):
            return output_model
        return {"value": output_model}

# agents/orchestration/interaction/ensemble_strategy.py
from __future__ import annotations

from collections import Counter
from typing import Any, Dict, List, Optional

from agents.buses.base import MessageBus
from agents.orchestration.models import (
    OrchestrationRequest,
    OrchestrationResult,
    TaskResult,
    AgentMessage
)
from .base_strategy import InteractionStrategy


class EnsembleStrategy(InteractionStrategy):
    """
    استراتژی رای‌گیری/Ensemble: پاسخ‌های عوامل را جمع‌آوری می‌کند و با استفاده از
    یک قاعده‌ی رای‌گیری یا aggregator پاسخ نهایی را ارائه می‌دهد.
    """

    scenario_name = "ensemble"

    def __init__(self, agent_registry, message_bus: Optional[MessageBus] = None, storage = None, vote_key: str = "final_answer", aggregator_agent: str | None = None):
        super().__init__(agent_registry, message_bus, storage)
        self.vote_key = vote_key
        self.aggregator_agent = aggregator_agent

    async def execute(self, request: OrchestrationRequest) -> OrchestrationResult:
        shared_context: Dict[str, Any] = dict(request.context)
        votes: List[Any] = []
        results: List[TaskResult] = []

        for task in request.tasks:
            payload = dict(task.payload)
            payload.setdefault("shared_context", dict(shared_context))
            task_id = task.task_id or f"ensemble:{task.agent_name}"
            try:
                output_model = await self.agent_registry.execute(task.agent_name, payload)
                normalized = self._normalize_output(output_model)
                vote_value = normalized.get(self.vote_key, normalized) if isinstance(normalized, dict) else normalized
                votes.append(vote_value)
                shared_context.setdefault("votes", []).append({"agent": task.agent_name, "vote": vote_value})

                results.append(
                    TaskResult(
                        task_id=task_id,
                        agent_name=task.agent_name,
                        success=True,
                        output=normalized,
                    )
                )
                await self._publish_vote(task.agent_name, task_id, vote_value)

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

        final_vote = await self._aggregate_votes(votes, shared_context)
        overall_success = all(result.success for result in results)

        return OrchestrationResult(
            results=results,
            success=overall_success,
            final_context={**shared_context, "ensemble_vote": final_vote},
            metadata={"vote_key": self.vote_key, "aggregator_agent": self.aggregator_agent},
        )

    async def _aggregate_votes(self, votes: List[Any], shared_context: Dict[str, Any]) -> Any:
        if self.aggregator_agent:
            try:
                payload = {"votes": votes, "shared_context": dict(shared_context)}
                output_model = await self.agent_registry.execute(self.aggregator_agent, payload)
                aggregated = self._normalize_output(output_model)
                shared_context["aggregator_output"] = aggregated
                return aggregated
            except Exception as exc:  # noqa: BLE001
                shared_context.setdefault("aggregation_errors", []).append(str(exc))
                return {"error": str(exc)}

        counter = Counter(votes)
        if not counter:
            return None
        most_common = counter.most_common(1)[0][0]
        shared_context["vote_summary"] = counter
        return most_common

    async def _publish_vote(self, agent_name: str, task_id: str, vote: Any) -> None:
        if self.message_bus is None:
            return
        await self.message_bus.publish(
            AgentMessage(
                message_id=f"ensemble-{task_id}",
                sender="EnsembleStrategy",
                recipient=agent_name,
                message_type="vote",
                payload={"task_id": task_id, "vote": vote},
            )
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

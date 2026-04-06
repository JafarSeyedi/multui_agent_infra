# agents/orchestration/interaction/debate_strategy.py
from typing import Any, Dict, List, Optional

from .base_strategy import InteractionStrategy
from ..models import (
    OrchestrationRequest,
    OrchestrationResult,
    TaskResult,
)


class DebateStrategy(InteractionStrategy):
    async def execute(self, request: OrchestrationRequest) -> OrchestrationResult:
        context: Dict[str, Any] = dict(request.context or {})
        tasks = request.tasks or []

        if len(tasks) < 2:
            raise ValueError("DebateStrategy requires at least two tasks (proposer & critic).")

        proposer_task, critic_task = tasks[0], tasks[1]
        proposer = self.registry.get(proposer_task.agent_name)
        critic = self.registry.get(critic_task.agent_name)
        if proposer is None or critic is None:
            raise ValueError("Required debate agents are not registered.")

        max_rounds = int(request.metadata.get("max_rounds", 5))
        history: List[Dict[str, Any]] = []
        results: List[TaskResult] = []
        current_answer: Optional[Any] = None
        approved_round: Optional[int] = None

        for round_id in range(1, max_rounds + 1):
            if self.message_bus:
                await self.message_bus.publish({"event": "debate_round_started", "round": round_id})

            try:
                proposer_output = await proposer.execute(
                    {**proposer_task.payload, "context": dict(context), "history": history, "round": round_id}
                )
                current_answer = proposer_output
                results.append(
                    TaskResult(
                        task_id=f"proposer_round_{round_id}",
                        agent_name=proposer_task.agent_name,
                        success=True,
                        output=proposer_output,
                    )
                )
            except Exception as exc:
                results.append(
                    TaskResult(
                        task_id=f"proposer_round_{round_id}",
                        agent_name=proposer_task.agent_name,
                        success=False,
                        error=str(exc),
                    )
                )
                break

            try:
                critic_output = await critic.execute(
                    {
                        **critic_task.payload,
                        "context": dict(context),
                        "answer": current_answer,
                        "history": history,
                        "round": round_id,
                    }
                )
                results.append(
                    TaskResult(
                        task_id=f"critic_round_{round_id}",
                        agent_name=critic_task.agent_name,
                        success=True,
                        output=critic_output,
                    )
                )
            except Exception as exc:
                results.append(
                    TaskResult(
                        task_id=f"critic_round_{round_id}",
                        agent_name=critic_task.agent_name,
                        success=False,
                        error=str(exc),
                    )
                )
                break

            history.append({"round": round_id, "answer": current_answer, "critique": critic_output})
            if isinstance(critic_output, dict) and critic_output.get("approved") is True:
                approved_round = round_id
                if self.message_bus:
                    await self.message_bus.publish({"event": "debate_finished", "round": round_id})
                break

            if self.message_bus:
                await self.message_bus.publish({"event": "debate_round_completed", "round": round_id})

        context["debate_history"] = history
        context["final_answer"] = current_answer

        return OrchestrationResult(
            success=True,
            results=results,
            final_context=context,
            metadata={"rounds_executed": len(history), "approved_round": approved_round},
        )

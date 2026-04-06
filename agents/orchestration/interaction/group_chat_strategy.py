# agents/orchestration/interaction/group_chat_strategy.py
from __future__ import annotations

from typing import Any, Dict, List, Optional

from .base_strategy import InteractionStrategy
from agents.orchestration.models import (
    OrchestrationRequest,
    OrchestrationResult,
    TaskDefinition,
    TaskResult,
)


class GroupChatStrategy(InteractionStrategy):
    scenario = "group_chat"

    def __init__(self, registry, message_bus: MessageBus, storage, default_max_rounds: int = 8):
        super().__init__(registry, message_bus, storage)
        self.default_max_rounds = max(1, default_max_rounds)

    async def execute(self, request: OrchestrationRequest) -> OrchestrationResult:
        context: Dict[str, Any] = dict(request.context or {})
        metadata: Dict[str, Any] = dict(request.metadata or {})
        messages: List[Dict[str, Any]] = self._init_messages(context)

        participants = self._resolve_participants(request.tasks, metadata)
        if not participants:
            return OrchestrationResult(success=False, results=[], final_context=context)

        max_rounds = int(metadata.get("max_rounds", self.default_max_rounds))
        stop_on_done = bool(metadata.get("stop_on_done", True))
        stop_on_role = metadata.get("stop_on_role")
        results: List[TaskResult] = []
        speaker_index = 0
        finished = False
        failure_reason: Optional[str] = None

        await self._publish_event(
            "group_chat_started",
            {
                "conversation_id": context.get("conversation_id"),
                "participant_ids": [p.task_id for p in participants],
                "max_rounds": max_rounds,
            },
        )

        for current_round in range(1, max_rounds + 1):
            if finished:
                break
            speaker = participants[speaker_index]
            speaker_index = (speaker_index + 1) % len(participants)

            agent = self.registry.get(speaker.agent_name)
            if agent is None:
                failure_reason = f"Agent '{speaker.agent_name}' missing for task {speaker.task_id}."
                await self._publish_event(
                    "group_chat_turn_failed",
                    {"round": current_round, "task_id": speaker.task_id, "error": failure_reason},
                )
                break

            await self._publish_event(
                "group_chat_turn_started",
                {"round": current_round, "task_id": speaker.task_id, "agent_name": speaker.agent_name},
            )

            payload = {
                **(speaker.payload or {}),
                "context": dict(context),
                "messages": list(messages),
            }
            payload.setdefault("role", payload.get("display_name", speaker.task_id))

            try:
                output = await agent.execute(payload)
                task_result = TaskResult(
                    task_id=speaker.task_id,
                    agent_name=speaker.agent_name,
                    success=True,
                    output=output,
                )
                results.append(task_result)

                context_update = self._extract_context_update(output)
                if context_update:
                    context.update(context_update)

                new_message = self._extract_message(output, payload)
                if new_message:
                    messages.append(new_message)

                done_flag = self._extract_done_flag(output)
                if stop_on_role and new_message and new_message.get("role") == stop_on_role:
                    done_flag = True

                if stop_on_done and done_flag:
                    finished = True
                    await self._publish_event(
                        "group_chat_finished",
                        {
                            "conversation_id": context.get("conversation_id"),
                            "round": current_round,
                            "reason": "done",
                        },
                    )
                else:
                    await self._publish_event(
                        "group_chat_turn_completed",
                        {
                            "round": current_round,
                            "task_id": speaker.task_id,
                            "agent_name": speaker.agent_name,
                        },
                    )

            except Exception as exc:
                error_msg = str(exc)
                results.append(
                    TaskResult(task_id=speaker.task_id, agent_name=speaker.agent_name, success=False, error=error_msg)
                )
                await self._publish_event(
                    "group_chat_turn_failed",
                    {"round": current_round, "task_id": speaker.task_id, "error": error_msg},
                )
                failure_reason = error_msg
                finished = True

        context["messages"] = messages
        success = failure_reason is None
        final_metadata = {
            "rounds_executed": len(messages),
            "failure_reason": failure_reason,
            "participants": [p.task_id for p in participants],
        }
        return OrchestrationResult(success=success, results=results, final_context=context, metadata=final_metadata)

    def _init_messages(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        messages = context.get("messages")
        if isinstance(messages, list):
            return list(messages)
        user_message = context.get("user_message")
        if isinstance(user_message, str) and user_message.strip():
            return [{"role": "user", "sender": "user", "content": user_message.strip()}]
        return []

    def _resolve_participants(self, tasks: List[TaskDefinition], metadata: Dict[str, Any]) -> List[TaskDefinition]:
        if not tasks:
            return []
        by_id = {t.task_id: t for t in tasks if t.task_id}
        order = metadata.get("participant_order")
        if isinstance(order, list):
            ordered = [by_id[tid] for tid in order if tid in by_id]
            if ordered:
                return ordered
        return list(tasks)

    def _extract_message(self, output: Any, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        sender = payload.get("sender", payload.get("role", "assistant"))
        if isinstance(output, dict):
            content = output.get("message") or output.get("content")
            if not content:
                return None
            return {
                "role": output.get("role", payload.get("role", "assistant")),
                "sender": sender,
                "content": content,
            }
        if isinstance(output, str):
            return {"role": payload.get("role", "assistant"), "sender": sender, "content": output}
        return None

    def _extract_context_update(self, output: Any) -> Optional[Dict[str, Any]]:
        if isinstance(output, dict):
            update = output.get("context_update")
            if isinstance(update, dict):
                return update
        return None

    def _extract_done_flag(self, output: Any) -> bool:
        if isinstance(output, dict):
            return output.get("done") is True or output.get("stop") is True
        return False

    async def _publish_event(self, event: str, payload: Dict[str, Any]) -> None:
        if not self.message_bus:
            return
        data = {"event": event}
        data.update(payload or {})
        await self.message_bus.publish(data)

from __future__ import annotations

from typing import Any, Dict, List, Optional

from .base_strategy import InteractionStrategy
from engines.buses.base_message_bus import MessageBus
from engines.agents.models import AgentOutput
from engines.interaction.interaction_models import AgentMessage
from engines.interaction.interaction_models import (
    InteractionRequest,
    InteractionResult,
)


class GroupChatStrategy(InteractionStrategy):

    scenario_name = "group_chat"

    def __init__(
        self,
        agent_registry,
        message_bus: Optional[MessageBus],
        storage,
        default_max_rounds: int = 8,
    ):
        super().__init__(agent_registry, message_bus, storage)
        self.default_max_rounds = max(1, default_max_rounds)

    async def execute(self, request: InteractionRequest) -> InteractionResult:

        context: Dict[str, Any] = dict(request.context or {})
        metadata: Dict[str, Any] = dict(request.metadata or {})
        messages: List[Dict[str, Any]] = self._init_messages(context)

        participants = self._resolve_participants(request.agents, metadata)

        if not participants:
            return InteractionResult(
                success=False,
                results=[],
                final_context=context,
            )

        max_rounds = int(metadata.get("max_rounds", self.default_max_rounds))
        stop_on_done = bool(metadata.get("stop_on_done", True))
        stop_on_role = metadata.get("stop_on_role")

        results: List[AgentOutput] = []
        speaker_index = 0
        finished = False
        failure_reason: Optional[str] = None

        await self._publish_event(
            "group_chat_started",
            {
                "conversation_id": context.get("conversation_id"),
                "participants": [p.agent_id for p in participants],
                "max_rounds": max_rounds,
            },
        )

        for current_round in range(1, max_rounds + 1):

            if finished:
                break

            speaker = participants[speaker_index]
            speaker_index = (speaker_index + 1) % len(participants)

            await self._publish_event(
                "group_chat_turn_started",
                {
                    "round": current_round,
                    "agent_id": speaker.agent_id,
                    "agent_name": speaker.agent_name,
                },
            )

            output = await self._run_agent(
                agent_name=speaker.agent_name,
                agent_id=speaker.agent_id,
                context=context,
                payload={
                    "messages": list(messages),
                    "round": current_round,
                    "mode": "group_chat",
                },
            )

            results.append(output)

            if output.error:
                failure_reason = output.error

                await self._publish_event(
                    "group_chat_turn_failed",
                    {
                        "round": current_round,
                        "agent_id": speaker.agent_id,
                        "error": output.error,
                    },
                )

                finished = True
                break

            result_data = output.payload or output.message

            context_update = self._extract_context_update(result_data)
            if context_update:
                context.update(context_update)

            new_message = self._extract_message(result_data, speaker.agent_id)

            if new_message:
                messages.append(new_message)

            done_flag = self._extract_done_flag(result_data)

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
                        "agent_id": speaker.agent_id,
                        "agent_name": speaker.agent_name,
                    },
                )

        context["messages"] = messages

        success = failure_reason is None

        return InteractionResult(
            success=success,
            results=results,
            final_context=context,
            metadata={
                "rounds_executed": len(messages),
                "failure_reason": failure_reason,
                "participants": [p.agent_id for p in participants],
            },
        )

    # ---------------------------------------------------------

    def _init_messages(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:

        messages = context.get("messages")

        if isinstance(messages, list):
            return list(messages)

        user_message = context.get("user_message")

        if isinstance(user_message, str) and user_message.strip():
            return [
                {
                    "role": "user",
                    "sender": "user",
                    "content": user_message.strip(),
                }
            ]

        return []

    # ---------------------------------------------------------

    def _resolve_participants(self, agents, metadata):

        if not agents:
            return []

        by_id = {t.agent_id: t for t in agents if t.agent_id}

        order = metadata.get("participant_order")

        if isinstance(order, list):

            ordered = [by_id[tid] for tid in order if tid in by_id]

            if ordered:
                return ordered

        return list(agents)

    # ---------------------------------------------------------

    def _extract_message(self, output: Any, sender: str):

        if isinstance(output, dict):

            content = output.get("message") or output.get("content")

            if not content:
                return None

            return {
                "role": output.get("role", "assistant"),
                "sender": sender,
                "content": content,
            }

        if isinstance(output, str):

            return {
                "role": "assistant",
                "sender": sender,
                "content": output,
            }

        return None

    # ---------------------------------------------------------

    def _extract_context_update(self, output):

        if isinstance(output, dict):

            update = output.get("context_update")

            if isinstance(update, dict):
                return update

        return None

    # ---------------------------------------------------------

    def _extract_done_flag(self, output):

        if isinstance(output, dict):
            return output.get("done") is True or output.get("stop") is True

        return False

    # ---------------------------------------------------------

    async def _publish_event(self, event: str, payload: Dict[str, Any]):

        if not self.message_bus:
            return

        await self.message_bus.publish(
            AgentMessage(
                message_id=f"group_chat_{event}",
                sender="GroupChatStrategy",
                recipient="system",
                message_type=event,
                payload=payload,
            )
        )

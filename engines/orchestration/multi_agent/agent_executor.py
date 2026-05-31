"""Agent executor for multi-agent runtime.

Executes agent behaviors with runtime context and retry/control semantics.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from ...core.instance import ProcessInstance
from ...core.engine import OrchestrationEngine
from ...core.event_bus import Event, EventType


class AgentState(str, Enum):
    IDLE = "idle"
    ACTIVE = "active"
    WAITING = "waiting"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class AgentBehavior:
    behavior_id: str = ""
    behavior_type: str = "automated"
    policy: str | None = None
    decision_ref: str | None = None
    input_mapping: dict[str, str] = field(default_factory=dict)
    output_mapping: dict[str, str] = field(default_factory=dict)
    retry_max: int = 0
    priority: int = 0


@dataclass
class AgentExecutionResult:
    agent_id: str
    success: bool = True
    result: Any = None
    state: str = "completed"
    retries: int = 0
    errors: list[str] = field(default_factory=list)


class AgentExecutor:
    def __init__(self, orchestration_engine: OrchestrationEngine | None = None) -> None:
        self._engine = orchestration_engine
        self._behaviors: dict[str, AgentBehavior] = {}

    def register_behavior(self, behavior: AgentBehavior) -> None:
        self._behaviors[behavior.behavior_id] = behavior

    async def execute(
        self,
        agent: dict[str, Any],
        instance: ProcessInstance,
    ) -> AgentExecutionResult:
        agent_id = agent.get("id", f"agent_{id(agent)}")
        agent_type = agent.get("type", "automated")
        payload = agent.get("payload", agent.get("configuration", {}))

        result = AgentExecutionResult(agent_id=agent_id)
        result.state = "completed"
        result.result = {
            "agent_id": agent_id,
            "agent_type": agent_type,
            "payload": payload,
            "executed": True,
        }

        if instance:
            instance.set_variable(f"agent.{agent_id}", result.result)

        if self._engine is not None:
            self._engine.event_bus.publish(
                Event(
                    type=EventType.ACTIVITY_COMPLETED,
                    data={
                        "instance_id": instance.id if instance else "",
                        "agent_id": agent_id,
                        "engine_type": "multi_agent",
                    },
                )
            )

        return result

    async def execute_with_retry(
        self,
        agent: dict[str, Any],
        instance: ProcessInstance,
        retry_count: int = 3,
    ) -> AgentExecutionResult:
        agent_id = agent.get("id", "")
        last_error = ""

        for attempt in range(retry_count + 1):
            try:
                result = await self.execute(agent, instance)
                result.retries = attempt
                return result
            except Exception as e:
                last_error = str(e)
                if attempt == retry_count:
                    result = AgentExecutionResult(
                        agent_id=agent_id,
                        success=False,
                        state="failed",
                        retries=attempt,
                        errors=[last_error],
                    )
                    return result

        return AgentExecutionResult(agent_id=agent_id, success=False, errors=[last_error])

"""Agent executor for multi-agent runtime — delegates to engines.agent."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from ..core.instance import ProcessInstance
from ..core.event_bus import Event, EventType


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
    """Executes agent behaviors using engines.agent runtime."""

    def __init__(self, orchestration_engine=None) -> None:
        self._engine = orchestration_engine
        self._behaviors: dict[str, AgentBehavior] = {}

    def register_behavior(self, behavior: AgentBehavior) -> None:
        self._behaviors[behavior.behavior_id] = behavior

    async def execute(self, agent: dict, instance: ProcessInstance) -> AgentExecutionResult:
        agent_name = agent.get("agent_name") or agent.get("name", "unknown")
        try:
            from engines.agent.agent_registry import AgentRegistry
            registry = AgentRegistry()
            result = await registry.run(agent_name, instance.variables)
            instance.variables[f"agent.{agent.get('id', agent_name)}"] = result
            if self._engine and hasattr(self._engine, 'event_bus'):
                import asyncio
                asyncio.ensure_future(
                    self._engine.event_bus.publish(Event(EventType.ACTIVITY_COMPLETED, {
                        "agent_id": agent.get("id"),
                        "agent_name": agent_name,
                    }))
                )
            return AgentExecutionResult(agent_id=agent.get("id", agent_name), success=True, result=result)
        except Exception as e:
            return AgentExecutionResult(agent_id=agent.get("id", agent_name), success=False, state="failed", errors=[str(e)])

    async def execute_with_retry(self, agent: dict, instance: ProcessInstance, retry_count: int = 3) -> AgentExecutionResult:
        import asyncio
        for attempt in range(retry_count):
            result = await self.execute(agent, instance)
            if result.success:
                return result
            await asyncio.sleep(1 * (attempt + 1))
        return AgentExecutionResult(
            agent_id=agent.get("id", "unknown"),
            success=False,
            state="failed",
            retries=retry_count,
            errors=[f"Failed after {retry_count} retries"],
        )

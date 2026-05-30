"""Agent execution abstraction for user-defined callbacks."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Agent:
    agent_id: str
    execute_task: callable


class AgentExecutor:
    async def execute(self, agent: Agent, task: str, context: dict) -> object:
        return await _maybe_await(agent.execute_task(agent_id=agent.agent_id, task=task, context=context))


async def _maybe_await(value):
    import inspect

    if inspect.isawaitable(value):
        return await value
    return value

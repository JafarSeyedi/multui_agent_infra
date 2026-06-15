from __future__ import annotations

import inspect
from dataclasses import dataclass, field
from typing import Any

from ..callbacks import CallbackContext
from ..models import AgentInput, AgentOutput
from .base_agent import BaseAgent


@dataclass
class ErrorContext:
    failed_keys: list[str] = field(default_factory=list)
    last_error: str | None = None


RouterFn = Any


class RoutedAgent(BaseAgent[AgentInput, AgentOutput]):
    """Agent that uses an explicit routing function to select a sub-agent.

    Supports failover: if the selected agent errors before producing output,
    the router is recalled with error context. Keys that already failed
    cannot be re-selected.
    """

    input_model_class = AgentInput
    output_model_class = AgentOutput

    def __init__(
        self,
        agent_id: str,
        agent_name: str,
        agents: dict[str, BaseAgent],
        router: RouterFn,
        **kwargs: Any,
    ) -> None:
        super().__init__(agent_id=agent_id, agent_name=agent_name, **kwargs)
        self._agents = agents
        self._router = router

    async def execute(self, input_model: AgentInput) -> AgentOutput:
        ctx = CallbackContext(
            agent_name=self.agent_name,
            agent_id=self.agent_id,
        )
        error_ctx = ErrorContext()

        selected_key = await self._resolve_route(ctx, self._agents, error_ctx)
        if selected_key is None:
            return AgentOutput(
                agent_name=self.agent_name,
                message="No agent could handle the request",
                payload={},
            )

        selected = self._agents[selected_key]
        try:
            return await selected.run(input_model)
        except Exception as e:
            error_ctx.failed_keys.append(selected_key)
            error_ctx.last_error = str(e)

            fallback_key = await self._resolve_route(ctx, self._agents, error_ctx)
            if fallback_key is None:
                raise

            fallback = self._agents[fallback_key]
            return await fallback.run(input_model)

    async def _resolve_route(
        self,
        ctx: CallbackContext,
        agents: dict[str, BaseAgent],
        error_ctx: ErrorContext,
    ) -> str | None:
        if callable(self._router):
            if error_ctx.failed_keys:
                result = self._router(ctx, agents, error_ctx)
            else:
                result = self._router(ctx, agents)
            if inspect.isawaitable(result):
                result = await result
        else:
            result = self._router

        if result is None:
            return None

        key = result if isinstance(result, str) else result.get("key", "")
        if key in error_ctx.failed_keys:
            return None
        return key if key in agents else None

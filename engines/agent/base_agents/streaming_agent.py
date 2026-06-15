from __future__ import annotations

from typing import Any, AsyncIterator

from ..models import AgentInput, AgentOutput
from .base_agent import BaseAgent


class StreamingAgent(BaseAgent[AgentInput, AgentOutput]):
    """Agent wrapper that yields token-by-token progress events.

    The wrapped agent's full output is collected and then replayed
    as individual token events for streaming display.
    """

    input_model_class = AgentInput
    output_model_class = AgentOutput

    def __init__(
        self,
        agent_id: str,
        agent_name: str,
        wrapped_agent: BaseAgent,
        **kwargs: Any,
    ) -> None:
        super().__init__(agent_id=agent_id, agent_name=agent_name, **kwargs)
        self._wrapped = wrapped_agent

    async def execute(self, input_model: AgentInput) -> AgentOutput:
        return await self._wrapped.run(input_model)

    async def run_streaming(
        self,
        input_data: Any,
        token_separator: str = " ",
    ) -> AsyncIterator[str]:
        result = await self.run(input_data)
        message = result.message or ""
        for token in message.split(token_separator):
            yield token + token_separator

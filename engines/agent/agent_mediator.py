"""Unified mediator for agent-to-agent communication and strategy dispatch."""

from __future__ import annotations

from typing import Any

from .._types import RawData


class AgentMediator:
    """Central mediator for agent communication and strategy execution.

    Replaces engines.agent.mediator.AgentMediator,
    engines.interaction.mediator.InteractionMediator, and
    the registration parts of engines.orchestration.multi_agent.mediator.
    """

    def __init__(self, registry=None, message_bus=None, protocol=None) -> None:
        from .agent_registry import AgentRegistry
        self.registry: AgentRegistry = registry or AgentRegistry()
        self.message_bus = message_bus
        self.protocol = protocol

    # --- Agent communication ---

    def register_agent(self, agent) -> None:
        self.registry.register(agent)

    def get_agent(self, name: str) -> Any | None:
        return self.registry.get(name)

    def list_agents(self) -> list[str]:
        return self.registry.list_agents()

    async def send(self, sender: str, recipient: str, input_data: RawData) -> Any | None:
        if self.protocol is not None:
            from .protocols import AgentMessage
            msg = AgentMessage(sender=sender, recipient=recipient, payload=input_data)
            return await self.protocol.send_message(msg)
        agent = self.registry.get(recipient)
        if agent is None:
            return None
        return await agent.run(input_data)

    async def broadcast(self, sender: str, input_data: RawData) -> dict[str, Any]:
        results = {}
        for name in self.registry.list_agents():
            try:
                result = await self.send(sender, name, input_data)
                results[name] = result
            except Exception as e:
                results[name] = {"error": str(e)}
        return results

    # --- Strategy dispatch ---

    def register_strategy(self, scenario: str, strategy) -> None:
        self.registry.register_strategy(scenario, strategy)

    async def execute_strategy(self, scenario: str, request) -> Any:
        from .backends.native_backend import NativeOrchestrationBackend
        backend = NativeOrchestrationBackend(
            agent_registry=self.registry,
            message_bus=self.message_bus,
        )
        return await backend.execute(request)

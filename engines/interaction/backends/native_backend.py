# agents/interaction/backends/native_backend.py
from datetime import datetime

from .base_backend import BaseOrchestrationBackend
from engines.communication.buses.base_message_bus import MessageBus
from engines.interaction.base_strategy import InteractionStrategy
from engines.interaction.broadcast_strategy import BroadcastStrategy
from engines.interaction.coordinator_strategy import CoordinatorStrategy
from engines.interaction.debate_strategy import DebateStrategy
from engines.interaction.ensemble_strategy import EnsembleStrategy
from engines.interaction.group_chat_strategy import GroupChatStrategy
from engines.interaction.interaction_models import InteractionRequest
from engines.interaction.interaction_models import InteractionResult
from engines.interaction.round_robin_strategy import RoundRobinStrategy
from engines.interaction.self_refine_strategy import SelfRefineStrategy
# import all strategies


# Scenario to Strategy class mapping
STRATEGY_REGISTRY: dict[str, type[InteractionStrategy]] = {
    "broadcast":         BroadcastStrategy,
    "round_robin":       RoundRobinStrategy,
    "group_chat":        GroupChatStrategy,
    "debate":            DebateStrategy,
    "ensemble":          EnsembleStrategy,
    "coordinator":       CoordinatorStrategy,
    "self_refine":       SelfRefineStrategy,
}


class NativeOrchestrationBackend(BaseOrchestrationBackend):
    def __init__(
        self,
        agent_registry,
        message_bus: MessageBus | None = None,
        storage=None,
        strategy_overrides: dict[str, type[InteractionStrategy]] | None = None,
    ):
        self.agent_registry = agent_registry
        self.message_bus = message_bus
        self.storage = storage

        # Ability to override strategies externally (for testing or development)
        self._strategy_map = {**STRATEGY_REGISTRY, **(strategy_overrides or {})}

    def _build_strategy(self, scenario: str) -> InteractionStrategy:
        strategy_cls = self._strategy_map.get(scenario)
        if strategy_cls is None:
            raise ValueError(f"Unsupported orchestration scenario: '{scenario}'")
        return strategy_cls(
            agent_registry=self.agent_registry,
            message_bus=self.message_bus,
            storage=self.storage,
        )

    async def execute(self, request: InteractionRequest) -> InteractionResult:
        started_at = datetime.utcnow()

        strategy = self._build_strategy(request.scenario)
        result = await strategy.execute(request)

        completed_at = datetime.utcnow()

        # Ensure tracking fields are filled
        return result.model_copy(
            update={
                "workflow_id": request.workflow_id,
                "scenario": request.scenario,
                "backend_used": "native",
                "started_at": started_at,
                "completed_at": completed_at,
            }
        )

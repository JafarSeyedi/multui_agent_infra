# agents/orchestration/backends/native_backend.py

from datetime import datetime
from typing import Optional, Dict, Type
import uuid

from agents.orchestration.models import (
    OrchestrationRequest,
    OrchestrationResult,
    OrchestrationExecution,
    PipelineStep,
    AgentMessage,
)
from agents.buses.base import MessageBus
from agents.orchestration.interaction.base_strategy import InteractionStrategy

# import همه استراتژی‌ها
from agents.orchestration.interaction.broadcast_strategy import BroadcastStrategy
from agents.orchestration.interaction.conditional_strategy import ConditionalStrategy
from agents.orchestration.interaction.dag_strategy import DAGStrategy
from agents.orchestration.interaction.selector_strategy import SelectorStrategy
from agents.orchestration.interaction.debate_strategy import DebateStrategy
from agents.orchestration.interaction.ensemble_strategy import EnsembleStrategy
from agents.orchestration.interaction.event_driven_strategy import EventDrivenStrategy
from agents.orchestration.interaction.group_chat_strategy import GroupChatStrategy
from agents.orchestration.interaction.manager_strategy import ManagerStrategy
from agents.orchestration.interaction.memory_augmented_strategy import MemoryAugmentedStrategy
from agents.orchestration.interaction.pipeline_strategy import PipelineStrategy
from agents.orchestration.interaction.round_robin_strategy import RoundRobinStrategy
from agents.orchestration.interaction.self_refine_strategy import SelfRefineStrategy
from agents.orchestration.interaction.sequential_strategy import SequentialStrategy


# نگاشت سناریو → کلاس استراتژی
STRATEGY_REGISTRY: Dict[str, Type[InteractionStrategy]] = {
    "sequential":        SequentialStrategy,
    "broadcast":         BroadcastStrategy,
    "round_robin":       RoundRobinStrategy,
    "selector":          SelectorStrategy,
    "group_chat":        GroupChatStrategy,
    "debate":            DebateStrategy,
    "dag":               DAGStrategy,
    "event_driven":      EventDrivenStrategy,
    "ensemble":          EnsembleStrategy,
    "manager":           ManagerStrategy,
    "memory_augmented":  MemoryAugmentedStrategy,
    "pipeline":          PipelineStrategy,
    "conditional":       ConditionalStrategy,
    "self_refine":       SelfRefineStrategy,
}


class NativeOrchestrationBackend:
    def __init__(
        self,
        registry,
        message_bus: Optional[MessageBus] = None,
        storage=None,
        strategy_overrides: Optional[Dict[str, Type[InteractionStrategy]]] = None,
    ):
        self.registry = registry
        self.message_bus = message_bus
        self.storage = storage

        # امکان override کردن استراتژی‌ها از بیرون (برای تست یا توسعه)
        self._strategy_map = {**STRATEGY_REGISTRY, **(strategy_overrides or {})}

    def _build_strategy(self, scenario: str) -> InteractionStrategy:
        strategy_cls = self._strategy_map.get(scenario)
        if strategy_cls is None:
            raise ValueError(f"Unsupported orchestration scenario: '{scenario}'")
        return strategy_cls(
            registry=self.registry,
            message_bus=self.message_bus,
            storage=self.storage,
        )

    async def execute(self, request: OrchestrationRequest) -> OrchestrationResult:
        strategy = self._build_strategy(request.scenario)
        return await strategy.execute(request)

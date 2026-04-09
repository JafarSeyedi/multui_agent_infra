# agents/orchestration/backends/native_backend.py
from datetime import datetime
from typing import Optional, Dict, Type

from agents.orchestration.models import (
    OrchestrationRequest,
    OrchestrationResult,
)
from agents.buses.base import MessageBus
from agents.orchestration.interaction.base_strategy import InteractionStrategy

# import همه استراتژی‌ها
from agents.orchestration.interaction.broadcast_strategy import BroadcastStrategy
from agents.orchestration.interaction.conditional_strategy import ConditionalStrategy
from agents.orchestration.interaction.dag_strategy import DAGStrategy
from agents.orchestration.interaction.debate_strategy import DebateStrategy
from agents.orchestration.interaction.ensemble_strategy import EnsembleStrategy
from agents.orchestration.interaction.event_driven_strategy import EventDrivenStrategy
from agents.orchestration.interaction.group_chat_strategy import GroupChatStrategy
from agents.orchestration.interaction.manager_strategy import ManagerStrategy
from agents.orchestration.interaction.memory_augmented_strategy import MemoryAugmentedStrategy
from agents.orchestration.interaction.pipeline_strategy import PipelineStrategy
from agents.orchestration.interaction.round_robin_strategy import RoundRobinStrategy
from agents.orchestration.interaction.self_refine_strategy import SelfRefineStrategy
from .base_backend import BaseOrchestrationBackend


# نگاشت سناریو → کلاس استراتژی
STRATEGY_REGISTRY: Dict[str, Type[InteractionStrategy]] = {
    "broadcast":         BroadcastStrategy,
    "round_robin":       RoundRobinStrategy,
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


class NativeOrchestrationBackend(BaseOrchestrationBackend):
    def __init__(
        self,
        agent_registry,
        message_bus: Optional[MessageBus] = None,
        storage=None,
        strategy_overrides: Optional[Dict[str, Type[InteractionStrategy]]] = None,
    ):
        self.agent_registry = agent_registry
        self.message_bus = message_bus
        self.storage = storage

        # امکان override کردن استراتژی‌ها از بیرون (برای تست یا توسعه)
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

    async def execute(self, request: OrchestrationRequest) -> OrchestrationResult:
        started_at = datetime.utcnow()
        
        strategy = self._build_strategy(request.scenario)
        result = await strategy.execute(request)
        
        completed_at = datetime.utcnow()
        
        # اطمینان از پر بودن فیلدهای tracking
        return result.model_copy(
            update={
                "workflow_id": request.workflow_id,
                "scenario": request.scenario,
                "backend_used": "native",
                "started_at": started_at,
                "completed_at": completed_at,
            }
        )

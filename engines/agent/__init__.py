from .agent_registry import AgentRegistry
from .agent_mediator import AgentMediator
from .models import AgentExecutionRecord, AgentInput, AgentOutput

__all__ = [
    "AgentExecutionRecord",
    "AgentInput",
    "AgentMediator",
    "AgentOutput",
    "AgentRegistry",
    "BroadcastStrategy",
    "CoordinatorStrategy",
    "DebateStrategy",
    "EnsembleStrategy",
    "GroupChatStrategy",
    "InteractionStrategy",
    "InteractionStrategyRegistry",
    "RoundRobinStrategy",
    "SelfRefineStrategy",
]


def __getattr__(name):
    if name in _STRATEGY_MODULES:
        import importlib
        mod = importlib.import_module(f".strategies.{_STRATEGY_MODULES[name]}", __package__)
        attr = getattr(mod, name)
        globals()[name] = attr
        return attr
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


_STRATEGY_MODULES = {
    "BroadcastStrategy": "broadcast_strategy",
    "CoordinatorStrategy": "coordinator_strategy",
    "DebateStrategy": "debate_strategy",
    "EnsembleStrategy": "ensemble_strategy",
    "GroupChatStrategy": "group_chat_strategy",
    "InteractionStrategy": "base_strategy",
    "InteractionStrategyRegistry": "interaction_strategy_registry",
    "RoundRobinStrategy": "round_robin_strategy",
    "SelfRefineStrategy": "self_refine_strategy",
}

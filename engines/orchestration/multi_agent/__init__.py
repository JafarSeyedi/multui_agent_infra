"""Multi-agent runtime APIs."""

import importlib

_LAZY_MODULES: dict[str, str] = {
    "AgentBehavior": ".agent_executor",
    "AgentExecutionResult": ".agent_executor",
    "AgentExecutor": ".agent_executor",
    "AgentMessage": ".message_router",
    "AgentState": ".agent_executor",
    "CoordinationHandler": ".coordination_handler",
    "CoordinationPattern": ".coordination_handler",
    "CoordinationStep": ".coordination_handler",
    "InteractionHandler": ".interaction_handler",
    "InteractionState": ".interaction_handler",
    "MessageRouter": ".message_router",
    "MultiAgentEngine": ".engine",
    "MultiAgentExecutionError": ".engine",
    "MultiAgentPlan": ".engine",
    "NegotiationHandler": ".negotiation_handler",
    "NegotiationOffer": ".negotiation_handler",
    "NegotiationPhase": ".negotiation_handler",
    "NegotiationState": ".negotiation_handler",
    "ProtocolHandler": ".protocol_handler",
    "ProtocolState": ".protocol_handler",
    "ProtocolType": ".protocol_handler",
    "RoutingResult": ".message_router",
}


def __getattr__(name: str):
    if name in _LAZY_MODULES:
        mod = importlib.import_module(_LAZY_MODULES[name], __package__)
        val = getattr(mod, name)
        globals()[name] = val
        return val
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = sorted(_LAZY_MODULES.keys())

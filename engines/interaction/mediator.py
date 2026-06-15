# Backward-compat re-export
from engines.agent.agent_mediator import AgentMediator

InteractionMediator = AgentMediator

__all__ = ["AgentMediator", "InteractionMediator"]

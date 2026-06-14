# engines/orchestration/multi_agent/models/multi_agent_models.py
"""
Multi-Agent Interaction models
===============================
Extracted from osdm_models.py
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from ...models.shared_models import BaseElement, BaseOSDMDocument
from ...bpmn.models.bpmn_models import Participant


class InteractionStrategy(str, Enum):
    BROADCAST = "broadcast"
    DEBATE = "debate"
    COORDINATOR = "coordinator"
    ENSEMBLE = "ensemble"
    ROUND_ROBIN = "round_robin"
    SELF_REFINE = "self_refine"
    GROUP_CHAT = "group_chat"


@dataclass
class InteractionProtocol(BaseElement):
    strategy: InteractionStrategy = InteractionStrategy.BROADCAST
    participants: list[Participant] = field(default_factory=list)
    message_pattern: str | None = None
    coordinator_ref: Participant | None = None


@dataclass
class InteractionModel:
    id: str
    name: str
    protocols: list[InteractionProtocol] = field(default_factory=list)


class MultiAgentInteractionDocument(BaseOSDMDocument):
    interaction_models: list[InteractionModel] = field(default_factory=list)

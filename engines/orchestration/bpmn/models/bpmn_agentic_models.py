from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from ...models.shared_models import BaseElement
from .bpmn_models import Gateway, Lane, MessageFlow, Task


class ReflectionStrategy(str, Enum):
    SELF = "self"
    CROSS = "cross"
    HUMAN = "human"


class CollaborationStrategyType(str, Enum):
    VOTING = "voting"
    ROLE = "role"
    DEBATE = "debate"
    COMPETITION = "competition"


class MergeStrategyType(str, Enum):
    MAJORITY = "majority"
    LEADER = "leader"
    FASTEST = "fastest"
    MOST_COMPLETE = "most_complete"


class VotingRule(str, Enum):
    MAJORITY = "majority"
    ABSOLUTE_MAJORITY = "absolute_majority"
    MINORITY = "minority"


class RoleStrategyType(str, Enum):
    LEADER_DRIVEN = "leader_driven"
    COMPOSED = "composed"


class CompetitionRule(str, Enum):
    FASTEST = "fastest"
    MOST_COMPLETE = "most_complete"


@dataclass
class VotingConfig:
    rule: VotingRule = VotingRule.MAJORITY
    quorum: float | None = None


@dataclass
class RoleConfig:
    strategy: RoleStrategyType = RoleStrategyType.LEADER_DRIVEN
    leader_id: str | None = None


@dataclass
class CompetitionConfig:
    rule: CompetitionRule = CompetitionRule.FASTEST
    timeout_seconds: float | None = None


@dataclass
class CollaborationStrategy:
    type: CollaborationStrategyType = CollaborationStrategyType.VOTING
    voting_config: VotingConfig | None = None
    role_config: RoleConfig | None = None
    competition_config: CompetitionConfig | None = None
    max_rounds: int | None = None
    consensus_threshold: float | None = None


@dataclass
class MergeStrategy:
    type: MergeStrategyType = MergeStrategyType.MAJORITY
    min_votes: int | None = None


@dataclass
class AgenticTask(Task):
    reflection_strategy: ReflectionStrategy = ReflectionStrategy.SELF
    human_feedback_enabled: bool = False
    agent_id: str | None = None
    trust_threshold: float = 0.0
    max_reflection_rounds: int = 3
    reflection_config: dict[str, Any] = field(default_factory=dict)
    agent_ids: list[str] = field(default_factory=list)


@dataclass
class AgenticMessageFlow(MessageFlow):
    agent_communication: bool = True
    communication_protocol: str | None = None
    reflection_enabled: bool = False


@dataclass
class DivergingAgenticGateway(Gateway):
    collaboration_strategy: CollaborationStrategy | None = None
    agent_ids: list[str] = field(default_factory=list)
    min_agents: int = 1


@dataclass
class MergingAgenticGateway(Gateway):
    merge_strategy: MergeStrategy | None = None
    wait_for_all: bool = True
    timeout_seconds: float | None = None


@dataclass
class AgenticLane(Lane):
    trust_score: float = 1.0
    agent_id: str | None = None
    agent_capabilities: list[str] = field(default_factory=list)
    model_provider: str | None = None
    system_prompt: str | None = None

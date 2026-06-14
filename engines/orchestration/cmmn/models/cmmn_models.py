# engines/orchestration/cmmn/models/cmmn_models.py
"""
CMMN – Case Management Model Notation models
=============================================
Extracted from osdm_models.py
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from ...models.shared_models import BaseElement, BaseOSDMDocument, CaseFileMultiplicity
from ...bpmn.models.bpmn_models import Activity, EventListenerType, FlowElement, FlowNode, FormalExpression, ItemDefinition, Process, ResourceRole


@dataclass
class PlanItem(BaseElement):
    definition_ref: Stage | Milestone | EventListener | None = None
    entry_criteria: list[EntryCriterion] = field(default_factory=list)
    exit_criteria: list[ExitCriterion] = field(default_factory=list)
    repetition_count: int = 1
    is_blocking: bool = True
    _definition_ref_id: str | None = None


@dataclass
class DiscretionaryItem(PlanItem):
    applicability_rule: ApplicabilityRule | None = None


@dataclass
class CaseFileItem(BaseElement):
    item_definition_ref: ItemDefinition | None = None
    multiplicity: CaseFileMultiplicity = CaseFileMultiplicity.EXACTLY_ONE
    _item_definition_ref_id: str | None = None


@dataclass
class CaseTask(Activity):
    case_ref: CMMNDefinition | None = None
    _case_ref_id: str | None = None


@dataclass
class ProcessTask(Activity):
    process_ref: Process | None = None
    _process_ref_id: str | None = None


@dataclass
class HumanTask(Activity):
    role_ref: ResourceRole | None = None
    _role_ref_id: str | None = None


@dataclass
class ApplicabilityRule(BaseElement):
    condition: FormalExpression | None = None


@dataclass
class EntryCriterion(BaseElement):
    sentry_ref: Sentry | None = None
    _sentry_ref_id: str | None = None


@dataclass
class ExitCriterion(BaseElement):
    sentry_ref: Sentry | None = None
    _sentry_ref_id: str | None = None


@dataclass
class Stage(FlowNode):
    flow_elements: dict[str, FlowElement] = field(default_factory=dict)
    sentries: list[Sentry] = field(default_factory=list)


@dataclass
class Milestone(FlowNode):
    pass


class MilestoneKind(str, Enum):
    ACHIEVEMENT = "achievement"
    DEADLINE = "deadline"
    CONDITIONAL = "conditional"


@dataclass
class DecisionTask(Activity):
    decision_ref: str | None = None


@dataclass
class EventListener(FlowNode):
    event_type: EventListenerType = EventListenerType.USER


@dataclass
class Sentry(BaseElement):
    on_part: FormalExpression | None = None
    if_part: FormalExpression | None = None


@dataclass
class SentryExpression(FormalExpression):
    pass


@dataclass
class CMMNDefinition:
    id: str
    name: str
    case: Stage
    plan_items: list[PlanItem] = field(default_factory=list)
    discretionary_items: list[DiscretionaryItem] = field(default_factory=list)
    case_file_items: list[CaseFileItem] = field(default_factory=list)


class CMMNDocument(BaseOSDMDocument):
    cmmn_definitions: list[CMMNDefinition] = field(default_factory=list)

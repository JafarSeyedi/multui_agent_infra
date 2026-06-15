# engines/orchestration/models/shared_models.py
"""
OSDM – Shared Models (extracted from osdm_models.py)
=====================================================
Classes that are shared across multiple model files, including
enums, base infrastructure, error handling, and document roots.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Any

from engines.document.models.base import BaseDocument
from engines.document.models.media_types import DocumentFormat
from engines.document.models.msdm_models import MSDMDocument
from engines.document.models.ssdm_models import SSDMDocument
from engines.document.models.standard import DocumentStandard
from engines.tools.models import TSDMDocument

if TYPE_CHECKING:
    from ..bpmn.models.bpmn_models import BPMNDiagram, BPMNDocument
    from ..cmmn.models.cmmn_models import CMMNDocument
    from ..dmn.models.dmn_models import DMNDocument
    from ..cep.models.cep_models import CEPDocument
    from ..multi_agent.models.multi_agent_models import MultiAgentInteractionDocument
    from ..bpmn.models.bpmn_models import Script
    from ..state_machine.models.state_machine_models import State




# ═══════════════════════════════════════════════════════════════
# New Enums for previously untyped fields
# ═══════════════════════════════════════════════════════════════

class ParticipantBandKind(str, Enum):
    TOP_INITIATING = "top_initiating"
    MIDDLE_INITIATING = "middle_initiating"
    BOTTOM_INITIATING = "bottom_initiating"
    TOP_NON_INITIATING = "top_non_initiating"
    MIDDLE_NON_INITIATING = "middle_non_initiating"
    BOTTOM_NON_INITIATING = "bottom_non_initiating"

class MessageVisibleKind(str, Enum):
    INITIATING = "initiating"
    NON_INITIATING = "non_initiating"

class AlignmentKind(str, Enum):
    LEFT = "left"
    CENTER = "center"
    RIGHT = "right"
    TOP = "top"
    BOTTOM = "bottom"

class TimerCalculationType(str, Enum):
    ISO8601 = "Iso8601"
    NUMBER = "Number"
    PROPERTY = "Property"
    FORMULA = "Formula"

class TimeReference(str, Enum):
    PROPERTY = "Property"
    PROCESS_START_TIME = "ProcessStartTime"
    ACTIVITY_START_TIME = "ActivityStartTime"
    EVENT_START_TIME = "EventStartTime"

class DurationResolution(str, Enum):
    SECOND = "Second"
    MINUTE = "Minute"
    HOUR = "Hour"
    DAY = "Day"

class EscapeType(str, Enum):
    pass

class CorrelationPropertyType(str, Enum):
    KEY = "key"
    VALUE = "value"

class CaseFileMultiplicity(str, Enum):
    ZERO_OR_ONE = "0..1"
    EXACTLY_ONE = "1"
    ZERO_OR_MORE = "0..*"
    ONE_OR_MORE = "1..*"

# ── Original Enums (unchanged, included for completeness) ────────

class ItemKind(str, Enum):
    INFORMATION = "Information"
    PHYSICAL = "Physical"

class TimerEventType(str, Enum):
    DATE = "dateTime"
    CYCLE = "timeCycle"
    DURATION = "timeDuration"

class RelationshipDirection(str, Enum):
    NONE = "None"
    FORWARD = "Forward"
    BACKWARD = "Backward"
    BOTH = "Both"

class WorkflowStateType(str, Enum):
    OPERATION = "operation"
    EVENT = "event"
    SWITCH = "switch"
    DELAY = "delay"
    PARALLEL = "parallel"
    FOREACH = "forEach"
    INJECT = "inject"
    CALLBACK = "callback"
    SUBFLOW = "subFlow"

class ResourceParameterType(str, Enum):
    USER_FIELD = "UserField"
    ENTITY_FIELD = "EntityField"
    CLAIM = "Claim"
    ROLE = "Role"

class PseudoStateKind(str, Enum):
    INITIAL = "initial"
    DEEP_HISTORY = "deepHistory"
    SHALLOW_HISTORY = "shallowHistory"
    JOIN = "join"
    FORK = "fork"
    JUNCTION = "junction"
    CHOICE = "choice"
    ENTRY_POINT = "entryPoint"
    EXIT_POINT = "exitPoint"
    TERMINATE = "terminate"

# ═══════════════════════════════════════════════════════════════
# Base elements (unchanged)
# ═══════════════════════════════════════════════════════════════
@dataclass
class BaseElement:
    id: str
    name: str | None = None
    documentation: str | None = None

@dataclass
class RootElement(BaseElement):
    pass

# ── Extension definitions ────────────────────────────────────────
@dataclass
class ExtensionAttributeDefinition:
    name: str
    extension_type: str
    is_reference: bool = False

@dataclass
class ExtensionDefinition:
    name: str
    extension_attribute_definitions: list[ExtensionAttributeDefinition] = field(default_factory=list)

@dataclass
class ExtensionAttributeValue:
    extension_attribute_definition: ExtensionAttributeDefinition | None = None
    value: str | None = None
    value_ref: str | None = None

@dataclass
class Extension:
    definition: ExtensionDefinition | None = None
    must_understand: bool = False

# ── Diagram interchange ──────────────────────────────────────────
@dataclass
class Bounds:
    x: float = 0
    y: float = 0
    width: float = 0
    height: float = 0

@dataclass
class Locator(BaseElement):
    x: float = 0.0
    y: float = 0.0

@dataclass
class DiagramElement(BaseElement):
    owning_element: DiagramElement | None = None
    model_element: BaseElement | None = None
    model_element_id: str | None = None  # temporary ID for resolution

@dataclass
class Edge(DiagramElement):
    source: DiagramElement | None = None
    target: DiagramElement | None = None

@dataclass
class Shape(DiagramElement):
    bounds: Bounds = field(default_factory=Bounds)

# ── Cloud‑native extensions for AWS Step Functions / Azure Logic Apps ─
class ErrorHandlingOperator(str, Enum):
    EQUALS = "Equals"
    NOT_EQUALS = "NotEquals"
    MATCHES = "Matches"

class RetryBackoffRate(float, Enum):
    LINEAR = 1.0
    DEFAULT = 2.0

@dataclass
class CloudResourceBinding:
    resource_arn: str | None = None
    azure_function_id: str | None = None
    parameters: dict[str, Any] = field(default_factory=dict)

@dataclass
class ErrorHandlingConfig:
    error_equals: list[str] = field(default_factory=list)
    next_state: State | None = None
    result_path: str | None = None

@dataclass
class RetryConfig:
    error_equals: list[str] = field(default_factory=list)
    interval_seconds: int = 1
    max_attempts: int = 3
    backoff_rate: float = 2.0

@dataclass
class TimeoutConfig:
    timeout_seconds: int = 300
    heartbeat_seconds: int | None = None

# ═══════════════════════════════════════════════════════════════
# Top‑level OSDM Document
# ═══════════════════════════════════════════════════════════════
class BaseOSDMDocument(BaseDocument):
    kind: DocumentStandard = DocumentStandard.OSDM
    source_format: DocumentFormat | None = None
    source_file: str | None = None
    version: str = "1.0.0"
    version_description: str | None = None

    root_elements: dict[str, RootElement] = field(default_factory=dict)
    diagrams: list[BPMNDiagram] = field(default_factory=list)
    extensions: list[Extension] = field(default_factory=list)


@dataclass
class OSDMModel:
    processes: list[BPMNDocument] = field(default_factory=list)
    collaborations: list[BPMNDocument] = field(default_factory=list)
    choreographies: list[BPMNDocument] = field(default_factory=list)
    global_tasks: list[BPMNDocument] = field(default_factory=list)
    cmmn_definitions: list[CMMNDocument] = field(default_factory=list)
    state_machines: list[CMMNDocument] = field(default_factory=list)
    dmn_definitions: list[DMNDocument] = field(default_factory=list)
    cep_definitions: list[CEPDocument] = field(default_factory=list)
    interaction_models: list[MultiAgentInteractionDocument] = field(default_factory=list)

    msdm_refs: dict[str, MSDMDocument] = field(default_factory=dict)
    ssdm_refs: dict[str, SSDMDocument ] = field(default_factory=dict)
    tsdm_refs: dict[str, TSDMDocument] = field(default_factory=dict)


# Helper dataclasses that need to be defined after the main ones
@dataclass
class ActionList(BaseElement):
    actions: list[str | Script] = field(default_factory=list)

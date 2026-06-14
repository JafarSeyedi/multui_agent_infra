# engines/orchestration/cep/models/cep_models.py
"""
CEP – Complex Event Processing models
======================================
Extracted from osdm_models.py
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from ...models.shared_models import ActionList, BaseElement, BaseOSDMDocument


class CEPOperator(str, Enum):
    AND = "and"
    OR = "or"
    NOT = "not"
    SEQUENCE = "sequence"
    WINDOW = "window"
    THRESHOLD = "threshold"
    ABSENCE = "absence"


@dataclass
class EventStream:
    name: str
    attributes: dict[str, str] = field(default_factory=dict)


@dataclass
class CEPRule:
    name: str
    pattern: str
    operator: CEPOperator = CEPOperator.AND
    window_duration: str | None = None
    filter_expression: str | None = None
    actions: ActionList = field(default_factory=lambda: ActionList(id="", actions=[]))


@dataclass
class CEPDefinition:
    id: str
    name: str
    streams: list[EventStream] = field(default_factory=list)
    rules: list[CEPRule] = field(default_factory=list)


class CEPDocument(BaseOSDMDocument):
    cep_definitions: list[CEPDefinition] = field(default_factory=list)

# engines/orchestration/dmn/models/dmn_models.py
"""
DMN – Decision Model Notation models
======================================
Extracted from osdm_models.py
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from engines.document.models.msdm_models import Entity

from ...models.shared_models import BaseElement, BaseOSDMDocument, RootElement
from ...bpmn.models.bpmn_models import FlowNode, FormalExpression, Script


class DecisionLogicType(str, Enum):
    DECISION_TABLE = "decisionTable"
    INVOCATION = "invocation"
    LITERAL_EXPRESSION = "literalExpression"
    CONTEXT = "context"
    RELATION = "relation"
    FUNCTION_DEFINITION = "functionDefinition"


@dataclass
class InformationRequirement(BaseElement):
    required_decision: Decision | None = None
    required_input: InputData | None = None
    _required_decision_id: str | None = None
    _required_input_id: str | None = None


@dataclass
class KnowledgeRequirement(BaseElement):
    required_knowledge: BusinessKnowledgeModel | None = None
    _required_knowledge_id: str | None = None


@dataclass
class AuthorityRequirement(BaseElement):
    required_authority: KnowledgeSource | None = None
    _required_authority_id: str | None = None


@dataclass
class DecisionService(BaseElement):
    decisions: list[Decision] = field(default_factory=list)
    output_decisions: list[Decision] = field(default_factory=list)
    input_data: list[InputData] = field(default_factory=list)


@dataclass
class LiteralExpression(BaseElement):
    body: str | None = None


@dataclass
class UnaryTests(BaseElement):
    body: str | None = None


@dataclass
class InputClause(BaseElement):
    input_expression: FormalExpression | LiteralExpression | None = None
    input_values: list[Any] | None = None


@dataclass
class OutputClause(BaseElement):
    name: str | None = None
    output_values: list[Any] | None = None
    default_output: LiteralExpression | None = None


@dataclass
class DecisionRule(BaseElement):
    input_entries: list[UnaryTests | FormalExpression] = field(default_factory=list)
    output_entries: list[LiteralExpression | FormalExpression] = field(default_factory=list)


@dataclass
class DecisionTable(BaseElement):
    hit_policy: str = "UNIQUE"
    aggregation: str | None = None
    inputs: list[InputClause] = field(default_factory=list)
    outputs: list[OutputClause] = field(default_factory=list)
    rules: list[DecisionRule] = field(default_factory=list)
    columns: list[str] = field(default_factory=list)
    rows: list[list[str]] = field(default_factory=list)


@dataclass
class Decision(FlowNode):
    logic: DecisionLogicType = DecisionLogicType.DECISION_TABLE
    expression: Script | None = None
    table_data: DecisionTable | None = None
    decision_table: DecisionTable | None = None
    information_requirements: list[InformationRequirement] = field(default_factory=list)
    knowledge_requirements: list[KnowledgeRequirement] = field(default_factory=list)
    authority_requirements: list[AuthorityRequirement] = field(default_factory=list)


@dataclass
class BusinessKnowledgeModel(FlowNode):
    logic: DecisionLogicType = DecisionLogicType.LITERAL_EXPRESSION
    expression: FormalExpression | None = None


@dataclass
class InputData(FlowNode):
    entity_ref: Entity | None = None


@dataclass
class KnowledgeSource(FlowNode):
    pass


@dataclass
class DMNDefinition:
    id: str
    name: str
    decisions: list[Decision] = field(default_factory=list)
    bkms: list[BusinessKnowledgeModel] = field(default_factory=list)
    input_data: list[InputData] = field(default_factory=list)
    knowledge_sources: list[KnowledgeSource] = field(default_factory=list)


@dataclass
class Binding:
    parameter: str = ""
    expression: str | None = None
    formal_parameter: str | None = None


@dataclass
class Invocation:
    called_element_ref: str = ""
    called_element_type: str = ""
    bindings: list[Binding] = field(default_factory=list)
    expression_id: str = ""


@dataclass
class ContextEntry:
    key: str = ""
    value_expression: str | None = None
    variable_name: str | None = None


@dataclass
class Context:
    entries: list[ContextEntry] = field(default_factory=list)
    result_type: str = "string"


@dataclass
class Relation:
    columns: list[str] = field(default_factory=list)
    rows: list[list[str]] = field(default_factory=list)
    result_type: str = "list"


@dataclass
class FormalParameter:
    name: str = ""
    type_ref: str = "string"


@dataclass
class FunctionDefinition:
    formal_parameters: list[FormalParameter] = field(default_factory=list)
    body_expression: str | None = None
    result_type: str = "string"


class DMNDocument(BaseOSDMDocument):
    dmn_definitions: list[DMNDefinition] = field(default_factory=list)


# Resolve forward reference to BPMNDiagram (referenced by BaseOSDMDocument)
from ...bpmn.models.bpmn_models import BPMNDiagram  # noqa: E402
DMNDocument.model_rebuild()

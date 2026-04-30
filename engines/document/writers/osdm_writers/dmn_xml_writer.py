# engines/document/writers/osdm_writers/dmn_xml_writer.py
"""
DMN 1.x XML Writer – serialises OSDM DMN definitions into DMN 1.x XML.
Handles decisions, business knowledge models, input data, knowledge sources,
information requirements, knowledge requirements, authority requirements,
decision tables, literal expressions, invocations, and contexts.
"""

from __future__ import annotations
from pathlib import Path
from typing import Optional, Dict, Any, List, Union
from xml.etree.ElementTree import Element, SubElement, tostring

from .base_osdm_writer import BaseOSDMWriter, OSDMWriteOptions
from ...models.osdm_models import (
    BaseOSDMDocument, DMNDocument,
    DMNDefinition,
    Decision,
    BusinessKnowledgeModel,
    InputData,
    KnowledgeSource,
    InformationRequirement,
    KnowledgeRequirement,
    AuthorityRequirement,
    DecisionTable,
    Script,
    FormalExpression,
    DecisionLogicType,
)
from ...models.base import BaseDocument


# ── Namespaces ────────────────────────────────────────────────────
DMN_NS = "https://www.omg.org/spec/DMN/20191111/MODEL/"
DMNDI_NS = "https://www.omg.org/spec/DMN/20191111/DMNDI/"
DI_NS = "http://www.omg.org/spec/DD/20100524/DI"
DC_NS = "http://www.omg.org/spec/DD/20100524/DC"


class DMNXMLWriter(BaseOSDMWriter):
    """Serialises an DMNDocument to DMN 1.x XML."""

    name = "dmn_xml"
    supported_extensions = (".dmn",)

    def __init__(self, options: Optional[OSDMWriteOptions] = None):
        super().__init__(options)
        self._id_map: Dict[str, str] = {}
        self._next_internal_id = 0

    async def _write_design(self, base_document: BaseOSDMDocument) -> bytes:
        document = cast(DMNDocument, base_document)
        root = Element(f"{{{DMN_NS}}}definitions", {
            "xmlns": DMN_NS,
            "xmlns:dmndi": DMNDI_NS,
            "xmlns:di": DI_NS,
            "xmlns:dc": DC_NS,
            "id": self._new_id("definitions"),
            "name": document.title or "DMN Definitions",
        })

        if not document or not document.dmn_definitions:
            xml_bytes = tostring(root, encoding="unicode", method="xml")
            return xml_bytes.encode(self.options.encoding or "utf-8")

        # DMN files typically have a single definition with multiple decisions inside,
        # but our model stores multiple DMNDefinition objects. We'll merge them into one
        # definitions element.
        for dmn_def in document.dmn_definitions:
            # Write input data first (so they can be referenced)
            for input_data in dmn_def.input_data:
                self._write_input_data(root, input_data)

            # Write BKMs
            for bkm in dmn_def.bkms:
                self._write_bkm(root, bkm)

            # Write decisions (after all referenced elements)
            for decision in dmn_def.decisions:
                self._write_decision(root, decision)

        xml_bytes = tostring(root, encoding="unicode", method="xml")
        return xml_bytes.encode(self.options.encoding or "utf-8")

    def get_supported_media_types(self) -> list[str]:
        return ["application/xml"]

    def get_supported_extensions(self) -> list[str]:
        return list(self.supported_extensions)

    # ── Helpers ────────────────────────────────────────────────────
    def _new_id(self, prefix: str) -> str:
        self._next_internal_id += 1
        return f"{prefix}_{self._next_internal_id}"

    def _obj_id(self, obj) -> str:
        if isinstance(obj, BaseElement):
            return obj.id
        return str(id(obj))

    def _add_dmn_element(self, parent: Element, tag: str, obj=None, **attrs):
        if obj is not None:
            attrs.setdefault("id", self._obj_id(obj))
        return SubElement(parent, f"{{{DMN_NS}}}{tag}", attrs)

    # ── Decision ──────────────────────────────────────────────────
    def _write_decision(self, root: Element, decision: Decision):
        elem = self._add_dmn_element(root, "decision", decision, name=decision.name or "")
        # Information requirements
        for ir in decision.information_requirements:
            self._write_information_requirement(elem, ir)
        # Knowledge requirements
        for kr in decision.knowledge_requirements:
            self._write_knowledge_requirement(elem, kr)
        # Authority requirements
        for ar in decision.authority_requirements:
            self._write_authority_requirement(elem, ar)

        # Decision logic
        if decision.logic == DecisionLogicType.DECISION_TABLE and decision.table_data:
            self._write_decision_table(elem, decision.table_data)
        elif decision.logic == DecisionLogicType.LITERAL_EXPRESSION and decision.expression:
            self._write_literal_expression(elem, decision.expression)
        elif decision.logic == DecisionLogicType.INVOCATION:
            self._write_invocation(elem, decision)
        elif decision.logic == DecisionLogicType.CONTEXT:
            self._write_context(elem, decision)
        elif decision.logic == DecisionLogicType.RELATION:
            self._write_relation(elem, decision)
        elif decision.logic == DecisionLogicType.FUNCTION_DEFINITION:
            self._write_function_definition(elem, decision)
        # else: no logic

    def _write_information_requirement(self, parent: Element, ir: InformationRequirement):
        elem = self._add_dmn_element(parent, "informationRequirement", ir)
        if ir.required_decision:
            req_dec = self._add_dmn_element(elem, "requiredDecision", None, href=f"#{self._obj_id(ir.required_decision)}")
        if ir.required_input:
            req_input = self._add_dmn_element(elem, "requiredInput", None, href=f"#{self._obj_id(ir.required_input)}")

    def _write_knowledge_requirement(self, parent: Element, kr: KnowledgeRequirement):
        elem = self._add_dmn_element(parent, "knowledgeRequirement", kr)
        if kr.required_knowledge:
            self._add_dmn_element(elem, "requiredKnowledge", None, href=f"#{self._obj_id(kr.required_knowledge)}")

    def _write_authority_requirement(self, parent: Element, ar: AuthorityRequirement):
        elem = self._add_dmn_element(parent, "authorityRequirement", ar)
        if ar.required_authority:
            self._add_dmn_element(elem, "requiredAuthority", None, href=f"#{self._obj_id(ar.required_authority)}")

    # ── Decision logic writers ────────────────────────────────────
    def _write_decision_table(self, parent: Element, table: DecisionTable):
        dt_elem = self._add_dmn_element(parent, "decisionTable", table)
        # Output columns as input/output entries
        for col_name in table.columns:
            # DMN distinguishes input and output columns; we'll just use generic input/output based on position
            if col_name.startswith("output"):
                SubElement(dt_elem, f"{{{DMN_NS}}}output", {"label": col_name, "typeRef": "string"})
            else:
                SubElement(dt_elem, f"{{{DMN_NS}}}input", {"label": col_name})
        # Rules
        for row in table.rows:
            rule_elem = SubElement(dt_elem, f"{{{DMN_NS}}}rule")
            for col_name in table.columns:
                val = row.get(col_name, "")
                if col_name.startswith("output"):
                    out_elem = SubElement(rule_elem, f"{{{DMN_NS}}}outputEntry")
                    text_elem = SubElement(out_elem, f"{{{DMN_NS}}}text")
                    text_elem.text = str(val)
                else:
                    in_elem = SubElement(rule_elem, f"{{{DMN_NS}}}inputEntry")
                    text_elem = SubElement(in_elem, f"{{{DMN_NS}}}text")
                    text_elem.text = str(val)

    def _write_literal_expression(self, parent: Element, expr: Script):
        le_elem = self._add_dmn_element(parent, "literalExpression", expr)
        if expr.script_body:
            text_elem = SubElement(le_elem, f"{{{DMN_NS}}}text")
            text_elem.text = expr.script_body
        if expr.script_language:
            le_elem.set("expressionLanguage", expr.script_language.value)

    def _write_invocation(self, parent: Element, decision: Decision):
        inv_elem = self._add_dmn_element(parent, "invocation", decision)
        # invocation requires a called BKM or Decision Service; we don't have that ref in the model yet.
        # We'll write a placeholder.
        # If decision.expression is a reference to a BKM? We don't have a dedicated field. We'll leave empty.
        pass

    def _write_context(self, parent: Element, decision: Decision):
        ctx_elem = self._add_dmn_element(parent, "context", decision)
        # context entries would be missing from model; placeholder
        pass

    def _write_relation(self, parent: Element, decision: Decision):
        rel_elem = self._add_dmn_element(parent, "relation", decision)
        # relation columns and rows missing; placeholder
        pass

    def _write_function_definition(self, parent: Element, decision: Decision):
        fd_elem = self._add_dmn_element(parent, "functionDefinition", decision)
        # function definition missing; placeholder
        pass

    # ── Business Knowledge Model ───────────────────────────────────
    def _write_bkm(self, root: Element, bkm: BusinessKnowledgeModel):
        elem = self._add_dmn_element(root, "businessKnowledgeModel", bkm, name=bkm.name or "")
        if bkm.logic == DecisionLogicType.LITERAL_EXPRESSION and bkm.expression:
            self._write_literal_expression(elem, bkm.expression)
        # BKMs can also contain decision tables etc., but not yet modelled

    # ── Input Data ────────────────────────────────────────────────
    def _write_input_data(self, root: Element, input_data: InputData):
        elem = self._add_dmn_element(root, "inputData", input_data, name=input_data.name or "")
        # If it references an MSDM entity, we could output typeRef? DMN uses ItemDefinition, not MSDM directly.
        # We'll store the reference as an extension attribute.
        if input_data.entity_ref:
            elem.set("typeRef", f"msdm:{input_data.entity_ref.document_id if input_data.entity_ref else ''}")

    # ── Knowledge Source ──────────────────────────────────────────
    def _write_knowledge_source(self, root: Element, ks: KnowledgeSource):
        self._add_dmn_element(root, "knowledgeSource", ks, name=ks.name or "")
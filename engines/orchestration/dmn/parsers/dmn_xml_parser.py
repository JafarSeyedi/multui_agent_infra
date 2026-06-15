# engines/document/parsers/osdm_parsers/dmn_xml_parser.py
"""
DMN 1.x XML Parser – converts a .dmn file into a DMNDocument (unified OSDM).

Mapping rules:
- <definitions> → DMNDefinition
- <decision> → Decision (with decision table, literal expression, etc.)
- <businessKnowledgeModel> → BusinessKnowledgeModel
- <inputData> → InputData
- <knowledgeSource> → KnowledgeSource (stored in DMNDefinition.knowledge_sources)
- <informationRequirement> → InformationRequirement (links to Decision / InputData)
- <knowledgeRequirement> → KnowledgeRequirement
- <authorityRequirement> → AuthorityRequirement
- <decisionTable> → DecisionTable (columns and rules)
- <literalExpression> → Script (expression body)
- All references are resolved in a second pass using temporary ID fields.
"""
from __future__ import annotations

import uuid
from typing import Union
from xml.etree import ElementTree as ET

from engines.document.models.media_types import MEDIA_TYPES
from ..models.dmn_models import (
    AuthorityRequirement, BaseOSDMDocument, BusinessKnowledgeModel, Decision,
    DecisionLogicType, DecisionTable, DMNDefinition, DMNDocument,
    InformationRequirement, InputData, KnowledgeRequirement, KnowledgeSource,
)
from ...bpmn.models.bpmn_models import Script, ScriptLanguage
from engines.document.parsers.base import ParseOptions
from ...models.base_osdm_parser import BaseOSDMParser

DMN_NS = "https://www.omg.org/spec/DMN/20191111/MODEL/"
NS = {"dmn": DMN_NS}


class DMNXMLParser(BaseOSDMParser):
    """Parser for DMN 1.x XML files (.dmn)."""

    name = "dmn_xml"
    supported_extensions = (".dmn",)

    async def _parse_to_document(
        self, data: bytes, source_name: str, options: ParseOptions
    ) -> BaseOSDMDocument:
        encoding = options.encoding or "utf-8"
        text = data.decode(encoding)
        root = ET.fromstring(text)

        doc = DMNDocument(
            document_id=root.get("id", source_name),
            title=root.get("name", source_name),
            media_type=MEDIA_TYPES.get("dmn_xml", MEDIA_TYPES["xml"])
        )
        doc.source_file = source_name

        dmn_def = self._parse_definitions(root)
        doc.dmn_definitions.append(dmn_def)
        return doc

    def _parse_definitions(self, root: ET.Element) -> DMNDefinition:
        dmn_def = DMNDefinition(
            id=root.get("id", ""),
            name=root.get("name", ""),
        )

        # First pass: collect all elements by ID
        decisions_map: dict[str, Decision] = {}
        input_data_map: dict[str, InputData] = {}
        bkm_map: dict[str, BusinessKnowledgeModel] = {}
        ks_map: dict[str, KnowledgeSource] = {}

        # Also keep a list of elements with unresolved references for later resolution
        pending_items: list[tuple[ET.Element, Decision | BusinessKnowledgeModel]] = []

        for child in root:
            tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
            if tag == "decision":
                dec = self._parse_decision(child)
                decisions_map[dec.id] = dec
                dmn_def.decisions.append(dec)
                pending_items.append((child, dec))
            elif tag == "businessKnowledgeModel":
                bkm = self._parse_bkm(child)
                bkm_map[bkm.id] = bkm
                dmn_def.bkms.append(bkm)
                pending_items.append((child, bkm))
            elif tag == "inputData":
                inp = self._parse_input_data(child)
                input_data_map[inp.id] = inp
                dmn_def.input_data.append(inp)
            elif tag == "knowledgeSource":
                ks = self._parse_knowledge_source(child)
                ks_map[ks.id] = ks
                dmn_def.knowledge_sources.append(ks)

        # Second pass: resolve references using the maps
        for elem, target in pending_items:
            if isinstance(target, Decision):
                self._resolve_decision_requirements(elem, target, decisions_map, input_data_map, bkm_map, ks_map)
                self._parse_decision_logic(elem, target)
            elif isinstance(target, BusinessKnowledgeModel):
                self._parse_decision_logic(elem, target)

        return dmn_def

    def _parse_decision(self, elem: ET.Element) -> Decision:
        return Decision(
            id=elem.get("id", ""),
            name=elem.get("name", ""),
        )

    def _resolve_decision_requirements(
        self,
        elem: ET.Element,
        dec: Decision,
        dec_map: dict[str, Decision],
        inp_map: dict[str, InputData],
        bkm_map: dict[str, BusinessKnowledgeModel],
        ks_map: dict[str, KnowledgeSource]
    ) -> None:
        for child in elem:
            tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
            if tag == "informationRequirement":
                ir = self._parse_information_requirement(child)
                # Resolve references using the stored temporary IDs
                if ir._required_decision_id and ir._required_decision_id in dec_map:
                    ir.required_decision = dec_map[ir._required_decision_id]
                if ir._required_input_id and ir._required_input_id in inp_map:
                    ir.required_input = inp_map[ir._required_input_id]
                dec.information_requirements.append(ir)
            elif tag == "knowledgeRequirement":
                kr = self._parse_knowledge_requirement(child)
                if kr._required_knowledge_id and kr._required_knowledge_id in bkm_map:
                    kr.required_knowledge = bkm_map[kr._required_knowledge_id]
                dec.knowledge_requirements.append(kr)
            elif tag == "authorityRequirement":
                ar = self._parse_authority_requirement(child)
                if ar._required_authority_id and ar._required_authority_id in ks_map:
                    ar.required_authority = ks_map[ar._required_authority_id]
                dec.authority_requirements.append(ar)

    def _parse_information_requirement(self, elem: ET.Element) -> InformationRequirement:
        ir = InformationRequirement(id=elem.get("id", ""))
        req_dec = elem.find("dmn:requiredDecision", NS)
        if req_dec is not None:
            ir._required_decision_id = req_dec.get("href", "").lstrip("#")
        req_input = elem.find("dmn:requiredInput", NS)
        if req_input is not None:
            ir._required_input_id = req_input.get("href", "").lstrip("#")
        return ir

    def _parse_knowledge_requirement(self, elem: ET.Element) -> KnowledgeRequirement:
        kr = KnowledgeRequirement(id=elem.get("id", ""))
        req_knowledge = elem.find("dmn:requiredKnowledge", NS)
        if req_knowledge is not None:
            kr._required_knowledge_id = req_knowledge.get("href", "").lstrip("#")
        return kr

    def _parse_authority_requirement(self, elem: ET.Element) -> AuthorityRequirement:
        ar = AuthorityRequirement(id=elem.get("id", ""))
        req_auth = elem.find("dmn:requiredAuthority", NS)
        if req_auth is not None:
            ar._required_authority_id = req_auth.get("href", "").lstrip("#")
        return ar

    def _parse_decision_logic(
        self, elem: ET.Element, target: Decision | BusinessKnowledgeModel
    ) -> None:
        """
        Parse the logic (decisionTable, literalExpression, etc.) and set the
        appropriate fields on the target (Decision or BusinessKnowledgeModel).
        """
        for child in elem:
            tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
            if tag == "decisionTable":
                target.logic = DecisionLogicType.DECISION_TABLE
                # Only Decision has table_data; BusinessKnowledgeModel does not
                if isinstance(target, Decision):
                    target.table_data = self._parse_decision_table(child)
            elif tag == "literalExpression":
                target.logic = DecisionLogicType.LITERAL_EXPRESSION
                target.expression = self._parse_literal_expression(child)
            elif tag == "invocation":
                target.logic = DecisionLogicType.INVOCATION
            elif tag == "context":
                target.logic = DecisionLogicType.CONTEXT
            elif tag == "relation":
                target.logic = DecisionLogicType.RELATION
            elif tag == "functionDefinition":
                target.logic = DecisionLogicType.FUNCTION_DEFINITION

    def _parse_decision_table(self, elem: ET.Element) -> DecisionTable:
        dt = DecisionTable(id=elem.get("id", ""))
        # Parse inputs and outputs to build columns
        inputs = elem.findall("dmn:input", NS)
        outputs = elem.findall("dmn:output", NS)
        for inp in inputs:
            label = inp.get("label", "")
            dt.columns.append(label)
        for out in outputs:
            label = out.get("label", "")
            dt.columns.append(f"output:{label}")
        # Parse rules
        for rule_elem in elem.findall("dmn:rule", NS):
            row: list[str] = []
            # input entries
            in_entries = rule_elem.findall("dmn:inputEntry", NS)
            for idx, entry in enumerate(in_entries):
                text_elem = entry.find("dmn:text", NS)
                value = text_elem.text if text_elem is not None and text_elem.text is not None else ""
                row.append(value)
            out_entries = rule_elem.findall("dmn:outputEntry", NS)
            for idx, entry in enumerate(out_entries):
                text_elem = entry.find("dmn:text", NS)
                value = text_elem.text if text_elem is not None and text_elem.text is not None else ""
                row.append(value)
            dt.rows.append(row)
        return dt

    def _parse_literal_expression(self, elem: ET.Element) -> Script:
        text_elem = elem.find("dmn:text", NS)
        body = text_elem.text if text_elem is not None and text_elem.text is not None else ""
        language = elem.get("expressionLanguage", "")
        script_lang = ScriptLanguage.PYTHON
        if language in ("javascript", "js"):
            script_lang = ScriptLanguage.JS
        return Script(
            id=str(uuid.uuid4().hex),
            name=None,
            script_body=body,
            script_language=script_lang,
        )

    def _parse_bkm(self, elem: ET.Element) -> BusinessKnowledgeModel:
        return BusinessKnowledgeModel(
            id=elem.get("id", ""),
            name=elem.get("name", ""),
        )

    def _parse_input_data(self, elem: ET.Element) -> InputData:
        return InputData(
            id=elem.get("id", ""),
            name=elem.get("name", ""),
        )

    def _parse_knowledge_source(self, elem: ET.Element) -> KnowledgeSource:
        return KnowledgeSource(
            id=elem.get("id", ""),
            name=elem.get("name", ""),
        )
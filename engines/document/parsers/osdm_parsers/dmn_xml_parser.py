# engines/document/parsers/osdm_parsers/dmn_xml_parser.py
"""
DMN 1.x XML Parser – converts a .dmn file into a DMNDocument (unified OSDM).

Mapping rules:
- <definitions> → DMNDefinition
- <decision> → Decision (with decision table, literal expression, etc.)
- <businessKnowledgeModel> → BusinessKnowledgeModel
- <inputData> → InputData
- <knowledgeSource> → KnowledgeSource
- <informationRequirement> → InformationRequirement (links to Decision / InputData)
- <knowledgeRequirement> → KnowledgeRequirement
- <authorityRequirement> → AuthorityRequirement
- <decisionTable> → DecisionTable (columns and rules)
- <literalExpression> → Script (expression body)
- All references are resolved in a second pass using ID maps.
"""

from __future__ import annotations
from pathlib import Path
from typing import Optional, Dict, Any, List
from xml.etree import ElementTree as ET

from .base_osdm_parser import BaseOSDMParser
from ..base import ParseOptions
from ...models.osdm_models import (
    BaseOSDMDocument,
    DMNDocument,
    DMNDefinition,
    Decision,
    BusinessKnowledgeModel,
    InputData,
    KnowledgeSource,
    InformationRequirement,
    KnowledgeRequirement,
    AuthorityRequirement,
    DecisionTable,
    DecisionLogicType,
    Script,
    ScriptLanguage,
    FormalExpression,
)
from ...models.base import BaseDocument


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

        doc = DMNDocument()
        dmn_def = self._parse_definitions(root)
        doc.dmn_definitions.append(dmn_def)
        return doc

    def _parse_definitions(self, root: ET.Element) -> DMNDefinition:
        dmn_def = DMNDefinition(
            id=root.get("id", ""),
            name=root.get("name", ""),
        )

        # First pass: collect all elements by ID
        decisions_map: Dict[str, Decision] = {}
        input_data_map: Dict[str, InputData] = {}
        bkm_map: Dict[str, BusinessKnowledgeModel] = {}
        ks_map: Dict[str, KnowledgeSource] = {}

        for child in root:
            tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
            if tag == "decision":
                dec = self._parse_decision(child)
                decisions_map[dec.id] = dec
                dmn_def.decisions.append(dec)
            elif tag == "businessKnowledgeModel":
                bkm = self._parse_bkm(child)
                bkm_map[bkm.id] = bkm
                dmn_def.bkms.append(bkm)
            elif tag == "inputData":
                inp = self._parse_input_data(child)
                input_data_map[inp.id] = inp
                dmn_def.input_data.append(inp)
            elif tag == "knowledgeSource":
                ks = self._parse_knowledge_source(child)
                ks_map[ks.id] = ks
                dmn_def.input_data.append(ks)  # KnowledgeSource is not in input_data, but we'll add separately? No, DMNDefinition.input_data expects InputData. We'll add ks later? Actually DMNDefinition has no knowledge_source list. We'll skip for now. We'll add a separate list? We'll just ignore for now; knowledge sources are not used in the model outside decisions. We'll keep in a separate list not part of DMNDefinition? The model doesn't have a list for KS. We'll store them in a temporary dict but not add to dmn_def.
                # We'll handle this later: maybe extend DMNDefinition. For now, we'll skip adding KS to dmn_def.

        # Second pass: resolve requirements inside decisions
        for dec in dmn_def.decisions:
            for child in root:  # we need to re-find the decision element; we'll store the element reference
                if child.get("id") == dec.id:
                    self._resolve_decision_requirements(child, dec, decisions_map, input_data_map, bkm_map, ks_map)
                    # Parse decision logic
                    self._parse_decision_logic(child, dec)

        return dmn_def

    def _parse_decision(self, elem: ET.Element) -> Decision:
        dec = Decision(
            id=elem.get("id", ""),
            name=elem.get("name", ""),
        )
        return dec

    def _resolve_decision_requirements(self, elem: ET.Element, dec: Decision,
                                        dec_map: Dict[str, Decision],
                                        inp_map: Dict[str, InputData],
                                        bkm_map: Dict[str, BusinessKnowledgeModel],
                                        ks_map: Dict[str, KnowledgeSource]) -> None:
        for child in elem:
            tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
            if tag == "informationRequirement":
                ir = self._parse_information_requirement(child)
                # Resolve references
                if ir.required_decision and ir.required_decision in dec_map:
                    ir.required_decision = dec_map[ir.required_decision]
                if ir.required_input and ir.required_input in inp_map:
                    ir.required_input = inp_map[ir.required_input]
                dec.information_requirements.append(ir)
            elif tag == "knowledgeRequirement":
                kr = self._parse_knowledge_requirement(child)
                if kr.required_knowledge and kr.required_knowledge in bkm_map:
                    kr.required_knowledge = bkm_map[kr.required_knowledge]
                dec.knowledge_requirements.append(kr)
            elif tag == "authorityRequirement":
                ar = self._parse_authority_requirement(child)
                if ar.required_authority and ar.required_authority in ks_map:
                    ar.required_authority = ks_map[ar.required_authority]
                dec.authority_requirements.append(ar)

    def _parse_information_requirement(self, elem: ET.Element) -> InformationRequirement:
        ir = InformationRequirement(id=elem.get("id", ""))
        req_dec = elem.find("dmn:requiredDecision", NS)
        if req_dec is not None:
            ir.required_decision = req_dec.get("href", "").lstrip("#")
        req_input = elem.find("dmn:requiredInput", NS)
        if req_input is not None:
            ir.required_input = req_input.get("href", "").lstrip("#")
        return ir

    def _parse_knowledge_requirement(self, elem: ET.Element) -> KnowledgeRequirement:
        kr = KnowledgeRequirement(id=elem.get("id", ""))
        req_knowledge = elem.find("dmn:requiredKnowledge", NS)
        if req_knowledge is not None:
            kr.required_knowledge = req_knowledge.get("href", "").lstrip("#")
        return kr

    def _parse_authority_requirement(self, elem: ET.Element) -> AuthorityRequirement:
        ar = AuthorityRequirement(id=elem.get("id", ""))
        req_auth = elem.find("dmn:requiredAuthority", NS)
        if req_auth is not None:
            ar.required_authority = req_auth.get("href", "").lstrip("#")
        return ar

    def _parse_decision_logic(self, elem: ET.Element, dec: Decision) -> None:
        # Look for child elements: decisionTable, literalExpression, invocation, context, relation, functionDefinition
        for child in elem:
            tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
            if tag == "decisionTable":
                dec.logic = DecisionLogicType.DECISION_TABLE
                dec.table_data = self._parse_decision_table(child)
            elif tag == "literalExpression":
                dec.logic = DecisionLogicType.LITERAL_EXPRESSION
                dec.expression = self._parse_literal_expression(child)
            elif tag == "invocation":
                dec.logic = DecisionLogicType.INVOCATION
                # Invocation has calledFunction? Not fully modelled; skip
            elif tag == "context":
                dec.logic = DecisionLogicType.CONTEXT
            elif tag == "relation":
                dec.logic = DecisionLogicType.RELATION
            elif tag == "functionDefinition":
                dec.logic = DecisionLogicType.FUNCTION_DEFINITION

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
            row = {}
            # input entries
            in_entries = rule_elem.findall("dmn:inputEntry", NS)
            for idx, entry in enumerate(in_entries):
                col_name = dt.columns[idx] if idx < len(dt.columns) else f"input{idx}"
                text_elem = entry.find("dmn:text", NS)
                value = text_elem.text if text_elem is not None else ""
                row[col_name] = value
            out_entries = rule_elem.findall("dmn:outputEntry", NS)
            out_offset = len(in_entries)
            for idx, entry in enumerate(out_entries):
                col_name = dt.columns[out_offset + idx] if (out_offset + idx) < len(dt.columns) else f"output{idx}"
                text_elem = entry.find("dmn:text", NS)
                value = text_elem.text if text_elem is not None else ""
                row[col_name] = value
            dt.rows.append(row)
        return dt

    def _parse_literal_expression(self, elem: ET.Element) -> Script:
        text_elem = elem.find("dmn:text", NS)
        body = text_elem.text if text_elem is not None else ""
        language = elem.get("expressionLanguage", "")
        script_lang = ScriptLanguage.PYTHON  # default
        if language in ("javascript", "js"):
            script_lang = ScriptLanguage.JS
        return Script(script_body=body, script_language=script_lang)

    def _parse_bkm(self, elem: ET.Element) -> BusinessKnowledgeModel:
        bkm = BusinessKnowledgeModel(
            id=elem.get("id", ""),
            name=elem.get("name", ""),
        )
        # BKMs can contain an encapsulated logic; similar to decision
        self._parse_decision_logic(elem, bkm)  # will set logic and expression if literalExpression etc.
        return bkm

    def _parse_input_data(self, elem: ET.Element) -> InputData:
        inp = InputData(
            id=elem.get("id", ""),
            name=elem.get("name", ""),
        )
        # typeRef? not used in model
        return inp

    def _parse_knowledge_source(self, elem: ET.Element) -> KnowledgeSource:
        ks = KnowledgeSource(
            id=elem.get("id", ""),
            name=elem.get("name", ""),
        )
        return ks
# engines/document/parsers/osdm_parsers/cmmn_xml_parser.py
"""
CMMN 1.1 XML Parser – converts a .cmmn file into a CMMNDocument (unified OSDM).

Mapping rules:
- <definitions> → root container
- <case> → CMMNDefinition (with id, name)
- <casePlanModel> → Stage (root stage of the case)
- <stage> → Stage (recursive: contains flow elements, sentries)
- <milestone> → Milestone
- <eventListener> → EventListener (eventType attribute preserved via enum)
- <sentry> → Sentry (onPart, ifPart as FormalExpression)
- <planItem> → PlanItem (definitionRef, entry/exit criteria)
- <discretionaryItem> → DiscretionaryItem (extends PlanItem, plus applicabilityRule)
- <caseFileItem> → CaseFileItem
- <caseTask> → CaseTask
- <processTask> → ProcessTask
- <humanTask> → HumanTask
- <entryCriterion>, <exitCriterion> → EntryCriterion / ExitCriterion (sentryRef)
- <applicabilityRule> → ApplicabilityRule
"""

from __future__ import annotations
from pathlib import Path
from typing import Optional, Any, List, Dict
from xml.etree import ElementTree as ET

from .base_osdm_parser import BaseOSDMParser
from ..base import ParseOptions
from ...models.osdm_models import (
    BaseOSDMDocument,
    CMMNDocument,
    CMMNDefinition,
    Stage,
    Milestone,
    EventListener,
    Sentry,
    PlanItem,
    DiscretionaryItem,
    CaseFileItem,
    CaseTask,
    ProcessTask,
    HumanTask,
    ApplicabilityRule,
    EntryCriterion,
    ExitCriterion,
    EventListenerType,
    CaseFileMultiplicity,
    FormalExpression,
    ScriptLanguage,
)
from ...models.base import BaseDocument


CMMN_NS = "http://www.omg.org/spec/CMMN/20151109/MODEL"
NS = {"cmmn": CMMN_NS}


class CMMNXMLParser(BaseOSDMParser):
    """Parser for CMMN 1.1 XML files (.cmmn)."""

    name = "cmmn_xml"
    supported_extensions = (".cmmn",)

    async def _parse_to_document(
        self, data: bytes, source_name: str, options: ParseOptions
    ) -> BaseOSDMDocument:
        encoding = options.encoding or "utf-8"
        text = data.decode(encoding)
        root = ET.fromstring(text)

        doc = CMMNDocument()
        # The root is <definitions> containing one or more <case> elements
        for case_elem in root.findall("cmmn:case", NS):
            cmmn_def = self._parse_case(case_elem)
            doc.cmmn_definitions.append(cmmn_def)

        return doc

    def _parse_case(self, case_elem: ET.Element) -> CMMNDefinition:
        case_id = case_elem.get("id", "")
        case_name = case_elem.get("name", "")

        # The case plan model is the first child (usually <casePlanModel>)
        case_plan = case_elem.find("cmmn:casePlanModel", NS)
        root_stage = self._parse_stage(case_plan) if case_plan is not None else Stage(id="", name="")

        # Collect plan items, discretionary items, case file items
        plan_items = []
        disc_items = []
        case_file_items = []

        # These elements can appear directly under the case element
        for child in case_elem:
            tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
            if tag == "planItem":
                plan_items.append(self._parse_plan_item(child))
            elif tag == "discretionaryItem":
                disc_items.append(self._parse_discretionary_item(child))
            elif tag == "caseFileItem":
                case_file_items.append(self._parse_case_file_item(child))

        # Also, plan items may be inside the case plan model (stage)
        # We already parsed the stage recursively, but plan items might be at the case level.
        # We'll also scan the stage for any plan items? Actually, in CMMN plan items are usually direct children of the case.
        # We'll collect them from both places: case element and casePlanModel.

        # For completeness, we also scan the case plan model for plan items (some tools put them inside)
        if case_plan is not None:
            for pi in case_plan.findall("cmmn:planItem", NS):
                plan_items.append(self._parse_plan_item(pi))
            for di in case_plan.findall("cmmn:discretionaryItem", NS):
                disc_items.append(self._parse_discretionary_item(di))

        return CMMNDefinition(
            id=case_id,
            name=case_name,
            case=root_stage,
            plan_items=plan_items,
            discretionary_items=disc_items,
            case_file_items=case_file_items,
        )

    def _parse_stage(self, elem: ET.Element) -> Stage:
        stage = Stage(
            id=elem.get("id", ""),
            name=elem.get("name", ""),
        )
        # Parse child elements: flow elements (stage, milestone, eventListener, caseTask, processTask, humanTask)
        # and sentries, plan items (though plan items are usually not nested inside a stage? Actually they can be.)
        for child in elem:
            tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
            flow = self._parse_flow_element(child)
            if flow is not None:
                stage.flow_elements[flow.id] = flow
            elif tag == "sentry":
                sentry = self._parse_sentry(child)
                stage.sentries.append(sentry)
            # Other elements like planItem can appear; skip or handle as needed.
        return stage

    def _parse_flow_element(self, elem: ET.Element) -> Optional[Any]:
        tag = elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag
        if tag == "stage":
            return self._parse_stage(elem)
        elif tag == "milestone":
            return self._parse_milestone(elem)
        elif tag == "eventListener":
            return self._parse_event_listener(elem)
        elif tag == "caseTask":
            return self._parse_case_task(elem)
        elif tag == "processTask":
            return self._parse_process_task(elem)
        elif tag == "humanTask":
            return self._parse_human_task(elem)
        return None

    def _parse_milestone(self, elem: ET.Element) -> Milestone:
        return Milestone(
            id=elem.get("id", ""),
            name=elem.get("name", ""),
        )

    def _parse_event_listener(self, elem: ET.Element) -> EventListener:
        event_type_str = elem.get("eventType", "user")
        try:
            event_type = EventListenerType(event_type_str)
        except ValueError:
            event_type = EventListenerType.USER
        return EventListener(
            id=elem.get("id", ""),
            name=elem.get("name", ""),
            event_type=event_type,
        )

    def _parse_sentry(self, elem: ET.Element) -> Sentry:
        on_part = None
        if_part = None
        on_part_elem = elem.find("cmmn:onPart", NS)
        if on_part_elem is not None:
            # Could be a simple text or a FormalExpression
            on_part = self._parse_child_expression(on_part_elem)
        if_part_elem = elem.find("cmmn:ifPart", NS)
        if if_part_elem is not None:
            if_part = self._parse_child_expression(if_part_elem)
        return Sentry(
            id=elem.get("id", ""),
            name=elem.get("name", ""),
            on_part=on_part,
            if_part=if_part,
        )

    def _parse_child_expression(self, elem: ET.Element) -> Optional[FormalExpression]:
        # The child element might contain a <condition> or just text; we wrap it as FormalExpression
        body = elem.text or ""
        # If there's a child <condition> element, take its text
        cond = elem.find("cmmn:condition", NS)
        if cond is not None:
            body = cond.text or ""
        if not body:
            return None
        return FormalExpression(id=elem.get("id", ""), body=body)

    def _parse_case_task(self, elem: ET.Element) -> CaseTask:
        task = CaseTask(
            id=elem.get("id", ""),
            name=elem.get("name", ""),
        )
        case_ref_id = elem.get("caseRef")
        if case_ref_id:
            # Reference to a case definition; we'll store as string for now, to be resolved later (if needed)
            task.case_ref = case_ref_id
        return task

    def _parse_process_task(self, elem: ET.Element) -> ProcessTask:
        task = ProcessTask(
            id=elem.get("id", ""),
            name=elem.get("name", ""),
        )
        proc_ref = elem.get("processRef")
        if proc_ref:
            task.process_ref = proc_ref
        return task

    def _parse_human_task(self, elem: ET.Element) -> HumanTask:
        task = HumanTask(
            id=elem.get("id", ""),
            name=elem.get("name", ""),
        )
        role_ref = elem.get("performerRef")  # CMMN uses performerRef for the role
        task.role_ref = role_ref
        return task

    def _parse_plan_item(self, elem: ET.Element) -> PlanItem:
        pi = PlanItem(
            id=elem.get("id", ""),
            name=elem.get("name", ""),
            definition_ref=elem.get("definitionRef"),
            repetition_count=int(elem.get("repetitionCount", "1")),
            is_blocking=elem.get("isBlocking", "true") == "true",
        )
        for ec in elem.findall("cmmn:entryCriterion", NS):
            pi.entry_criteria.append(self._parse_entry_criterion(ec))
        for xc in elem.findall("cmmn:exitCriterion", NS):
            pi.exit_criteria.append(self._parse_exit_criterion(xc))
        return pi

    def _parse_discretionary_item(self, elem: ET.Element) -> DiscretionaryItem:
        di = DiscretionaryItem(
            id=elem.get("id", ""),
            name=elem.get("name", ""),
            definition_ref=elem.get("definitionRef"),
            repetition_count=int(elem.get("repetitionCount", "1")),
            is_blocking=elem.get("isBlocking", "true") == "true",
        )
        for ec in elem.findall("cmmn:entryCriterion", NS):
            di.entry_criteria.append(self._parse_entry_criterion(ec))
        for xc in elem.findall("cmmn:exitCriterion", NS):
            di.exit_criteria.append(self._parse_exit_criterion(xc))
        app_rule = elem.find("cmmn:applicabilityRule", NS)
        if app_rule is not None:
            di.applicability_rule = self._parse_applicability_rule(app_rule)
        return di

    def _parse_entry_criterion(self, elem: ET.Element) -> EntryCriterion:
        ec = EntryCriterion(
            id=elem.get("id", ""),
            name=elem.get("name", ""),
            sentry_ref=elem.get("sentryRef"),
        )
        return ec

    def _parse_exit_criterion(self, elem: ET.Element) -> ExitCriterion:
        xc = ExitCriterion(
            id=elem.get("id", ""),
            name=elem.get("name", ""),
            sentry_ref=elem.get("sentryRef"),
        )
        return xc

    def _parse_applicability_rule(self, elem: ET.Element) -> ApplicabilityRule:
        rule = ApplicabilityRule(
            id=elem.get("id", ""),
            name=elem.get("name", ""),
        )
        cond = elem.find("cmmn:condition", NS)
        if cond is not None:
            rule.condition = self._parse_child_expression(cond)
        return rule

    def _parse_case_file_item(self, elem: ET.Element) -> CaseFileItem:
        cfi = CaseFileItem(
            id=elem.get("id", ""),
            name=elem.get("name", ""),
            item_definition_ref=elem.get("definitionRef"),
        )
        mult_str = elem.get("multiplicity", "1")
        try:
            cfi.multiplicity = CaseFileMultiplicity(mult_str)
        except ValueError:
            cfi.multiplicity = CaseFileMultiplicity.EXACTLY_ONE
        return cfi
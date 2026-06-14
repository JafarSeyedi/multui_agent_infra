# engines/document/parsers/osdm_parsers/cmmn_xml_parser.py
"""
CMMN 1.1 XML Parser – converts a .cmmn file into a CMMNDocument (unified OSDM).

Uses temporary ID fields for cross‑references that cannot be resolved inside
the same document. All references that point to elements within the same
CMMN model (sentries, definitions of plan items, case references) are resolved.
External references (processRef, performerRef, definitionRef for case file items)
are left as None, but their original IDs are stored in temporary attributes.
"""
from __future__ import annotations

import uuid
import logging

from xml.etree import ElementTree as ET

from engines.document.models.media_types import MEDIA_TYPES
from ..models.cmmn_models import (
    ApplicabilityRule, BaseOSDMDocument, CaseFileItem, CaseFileMultiplicity,
    CaseTask, CMMNDefinition, CMMNDocument, DiscretionaryItem, EntryCriterion,
    EventListener, EventListenerType, ExitCriterion, FormalExpression,
    HumanTask, ItemDefinition, Milestone, PlanItem, Process, ProcessTask,
    ResourceRole, Sentry, Stage
)
from engines.document.parsers.base import ParseOptions
from ...models.parsers.base_osdm_parser import BaseOSDMParser

CMMN_NS = "http://www.omg.org/spec/CMMN/20151109/MODEL"
NS = {"cmmn": CMMN_NS}

logger = logging.getLogger(__name__)


class CMMNXMLParser(BaseOSDMParser):
    name = "cmmn_xml"
    supported_extensions = (".cmmn",)

    async def _parse_to_document(
        self, data: bytes, source_name: str, options: ParseOptions
    ) -> BaseOSDMDocument:
        encoding = options.encoding or "utf-8"
        text = data.decode(encoding)
        root = ET.fromstring(text)

        doc = CMMNDocument(
            document_id=root.get("id", source_name),
            title=root.get("name", source_name),
            media_type=MEDIA_TYPES.get("cmmn_xml", MEDIA_TYPES["xml"])
        )
        doc.source_file = source_name

        # First pass: parse all definitions
        definitions = []
        for case_elem in root.findall("cmmn:case", NS):
            cmmn_def = self._parse_case(case_elem)
            definitions.append(cmmn_def)
        doc.cmmn_definitions = definitions

        # Second pass: resolve internal references
        self._resolve_references(doc)

        return doc

    def _parse_case(self, case_elem: ET.Element) -> CMMNDefinition:
        case_id = case_elem.get("id", "")
        case_name = case_elem.get("name", "")

        case_plan = case_elem.find("cmmn:casePlanModel", NS)
        root_stage = self._parse_stage(case_plan) if case_plan is not None else Stage(id="", name="")

        plan_items = []
        disc_items = []
        case_file_items = []

        for child in case_elem:
            tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
            if tag == "planItem":
                plan_items.append(self._parse_plan_item(child))
            elif tag == "discretionaryItem":
                disc_items.append(self._parse_discretionary_item(child))
            elif tag == "caseFileItem":
                case_file_items.append(self._parse_case_file_item(child))

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
        for child in elem:
            tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
            flow = self._parse_flow_element(child)
            if flow is not None:
                stage.flow_elements[flow.id] = flow
            elif tag == "sentry":
                stage.sentries.append(self._parse_sentry(child))
        return stage

    def _parse_flow_element(self, elem: ET.Element):
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

    def _parse_child_expression(self, elem: ET.Element) -> FormalExpression | None:
        body = elem.text or ""
        cond = elem.find("cmmn:condition", NS)
        if cond is not None:
            body = cond.text or ""
        if not body:
            return None
        return FormalExpression(
            id=elem.get("id", str(uuid.uuid4().hex)),
            body=body
        )

    def _parse_case_task(self, elem: ET.Element) -> CaseTask:
        task = CaseTask(
            id=elem.get("id", ""),
            name=elem.get("name", ""),
        )
        case_ref_id = elem.get("caseRef")
        if case_ref_id:
            task._case_ref_id = case_ref_id
        return task

    def _parse_process_task(self, elem: ET.Element) -> ProcessTask:
        task = ProcessTask(
            id=elem.get("id", ""),
            name=elem.get("name", ""),
        )
        proc_ref = elem.get("processRef")
        if proc_ref:
            task._process_ref_id = proc_ref
        return task

    def _parse_human_task(self, elem: ET.Element) -> HumanTask:
        task = HumanTask(
            id=elem.get("id", ""),
            name=elem.get("name", ""),
        )
        role_ref = elem.get("performerRef")
        if role_ref:
            task._role_ref_id = role_ref
        return task

    def _parse_plan_item(self, elem: ET.Element) -> PlanItem:
        pi = PlanItem(
            id=elem.get("id", ""),
            name=elem.get("name", ""),
            _definition_ref_id=elem.get("definitionRef"),
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
            _definition_ref_id=elem.get("definitionRef"),
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
        return EntryCriterion(
            id=elem.get("id", ""),
            name=elem.get("name", ""),
            _sentry_ref_id=elem.get("sentryRef"),
        )

    def _parse_exit_criterion(self, elem: ET.Element) -> ExitCriterion:
        return ExitCriterion(
            id=elem.get("id", ""),
            name=elem.get("name", ""),
            _sentry_ref_id=elem.get("sentryRef"),
        )

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
        mult_str = elem.get("multiplicity", "1")
        try:
            multiplicity = CaseFileMultiplicity(mult_str)
        except ValueError:
            multiplicity = CaseFileMultiplicity.EXACTLY_ONE

        return CaseFileItem(
            id=elem.get("id", ""),
            name=elem.get("name", ""),
            _item_definition_ref_id=elem.get("definitionRef"),
            multiplicity=multiplicity,
        )

    # ── Second‑pass resolution ─────────────────────────────────────
    def _resolve_references(self, doc: CMMNDocument) -> None:
        """Resolve all internal references. External references are left as None."""
        # Collect all element maps
        all_cmmn_defs: dict[str, CMMNDefinition] = {}
        all_sentries: dict[str, Sentry] = {}
        all_stages: dict[str, Stage] = {}
        all_milestones: dict[str, Milestone] = {}
        all_event_listeners: dict[str, EventListener] = {}
        all_case_tasks: dict[str, CaseTask] = {}
        all_process_tasks: dict[str, ProcessTask] = {}
        all_human_tasks: dict[str, HumanTask] = {}
        all_plan_items: dict[str, PlanItem] = {}
        all_discretionary_items: dict[str, DiscretionaryItem] = {}
        all_case_file_items: dict[str, CaseFileItem] = {}
        _all_item_definitions: dict[str, ItemDefinition] = {}   # may come from an external registry; empty here

        def collect_from_stage(stage: Stage):
            all_stages[stage.id] = stage
            for flow in stage.flow_elements.values():
                if isinstance(flow, Stage):
                    collect_from_stage(flow)
                elif isinstance(flow, Milestone):
                    all_milestones[flow.id] = flow
                elif isinstance(flow, EventListener):
                    all_event_listeners[flow.id] = flow
                elif isinstance(flow, CaseTask):
                    all_case_tasks[flow.id] = flow
                elif isinstance(flow, ProcessTask):
                    all_process_tasks[flow.id] = flow
                elif isinstance(flow, HumanTask):
                    all_human_tasks[flow.id] = flow
            for sentry in stage.sentries:
                all_sentries[sentry.id] = sentry

        for cmmn_def in doc.cmmn_definitions:
            all_cmmn_defs[cmmn_def.id] = cmmn_def
            collect_from_stage(cmmn_def.case)
            for pi in cmmn_def.plan_items:
                all_plan_items[pi.id] = pi
            for di in cmmn_def.discretionary_items:
                all_discretionary_items[di.id] = di
            for cfi in cmmn_def.case_file_items:
                all_case_file_items[cfi.id] = cfi

        # Resolve PlanItem.definition_ref
        for pi in all_plan_items.values():
            if pi._definition_ref_id:
                ref = pi._definition_ref_id
                if ref in all_stages:
                    pi.definition_ref = all_stages[ref]
                elif ref in all_milestones:
                    pi.definition_ref = all_milestones[ref]
                elif ref in all_event_listeners:
                    pi.definition_ref = all_event_listeners[ref]
                else:
                    logger.warning(f"PlanItem {pi.id}: definitionRef '{ref}' not found")
        for di in all_discretionary_items.values():
            if di._definition_ref_id:
                ref = di._definition_ref_id
                if ref in all_stages:
                    di.definition_ref = all_stages[ref]
                elif ref in all_milestones:
                    di.definition_ref = all_milestones[ref]
                elif ref in all_event_listeners:
                    di.definition_ref = all_event_listeners[ref]
                else:
                    logger.warning(f"DiscretionaryItem {di.id}: definitionRef '{ref}' not found")

        # Resolve EntryCriterion.sentry_ref and ExitCriterion.sentry_ref
        for pi in all_plan_items.values():
            for ec in pi.entry_criteria:
                if ec._sentry_ref_id and ec._sentry_ref_id in all_sentries:
                    ec.sentry_ref = all_sentries[ec._sentry_ref_id]
                elif ec._sentry_ref_id:
                    logger.warning(f"EntryCriterion {ec.id}: sentryRef '{ec._sentry_ref_id}' not found")
            for xc in pi.exit_criteria:
                if xc._sentry_ref_id and xc._sentry_ref_id in all_sentries:
                    xc.sentry_ref = all_sentries[xc._sentry_ref_id]
                elif xc._sentry_ref_id:
                    logger.warning(f"ExitCriterion {xc.id}: sentryRef '{xc._sentry_ref_id}' not found")
        for di in all_discretionary_items.values():
            for ec in di.entry_criteria:
                if ec._sentry_ref_id and ec._sentry_ref_id in all_sentries:
                    ec.sentry_ref = all_sentries[ec._sentry_ref_id]
                elif ec._sentry_ref_id:
                    logger.warning(f"EntryCriterion {ec.id}: sentryRef '{ec._sentry_ref_id}' not found")
            for xc in di.exit_criteria:
                if xc._sentry_ref_id and xc._sentry_ref_id in all_sentries:
                    xc.sentry_ref = all_sentries[xc._sentry_ref_id]
                elif xc._sentry_ref_id:
                    logger.warning(f"ExitCriterion {xc.id}: sentryRef '{xc._sentry_ref_id}' not found")

        # Resolve CaseTask.case_ref (internal)
        for ct in all_case_tasks.values():
            if ct._case_ref_id and ct._case_ref_id in all_cmmn_defs:
                ct.case_ref = all_cmmn_defs[ct._case_ref_id]
            elif ct._case_ref_id:
                logger.warning(f"CaseTask {ct.id}: caseRef '{ct._case_ref_id}' not found (may be external)")

        # Resolve ProcessTask.process_ref – external by nature; keep None, but store ID
        for pt in all_process_tasks.values():
            if pt._process_ref_id:
                # Could be resolved from an external registry; here we only log.
                logger.debug(f"ProcessTask {pt.id} references external process '{pt._process_ref_id}'")
                pt.process_ref = None   # external; caller can resolve later

        # Resolve HumanTask.role_ref – external
        for ht in all_human_tasks.values():
            if ht._role_ref_id:
                logger.debug(f"HumanTask {ht.id} references role '{ht._role_ref_id}'")
                ht.role_ref = None

        # Resolve CaseFileItem.item_definition_ref – could be internal if ItemDefinition is defined in same file
        # CMMN allows inline item definitions? Not typical. We'll search in the document for <itemDefinition> elements
        # Since we have not parsed them, we assume external.
        for cfi in all_case_file_items.values():
            if cfi._item_definition_ref_id:
                logger.debug(f"CaseFileItem {cfi.id} references definition '{cfi._item_definition_ref_id}'")
                cfi.item_definition_ref = None
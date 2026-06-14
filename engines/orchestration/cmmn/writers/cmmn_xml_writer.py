# engines/document/writers/osdm_writers/cmmn_xml_writer.py
"""
CMMN 1.1 XML Writer – serialises OSDM CMMN definitions into CMMN 1.1 XML.
Handles cases, stages, milestones, event listeners, sentries, plan items,
discretionary items, case file items, and all associated elements.
"""
from __future__ import annotations

from typing import cast
from xml.etree.ElementTree import Element
from xml.etree.ElementTree import SubElement
from xml.etree.ElementTree import tostring

from ..models.cmmn_models import ApplicabilityRule
from ..models.cmmn_models import BaseElement
from ..models.cmmn_models import BaseOSDMDocument
from ..models.cmmn_models import CaseFileItem
from ..models.cmmn_models import CaseTask
from ..models.cmmn_models import CMMNDefinition
from ..models.cmmn_models import CMMNDocument
from ..models.cmmn_models import DiscretionaryItem
from ..models.cmmn_models import EntryCriterion
from ..models.cmmn_models import EventListener
from ..models.cmmn_models import ExitCriterion
from ..models.cmmn_models import HumanTask
from ..models.cmmn_models import Milestone
from ..models.cmmn_models import PlanItem
from ..models.cmmn_models import ProcessTask
from ..models.cmmn_models import Sentry
from ..models.cmmn_models import Stage
from ...models.writers.base_osdm_writer import BaseOSDMWriter
from ...models.writers.base_osdm_writer import OSDMWriteOptions


# ── Namespaces ────────────────────────────────────────────────────
CMMN_NS = "http://www.omg.org/spec/CMMN/20151109/MODEL"
CMMN_DI_NS = "http://www.omg.org/spec/CMMN/20151109/CMMNDI"
DI_NS = "http://www.omg.org/spec/DD/20100524/DI"
DC_NS = "http://www.omg.org/spec/DD/20100524/DC"
XSI_NS = "http://www.w3.org/2001/XMLSchema-instance"


class CMMNXMLWriter(BaseOSDMWriter):
    """Serialises an CMMNDocument to CMMN 1.1 XML."""

    name = "cmmn_xml"
    supported_extensions = (".cmmn",)

    def __init__(self, options: OSDMWriteOptions | None = None):
        super().__init__(options)
        self._id_map: dict[str, str] = {}
        self._next_internal_id = 0

    async def _write_design(self, base_document: BaseOSDMDocument) -> bytes:
        document = cast(CMMNDocument, base_document)
        if not document or not document.cmmn_definitions:
            # Return minimal definitions element
            root = Element(f"{{{CMMN_NS}}}definitions", {
                "xmlns": CMMN_NS,
                "xmlns:cmmndi": CMMN_DI_NS,
                "xmlns:di": DI_NS,
                "xmlns:dc": DC_NS,
                "xmlns:xsi": XSI_NS,
            })
            return tostring(root, encoding="unicode", method="xml").encode("utf-8")

        # CMMN files typically contain a single definitions with one or more cases
        root = Element(f"{{{CMMN_NS}}}definitions", {
            "xmlns": CMMN_NS,
            "xmlns:cmmndi": CMMN_DI_NS,
            "xmlns:di": DI_NS,
            "xmlns:dc": DC_NS,
            "xmlns:xsi": XSI_NS,
        })

        for cmmn_def in document.cmmn_definitions:
            self._write_case(root, cmmn_def)

        xml_bytes = tostring(root, encoding="unicode", method="xml")
        return xml_bytes.encode(getattr(self.options, "encoding", "utf-8") or "utf-8")

    def get_supported_media_types(self) -> list[str]:
        return ["application/xml"]

    def get_supported_extensions(self) -> list[str]:
        return list(self.supported_extensions)

    # ── Helpers ─────────────────────────────────────────────────────
    def _obj_id(self, obj: BaseElement) -> str:
        return obj.id

    def _add_cmmn_element(self, parent: Element, tag: str, obj: BaseElement | None = None, **attrs):
        if obj:
            attrs.setdefault("id", self._obj_id(obj))
        return SubElement(parent, f"{{{CMMN_NS}}}{tag}", attrs)

    # ── Case ────────────────────────────────────────────────────────
    def _write_case(self, root: Element, cmmn: CMMNDefinition):
        case_elem = self._add_cmmn_element(root, "case", None, id=cmmn.id, name=cmmn.name)
        case_plan_model = SubElement(case_elem, f"{{{CMMN_NS}}}casePlanModel", {
            "id": cmmn.case.id,
            "name": cmmn.case.name or "CasePlanModel",
        })
        # Write the contents of the case plan model (stage)
        self._write_stage_contents(case_plan_model, cmmn.case)
        # Write plan items
        for pi in cmmn.plan_items:
            self._write_plan_item(case_plan_model, pi)
        for di in cmmn.discretionary_items:
            self._write_discretionary_item(case_plan_model, di)
        for cfi in cmmn.case_file_items:
            self._write_case_file_item(case_elem, cfi)

    def _write_stage_contents(self, parent: Element, stage: Stage):
        """Recursively write the stage's flow elements (including nested stages)."""
        for flow in stage.flow_elements.values():
            if isinstance(flow, Stage):
                self._write_stage(parent, flow)
            elif isinstance(flow, Milestone):
                self._write_milestone(parent, flow)
            elif isinstance(flow, EventListener):
                self._write_event_listener(parent, flow)
            elif isinstance(flow, Sentry):
                self._write_sentry(parent, flow)
            elif isinstance(flow, CaseTask):
                self._write_case_task(parent, flow)
            elif isinstance(flow, ProcessTask):
                self._write_process_task(parent, flow)
            elif isinstance(flow, HumanTask):
                self._write_human_task(parent, flow)
        # Also write sentries defined at stage level
        for sentry in stage.sentries:
            self._write_sentry(parent, sentry)

    def _write_stage(self, parent: Element, stage: Stage):
        elem = self._add_cmmn_element(parent, "stage", stage, name=stage.name or "")
        self._write_stage_contents(elem, stage)

    def _write_milestone(self, parent: Element, milestone: Milestone):
        self._add_cmmn_element(parent, "milestone", milestone, name=milestone.name or "")

    def _write_event_listener(self, parent: Element, listener: EventListener):
        elem = self._add_cmmn_element(parent, "eventListener", listener, name=listener.name or "")
        if listener.event_type:
            elem.set("eventType", listener.event_type.value if hasattr(listener.event_type, 'value') else str(listener.event_type))

    def _write_sentry(self, parent: Element, sentry: Sentry):
        elem = self._add_cmmn_element(parent, "sentry", sentry, name=sentry.name or "")
        if sentry.on_part:
            self._write_expression(elem, "onPart", sentry.on_part)
        if sentry.if_part:
            self._write_expression(elem, "ifPart", sentry.if_part)

    def _write_case_task(self, parent: Element, task: CaseTask):
        elem = self._add_cmmn_element(parent, "caseTask", task, name=task.name or "")
        if task.case_ref:
            elem.set("caseRef", task.case_ref.id)

    def _write_process_task(self, parent: Element, task: ProcessTask):
        elem = self._add_cmmn_element(parent, "processTask", task, name=task.name or "")
        if task.process_ref:
            elem.set("processRef", task.process_ref.id)

    def _write_human_task(self, parent: Element, task: HumanTask):
        self._add_cmmn_element(parent, "humanTask", task, name=task.name or "")

    # ── Plan Items / Discretionary Items ───────────────────────────
    def _write_plan_item(self, parent: Element, pi: PlanItem):
        elem = self._add_cmmn_element(parent, "planItem", pi, name=pi.name or "")
        if pi.definition_ref:
            elem.set("definitionRef", self._obj_id(pi.definition_ref))
        if pi.entry_criteria:
            for ec in pi.entry_criteria:
                self._write_entry_criterion(elem, ec)
        if pi.exit_criteria:
            for xc in pi.exit_criteria:
                self._write_exit_criterion(elem, xc)
        elem.set("repetitionCount", str(pi.repetition_count))
        elem.set("isBlocking", str(pi.is_blocking).lower())

    def _write_discretionary_item(self, parent: Element, di: DiscretionaryItem):
        elem = self._write_plan_item(parent, di)  # reuse base fields
        elem.tag = f"{{{CMMN_NS}}}discretionaryItem"
        if di.applicability_rule:
            self._write_applicability_rule(elem, di.applicability_rule)

    def _write_entry_criterion(self, parent: Element, ec: EntryCriterion):
        elem = self._add_cmmn_element(parent, "entryCriterion", ec, name=ec.name or "")
        if ec.sentry_ref:
            elem.set("sentryRef", self._obj_id(ec.sentry_ref))

    def _write_exit_criterion(self, parent: Element, xc: ExitCriterion):
        elem = self._add_cmmn_element(parent, "exitCriterion", xc, name=xc.name or "")
        if xc.sentry_ref:
            elem.set("sentryRef", self._obj_id(xc.sentry_ref))

    def _write_applicability_rule(self, parent: Element, rule: ApplicabilityRule):
        elem = self._add_cmmn_element(parent, "applicabilityRule", rule, name=rule.name or "")
        if rule.condition:
            self._write_expression(elem, "condition", rule.condition)

    # ── Case File Items ────────────────────────────────────────────
    def _write_case_file_item(self, parent: Element, cfi: CaseFileItem):
        elem = self._add_cmmn_element(parent, "caseFileItem", cfi, name=cfi.name or "")
        if cfi.item_definition_ref:
            elem.set("definitionRef", self._obj_id(cfi.item_definition_ref))
        if cfi.multiplicity:
            elem.set("multiplicity", cfi.multiplicity.value if hasattr(cfi.multiplicity, 'value') else str(cfi.multiplicity))

    # ── Expressions ─────────────────────────────────────────────────
    def _write_expression(self, parent: Element, tag: str, expr):
        elem = self._add_cmmn_element(parent, tag, expr)
        if hasattr(expr, 'body') and expr.body:
            elem.text = expr.body
        if hasattr(expr, 'language') and expr.language:
            lang_val = expr.language.value if hasattr(expr.language, 'value') else str(expr.language)
            elem.set("language", lang_val)

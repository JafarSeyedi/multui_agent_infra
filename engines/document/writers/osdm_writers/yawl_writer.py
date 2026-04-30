# engines/document/writers/osdm_writers/yawl_writer.py
"""
YAWL Writer – serialises an OSDM StateMachineModel (YAWL net) to YAWL XML.

Relies entirely on typed OSDM fields:
- StateMachineModel.model_type == "yawl_net"
- Place                              → YAWL condition
- PnTransition (+ YAWLTaskDecorator) → YAWL task
- Arc                                → flow relation
- CancellationRegion                 → <cancellationSet>
"""

from __future__ import annotations
from pathlib import Path
from typing import Optional, Dict, Any, List, cast
from xml.etree.ElementTree import Element, SubElement, tostring

from .base_osdm_writer import BaseOSDMWriter, OSDMWriteOptions
from ...models.osdm_models import (
    BaseOSDMDocument,
    StateMachineDocument,
    StateMachineModel,
    StateMachineRegion,
    Place,
    PnTransition,
    Arc,
    CancellationRegion,
    YAWLTaskDecorator,
    BaseElement,
)
from ...models.base import BaseDocument

YAWL_NS = "http://www.yawlfoundation.org/yawlschema"
XSI_NS = "http://www.w3.org/2001/XMLSchema-instance"


class YAWLWriter(BaseOSDMWriter):
    """Serialises a YAWL net (StateMachineModel) to YAWL XML."""

    name = "yawl"
    supported_extensions = (".yawl",)

    def __init__(self, options: Optional[OSDMWriteOptions] = None):
        super().__init__(options)

    async def _write_design(self, base_document: BaseOSDMDocument) -> bytes:
        document = cast(StateMachineDocument, base_document)
        root = Element("specificationSet", {
            "xmlns": YAWL_NS,
            "xmlns:xsi": XSI_NS,
        })

        for sm in document.state_machines:
            if sm.model_type == "yawl_net":
                self._write_specification(root, sm)

        xml_bytes = tostring(root, encoding="unicode", method="xml")
        return xml_bytes.encode(self.options.encoding or "utf-8")

    def get_supported_media_types(self) -> list[str]:
        return ["application/xml"]

    def get_supported_extensions(self) -> list[str]:
        return list(self.supported_extensions)

    # ── Specification ──────────────────────────────────────────────
    def _write_specification(self, root: Element, sm: StateMachineModel) -> None:
        spec = SubElement(root, "specification", {"id": sm.id})
        if sm.name:
            spec.set("name", sm.name)

        # Documentation (if present)
        if sm.description:
            doc = SubElement(spec, f"{{{YAWL_NS}}}documentation")
            doc.text = sm.description

        # Write the root net (top region)
        self._write_net(spec, sm)

    def _write_net(self, parent: Element, sm: StateMachineModel) -> None:
        net = SubElement(parent, "net", {"id": sm.id})
        if sm.name:
            net.set("name", sm.name)

        region = sm.top_region

        # Conditions (places) and tasks (transitions)
        for state in region.states:
            if isinstance(state, Place):
                self._write_condition(net, state)
            elif isinstance(state, PnTransition):
                self._write_task(net, state)

        # Arcs
        for trans in region.transitions:
            if isinstance(trans, Arc):
                self._write_arc(net, trans)

        # Cancellation regions
        for cr in sm.cancellation_regions:
            cancel_set = SubElement(net, "cancellationSet", {"id": cr.id})
            for nid in cr.enclosed_node_ids:
                SubElement(cancel_set, "contains", {"id": nid})

    # ── Condition (Place) ─────────────────────────────────────────
    def _write_condition(self, parent: Element, place: Place) -> None:
        cond = SubElement(parent, "condition", {"id": place.id})
        if place.name:
            cond.set("name", place.name)
        if place.initial_marking:
            im = SubElement(cond, "initialMarking")
            im.text = str(place.initial_marking)

    # ── Task (PnTransition) ───────────────────────────────────────
    def _write_task(self, parent: Element, trans: PnTransition) -> None:
        task = SubElement(parent, "task", {"id": trans.id})
        if trans.name:
            task.set("name", trans.name)

        # YAWL‑specific decorator
        decorator = trans.yawl_decorator
        if decorator:
            if decorator.join_type and decorator.join_type != YAWLJoinType.NONE:
                task.set("join", decorator.join_type.value)
            if decorator.split_type and decorator.split_type != YAWLSplitType.NONE:
                task.set("split", decorator.split_type.value)
            # if decorator.custom_form:
            #     task.set("customForm", decorator.custom_form)
            # if decorator.documentation:
            #     doc = SubElement(task, f"{{{YAWL_NS}}}documentation")
            #     doc.text = decorator.documentation

    # ── Arc ───────────────────────────────────────────────────────
    def _write_arc(self, parent: Element, arc: Arc) -> None:
        source_id = arc.source.id if arc.source else None
        target_id = arc.target.id if arc.target else None
        if not source_id or not target_id:
            return

        flow = SubElement(parent, "flow", {
            "id": arc.id,
            "source": source_id,
            "target": target_id,
        })
        if arc.weight != 1:
            insc = SubElement(flow, "inscription")
            insc.text = str(arc.weight)
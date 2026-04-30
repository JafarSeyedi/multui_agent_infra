# engines/document/writers/osdm_writers/pnml_xml_writer.py
"""
PNML XML Writer – serialises OSDM StateMachineModel (unified) to PNML.
Petri nets are detected by annotations placed by the PNML parser:
  - model annotation "model_type" = "petri_net"
  - State annotations: "petri_type" = "place" or "transition"
  - Place extra: "initial_marking", "capacity"
  - Transition extra: "timing_expression"
  - StateTransition annotations: "petri_type" = "arc"
  - Arc extra: "weight", "inhibitor", "reset"
  - Reference annotations: "reference_place", "reference_transition" (with target id)
"""

from __future__ import annotations
from pathlib import Path
from typing import Optional, Dict, Any, List, cast
from xml.etree.ElementTree import Element, SubElement, tostring

from .base_osdm_writer import BaseOSDMWriter, OSDMWriteOptions
from ...models.osdm_models import (
    BaseOSDMDocument, StateMachineDocument,
    StateMachineModel,
    StateMachineRegion,
    State,
    StateTransition,
    BaseElement,
)
from ...models.base import BaseDocument


PNML_NS = "http://www.pnml.org/version-2009/grammar/pnml"


class PNMLXMLWriter(BaseOSDMWriter):
    """Serialises Petri nets (as unified StateMachineModel) to PNML XML."""

    name = "pnml_xml"
    supported_extensions = (".pnml",)

    def __init__(self, options: Optional[OSDMWriteOptions] = None):
        super().__init__(options)

    async def _write_design(self, document: BaseOSDMDocument) -> bytes:
        document = cast(base_document, StateMachineDocument)
        root = Element(f"{{{PNML_NS}}}pnml")
        root.set("xmlns", PNML_NS)

        if document:
            for sm in document.state_machines:
                if self._is_petri_net(sm):
                    self._write_net(root, sm)

        xml_bytes = tostring(root, encoding="unicode", method="xml")
        return xml_bytes.encode(self.options.encoding or "utf-8")

    def get_supported_media_types(self) -> list[str]:
        return ["application/xml"]

    def get_supported_extensions(self) -> list[str]:
        return list(self.supported_extensions)

    # ── Helpers ───────────────────────────────────────────────────
    def _is_petri_net(self, sm: StateMachineModel) -> bool:
        return self._get_annotation(sm, "model_type") == "petri_net"

    def _get_annotation(self, obj, key: str) -> Optional[str]:
        for ann in getattr(obj, 'annotations', []):
            if ann.key == key:
                return ann.value
        return None

    def _has_annotation(self, obj, key: str, value: Optional[str] = None) -> bool:
        val = self._get_annotation(obj, key)
        if value is not None:
            return val == value
        return val is not None

    # ── Net & Page ────────────────────────────────────────────────
    def _write_net(self, root: Element, sm: StateMachineModel) -> None:
        net = SubElement(root, f"{{{PNML_NS}}}net", {"id": sm.id, "type": PNML_NS})
        # The top region represents the default page
        self._write_page(net, sm.top_region, "page0", sm.name)

        # If the state machine has pseudo states? Not needed.
        # We don't explicitly handle tool-specific extensions yet; they can be added as annotation.

    def _write_page(self, parent: Element, region: StateMachineRegion, page_id: str, name: Optional[str] = None) -> None:
        page = SubElement(parent, f"{{{PNML_NS}}}page", {"id": page_id})
        if name:
            page.set("name", name)

        # Write places and transitions
        for state in region.states:
            if self._has_annotation(state, "petri_type", "place"):
                self._write_place(page, state)
            elif self._has_annotation(state, "petri_type", "transition"):
                self._write_transition(page, state)

        for ref in region.references:
            if isinstance(ref, Place):
                self._write_reference_place(page_elem, ref)
            elif isinstance(ref, PnTransition):
                self._write_reference_transition(page_elem, ref)
        
        # Write arcs
        for trans in region.transitions:
            if self._has_annotation(trans, "petri_type", "arc"):
                self._write_arc(page, trans)

        # Recurse into sub‑regions (sub‑pages)
        for state in region.states:
            for sub_region in state.regions:
                sub_page_id = f"{page_id}_{state.id}"
                self._write_page(parent, sub_region, sub_page_id, state.name)

    # ── Place ─────────────────────────────────────────────────────
    def _write_place(self, parent: Element, state: State) -> None:
        place = SubElement(parent, f"{{{PNML_NS}}}place", {"id": state.id})
        if state.name:
            name_elem = SubElement(place, f"{{{PNML_NS}}}name")
            text = SubElement(name_elem, f"{{{PNML_NS}}}text")
            text.text = state.name

        # Initial marking
        marking = self._get_annotation(state, "initial_marking")
        if marking:
            im = SubElement(place, f"{{{PNML_NS}}}initialMarking")
            text = SubElement(im, f"{{{PNML_NS}}}text")
            text.text = marking

        # Capacity (if > 0)
        capacity = self._get_annotation(state, "capacity")
        if capacity and capacity != "0":
            cap_elem = SubElement(place, f"{{{PNML_NS}}}capacity")
            text = SubElement(cap_elem, f"{{{PNML_NS}}}text")
            text.text = capacity

    # ── Transition ────────────────────────────────────────────────
    def _write_transition(self, parent: Element, state: State) -> None:
        trans = SubElement(parent, f"{{{PNML_NS}}}transition", {"id": state.id})
        if state.name:
            name_elem = SubElement(trans, f"{{{PNML_NS}}}name")
            text = SubElement(name_elem, f"{{{PNML_NS}}}text")
            text.text = state.name

        # Timing expression (coloured/timed Petri net)
        timing = self._get_annotation(state, "timing_expression")
        if timing:
            toolspecific = SubElement(trans, f"{{{PNML_NS}}}toolspecific", {"tool": "time", "version": "1.0"})
            text = SubElement(toolspecific, f"{{{PNML_NS}}}text")
            text.text = timing

    # ── Arc ──────────────────────────────────────────────────────
    def _write_arc(self, parent: Element, trans: StateTransition) -> None:
        source = trans.source.id if trans.source else None
        target = trans.target.id if trans.target else None
        if not source or not target:
            return
        arc = SubElement(parent, f"{{{PNML_NS}}}arc", {
            "id": trans.id,
            "source": source,
            "target": target,
        })

        # Weight
        weight = self._get_annotation(trans, "weight")
        if weight:
            insc = SubElement(arc, f"{{{PNML_NS}}}inscription")
            text = SubElement(insc, f"{{{PNML_NS}}}text")
            text.text = weight

        # Inhibitor / reset arc
        if self._get_annotation(trans, "inhibitor") == "true":
            arc.set("type", "inhibitor")
        elif self._get_annotation(trans, "reset") == "true":
            arc.set("type", "reset")
        else:
            arc.set("type", "normal")

    # ── Reference Place / Transition ──────────────────────────────
    def _write_reference_place(self, parent: Element, place: Place) -> None:
        SubElement(parent, f"{{{PNML_NS}}}referencePlace", {
            "id": place.id,
            "ref": place.id,   # ref points to the actual place ID
        })

    def _write_reference_transition(self, parent: Element, trans: PnTransition) -> None:
        SubElement(parent, f"{{{PNML_NS}}}referenceTransition", {
            "id": trans.id,
            "ref": trans.id,
        })        
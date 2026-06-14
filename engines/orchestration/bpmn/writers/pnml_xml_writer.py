# engines/document/writers/osdm_writers/pnml_xml_writer.py
"""
PNML XML Writer – serialises a Petri net (as StateMachineModel with
dedicated Place, PnTransition, Arc fields) to PNML 1.3 format.

Composite states (State with sub‑regions) are written as separate <page>
elements under the same net, with the page ID derived from the parent page
and the state ID.
"""
from __future__ import annotations

from typing import cast
from xml.etree.ElementTree import Element, SubElement, tostring

from ..models.bpmn_models import (
    Arc, BaseOSDMDocument, Place, PnTransition, StateMachineDocument,
    StateMachineModel, StateMachineRegion
)
from ...models.writers.base_osdm_writer import BaseOSDMWriter, OSDMWriteOptions

PNML_NS = "http://www.pnml.org/version-2009/grammar/pnml"


class PNMLXMLWriter(BaseOSDMWriter):
    name = "pnml_xml"
    supported_extensions = (".pnml",)

    def __init__(self, options: OSDMWriteOptions | None = None):
        super().__init__(options)

    async def _write_design(self, base_document: BaseOSDMDocument) -> bytes:
        document = cast(StateMachineDocument, base_document)
        root = Element(f"{{{PNML_NS}}}pnml")
        root.set("xmlns", PNML_NS)

        for sm in document.state_machines:
            self._write_net(root, sm)

        xml_bytes = tostring(root, encoding="unicode", method="xml")
        return xml_bytes.encode(getattr(self.options, "encoding", "utf-8") or "utf-8")

    def get_supported_media_types(self) -> list[str]:
        return ["application/xml"]

    def get_supported_extensions(self) -> list[str]:
        return list(self.supported_extensions)

    # ── Net ──────────────────────────────────────────────────────
    def _write_net(self, root: Element, sm: StateMachineModel) -> None:
        net = SubElement(root, f"{{{PNML_NS}}}net", {"id": sm.id, "type": PNML_NS})
        # Write the top‑level page
        self._write_page(net, sm.top_region, "page0", sm.name)

        # Recursively write all sub‑pages from composite states
        self._write_sub_pages(net, sm.top_region, "page0")

    # ── Page (flat representation) ───────────────────────────────
    def _write_page(self, parent: Element, region: StateMachineRegion,
                    page_id: str, name: str | None = None) -> None:
        page = SubElement(parent, f"{{{PNML_NS}}}page", {"id": page_id})
        if name:
            page.set("name", name)

        # Places
        for place in region.places:
            self._write_place(page, place)

        # Transitions
        for trans in region.pn_transitions:
            self._write_transition(page, trans)

        # Arcs
        for arc in region.arcs:
            self._write_arc(page, arc)

    # ── Recursively write sub‑pages for composite states ─────────
    def _write_sub_pages(self, net: Element, region: StateMachineRegion,
                         parent_page_id: str) -> None:
        for state in region.states:
            for idx, sub_region in enumerate(state.regions):
                sub_page_id = f"{parent_page_id}_{state.id}_{idx}"
                self._write_page(net, sub_region, sub_page_id, state.name)
                # Recurse deeper
                self._write_sub_pages(net, sub_region, sub_page_id)

    # ── Place ────────────────────────────────────────────────────
    def _write_place(self, parent: Element, place: Place) -> None:
        elem = SubElement(parent, f"{{{PNML_NS}}}place", {"id": place.id})
        if place.name:
            name_elem = SubElement(elem, f"{{{PNML_NS}}}name")
            text = SubElement(name_elem, f"{{{PNML_NS}}}text")
            text.text = place.name

        # Initial marking
        if place.initial_marking != 0:
            im = SubElement(elem, f"{{{PNML_NS}}}initialMarking")
            text = SubElement(im, f"{{{PNML_NS}}}text")
            text.text = str(place.initial_marking)

        # Capacity (if > 0)
        if place.capacity > 0:
            cap = SubElement(elem, f"{{{PNML_NS}}}capacity")
            text = SubElement(cap, f"{{{PNML_NS}}}text")
            text.text = str(place.capacity)

    # ── Transition ───────────────────────────────────────────────
    def _write_transition(self, parent: Element, trans: PnTransition) -> None:
        elem = SubElement(parent, f"{{{PNML_NS}}}transition", {"id": trans.id})
        if trans.name:
            name_elem = SubElement(elem, f"{{{PNML_NS}}}name")
            text = SubElement(name_elem, f"{{{PNML_NS}}}text")
            text.text = trans.name

        # Timing expression (if present)
        if trans.timing_expression and trans.timing_expression.body:
            toolspecific = SubElement(elem, f"{{{PNML_NS}}}toolspecific",
                                      {"tool": "time", "version": "1.0"})
            text = SubElement(toolspecific, f"{{{PNML_NS}}}text")
            text.text = trans.timing_expression.body

    # ── Arc ──────────────────────────────────────────────────────
    def _write_arc(self, parent: Element, arc: Arc) -> None:
        if not arc.arc_source or not arc.arc_target:
            return
        elem = SubElement(parent, f"{{{PNML_NS}}}arc", {
            "id": arc.id,
            "source": arc.arc_source.id,
            "target": arc.arc_target.id,
        })

        # Weight (if != 1)
        if arc.weight != 1:
            insc = SubElement(elem, f"{{{PNML_NS}}}inscription")
            text = SubElement(insc, f"{{{PNML_NS}}}text")
            text.text = str(arc.weight)

        # Type
        if arc.inhibitor:
            elem.set("type", "inhibitor")
        elif arc.reset:
            elem.set("type", "reset")
        else:
            elem.set("type", "normal")
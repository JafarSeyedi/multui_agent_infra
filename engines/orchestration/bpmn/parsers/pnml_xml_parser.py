# engines/document/parsers/osdm_parsers/pnml_xml_parser.py
"""
PNML Parser – converts a .pnml file into a StateMachineDocument using the
dedicated Petri‑net types (Place, PnTransition, Arc) present in OSDM.

Mapping:
- <place> → Place (added to region.places)
- <transition> → PnTransition (added to region.pn_transitions)
- <arc> → Arc (added to region.arcs)
- <referencePlace> / <referenceTransition> → not used (PNML generally does not need them)
- Nested pages → composite State with sub‑region
"""
from __future__ import annotations

import uuid
from xml.etree import ElementTree as ET

from engines.document.models.media_types import MEDIA_TYPES
from ..models.bpmn_models import FormalExpression
from ...models.shared_models import BaseOSDMDocument
from ...state_machine.models.state_machine_models import (
    Arc, Place, PnTransition, State,
    StateMachineDocument, StateMachineModel, StateMachineRegion
)
from engines.document.parsers.base import ParseOptions
from ...models.base_osdm_parser import BaseOSDMParser

PNML_NS = "http://www.pnml.org/version-2009/grammar/pnml"
NS = {"pnml": PNML_NS}


class PNMLXMLParser(BaseOSDMParser):
    """Parser for PNML files (.pnml)."""

    name = "pnml_xml"
    supported_extensions = (".pnml",)

    async def _parse_to_document(
        self, data: bytes, source_name: str, options: ParseOptions
    ) -> BaseOSDMDocument:
        encoding = options.encoding or "utf-8"
        text = data.decode(encoding)
        root = ET.fromstring(text)

        doc = StateMachineDocument(
            document_id=root.get("id", source_name),
            title=root.get("name", source_name),
            media_type=MEDIA_TYPES.get("pnml", MEDIA_TYPES["xml"])
        )
        doc.source_file = source_name

        for net_elem in root.findall("pnml:net", NS):
            sm = self._parse_net(net_elem)
            doc.state_machines.append(sm)

        return doc

    def _parse_net(self, net_elem: ET.Element) -> StateMachineModel:
        net_id = net_elem.get("id", "")
        net_name = net_elem.get("name", net_id)
        sm = StateMachineModel(id=net_id, name=net_name)

        page = net_elem.find("pnml:page", NS)
        if page is not None:
            sm.top_region = self._parse_page(page)
        else:
            sm.top_region = self._parse_page(net_elem)   # net acts as page
        return sm

    def _parse_page(self, page_elem: ET.Element) -> StateMachineRegion:
        region = StateMachineRegion(id=str(uuid.uuid4().hex), name="page")
        # Temporary maps for resolving arc sources/targets
        place_map: dict[str, Place] = {}
        trans_map: dict[str, PnTransition] = {}
        pending_arcs: list[ET.Element] = []

        for child in page_elem:
            tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
            if tag == "place":
                place = self._parse_place(child)
                region.places.append(place)
                place_map[place.id] = place
            elif tag == "transition":
                trans = self._parse_transition(child)
                region.pn_transitions.append(trans)
                trans_map[trans.id] = trans
            elif tag == "arc":
                pending_arcs.append(child)
            elif tag == "page":
                # nested page becomes a composite state
                sub_region = self._parse_page(child)
                dummy_state = State(id=child.get("id", str(uuid.uuid4().hex)), name=child.get("name", ""))
                dummy_state.regions.append(sub_region)
                dummy_state.is_composite = True
                region.states.append(dummy_state)
            # ignore referencePlace, referenceTransition – not needed for PNML

        # Resolve arcs after all places and transitions are known
        for arc_elem in pending_arcs:
            arc = self._parse_arc(arc_elem, place_map, trans_map)
            if arc:
                region.arcs.append(arc)

        return region

    # ── Place ─────────────────────────────────────────────────────
    def _parse_place(self, elem: ET.Element) -> Place:
        place_id = elem.get("id", "")
        place_name = elem.get("name", "")
        p = Place(id=place_id, name=place_name)
        # initial marking
        marking_text = self._child_text(elem, "pnml:initialMarking/pnml:text")
        if marking_text is not None:
            p.initial_marking = int(marking_text)
        # capacity
        cap_text = self._child_text(elem, "pnml:capacity/pnml:text")
        if cap_text is not None:
            p.capacity = int(cap_text)
        return p

    # ── Transition ────────────────────────────────────────────────
    def _parse_transition(self, elem: ET.Element) -> PnTransition:
        trans_id = elem.get("id", "")
        trans_name = elem.get("name", "")
        t = PnTransition(id=trans_id, name=trans_name)
        # timing from toolspecific
        ts = elem.find("pnml:toolspecific", NS)
        if ts is not None and ts.text:
            expr_id = str(uuid.uuid4().hex)
            t.timing_expression = FormalExpression(id=expr_id, body=ts.text)
        return t

    # ── Arc ──────────────────────────────────────────────────────
    def _parse_arc(self, elem: ET.Element,
                   place_map: dict[str, Place],
                   trans_map: dict[str, PnTransition]) -> Arc | None:
        src_id = elem.get("source")
        tgt_id = elem.get("target")
        if not src_id or not tgt_id:
            return None

        arc_source = place_map.get(src_id) or trans_map.get(src_id)
        arc_target = place_map.get(tgt_id) or trans_map.get(tgt_id)
        if not arc_source or not arc_target:
            return None

        arc_id = elem.get("id", f"{src_id}_{tgt_id}")
        arc = Arc(
            id=arc_id,
            arc_source=arc_source,
            arc_target=arc_target,
        )
        # weight (inscription)
        w = self._child_text(elem, "pnml:inscription/pnml:text")
        if w is not None:
            try:
                arc.weight = int(w)
            except ValueError:
                pass

        # type (normal, inhibitor, reset)
        at = elem.get("type", "normal")
        if at == "inhibitor":
            arc.inhibitor = True
        elif at == "reset":
            arc.reset = True
        return arc

    # ── Helpers ──────────────────────────────────────────────────
    @staticmethod
    def _child_text(elem: ET.Element, xpath: str) -> str | None:
        el = elem.find(xpath, NS)
        return el.text if el is not None and el.text else None
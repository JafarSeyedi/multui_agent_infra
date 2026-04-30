# engines/document/parsers/osdm_parsers/pnml_xml_parser.py
"""
PNML Parser – converts a .pnml file into a StateMachineDocument using the
dedicated Petri‑net types (Place, PnTransition, Arc) already present in OSDM.
Reference places/transitions are temporarily stored as State with annotations
until StateMachineRegion gets a dedicated 'references' list.
"""

from __future__ import annotations
from pathlib import Path
from typing import Optional, Dict, Any, List
from xml.etree import ElementTree as ET

from .base_osdm_parser import BaseOSDMParser
from ..base import ParseOptions
from ...models.osdm_models import (
    BaseOSDMDocument,
    StateMachineDocument,
    StateMachineModel,
    StateMachineRegion,
    State,
    StateTransition,
    Place,
    PnTransition,
    Arc,
    ReferencePlace,
    ReferenceTransition,
    FormalExpression,
)
from ...models.base import BaseDocument


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

        doc = StateMachineDocument()

        for net_elem in root.findall("pnml:net", NS):
            sm = self._parse_net(net_elem)
            doc.state_machines.append(sm)

        return doc

    def _parse_net(self, net_elem: ET.Element) -> StateMachineModel:
        net_id = net_elem.get("id", "")
        net_name = net_elem.get("name", net_id)
        sm = StateMachineModel(id=net_id, name=net_name)

        # The top‑level page
        page = net_elem.find("pnml:page", NS)
        if page is not None:
            sm.top_region = self._parse_page(page)
        else:
            sm.top_region = self._parse_page(net_elem)   # net acts as page
        return sm

    def _parse_page(self, page_elem: ET.Element) -> StateMachineRegion:
        region = StateMachineRegion()
        # Temporary map for resolving references
        node_map: Dict[str, State] = {}
        pending_refs: List[tuple] = []   # (elem, region, is_place_ref)

        for child in page_elem:
            tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
            if tag == "place":
                place = self._parse_place(child)
                region.states.append(place)
                node_map[place.id] = place
            elif tag == "transition":
                trans = self._parse_transition(child)
                region.states.append(trans)
                node_map[trans.id] = trans
            elif tag == "arc":
                arc = self._parse_arc(child, region.states)
                if arc:
                    region.transitions.append(arc)
            elif tag == "referencePlace":
                ref_id = child.get("ref", "")
                if ref_id in node_map:
                    region.references.append(node_map[ref_id])
                else:
                    pending_refs.append((child, region, True))
            elif tag == "referenceTransition":
                ref_id = child.get("ref", "")
                if ref_id in node_map:
                    region.references.append(node_map[ref_id])
                else:
                    pending_refs.append((child, region, False))
            elif tag == "page":
                sub = self._parse_page(child)
                dummy = State(id=child.get("id", ""), name=child.get("name", ""))
                dummy.regions.append(sub)
                dummy.is_composite = True
                region.states.append(dummy)

        # Second pass for unresolved references (elements defined later on the same page)
        for elem, reg, is_place in pending_refs:
            ref_id = elem.get("ref", "")
            obj = node_map.get(ref_id)
            if obj:
                reg.references.append(obj)
            else:
                # Could not resolve – skip or create a placeholder
                pass

        return region

    # ── Place ─────────────────────────────────────────────────────
    def _parse_place(self, elem: ET.Element) -> Place:
        p = Place(id=elem.get("id", ""), name=elem.get("name", ""))
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
        t = PnTransition(id=elem.get("id", ""), name=elem.get("name", ""))
        # timing from toolspecific
        ts = elem.find("pnml:toolspecific", NS)
        if ts is not None and ts.text:
            t.timing_expression = FormalExpression(body=ts.text)
        return t

    # ── Arc ──────────────────────────────────────────────────────
    def _parse_arc(self, elem: ET.Element, nodes: List[State]) -> Optional[Arc]:
        src_id = elem.get("source")
        tgt_id = elem.get("target")
        if not src_id or not tgt_id:
            return None
        src = self._find_node(nodes, src_id)
        tgt = self._find_node(nodes, tgt_id)
        if not src or not tgt:
            return None

        arc = Arc(
            id=elem.get("id", f"{src_id}_{tgt_id}"),
            source=src,
            target=tgt,
        )
        # weight (inscription)
        w = self._child_text(elem, "pnml:inscription/pnml:text")
        if w is not None:
            arc.weight = int(w)
        # type (normal, inhibitor, reset)
        at = elem.get("type", "normal")
        if at == "inhibitor":
            arc.inhibitor = True
        elif at == "reset":
            arc.reset = True
        return arc
    
    # ── Helpers ──────────────────────────────────────────────────
    @staticmethod
    def _child_text(elem: ET.Element, xpath: str) -> Optional[str]:
        el = elem.find(xpath, NS)
        return el.text if el is not None and el.text else None

    @staticmethod
    def _find_node(nodes: List[State], node_id: str) -> Optional[State]:
        for n in nodes:
            if n.id == node_id:
                return n
        return None


# Missing import for Annotation used only in reference elements
from ...models.osdm_models import Annotation
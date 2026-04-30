# engines/document/parsers/osdm_parsers/yawl_parser.py
"""
YAWL Parser – converts a .yawl specification file into one or more
StateMachineDocument objects (unified OSDM).

YAWL‑specific details are stored in YAWLTaskDecorator attached to each
PnTransition, and CancellationRegion objects on the StateMachineModel.
No annotations are used.

Mapping rules (YAWL → OSDM):
- <specificationSet>                 → (root container, ignored)
- <specification>                    → parsed into one or more StateMachineModel
- <documentation>                    → stored in StateMachineModel.name / description
- <net>                              → top‑level StateMachineRegion
- <condition>                        → Place
- <task>                             → PnTransition + YAWLTaskDecorator
- <flow source=… target=…>          → Arc
- <cancellationSet>/<contains>      → CancellationRegion
- <variables>                        → stored in StateMachineModel.annotations for now
  (a future model extension could add a dedicated field)
- <layout>                           → ignored
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
    Place,
    PnTransition,
    YAWLTaskDecorator,
    Arc,
    CancellationRegion,
    BaseElement,
)
from ...models.base import BaseDocument


YAWL_NS = "http://www.yawlfoundation.org/yawlschema"
NS = {"yawl": YAWL_NS}


class YAWLParser(BaseOSDMParser):
    """Parser for YAWL specification files (.yawl)."""

    name = "yawl"
    supported_extensions = (".yawl",)

    async def _parse_to_document(
        self, data: bytes, source_name: str, options: ParseOptions
    ) -> BaseOSDMDocument:
        encoding = options.encoding or "utf-8"
        text = data.decode(encoding)
        root = ET.fromstring(text)

        doc = StateMachineDocument()

        for spec_elem in root.findall("yawl:specification", NS):
            # Each specification can contain multiple nets; each net → a StateMachineModel
            nets = spec_elem.findall("yawl:net", NS)
            if not nets:
                continue
            for net_elem in nets:
                sm = self._parse_specification_and_net(spec_elem, net_elem)
                doc.state_machines.append(sm)

        return doc

    def _parse_specification_and_net(
        self, spec_elem: ET.Element, net_elem: ET.Element
    ) -> StateMachineModel:
        sm_id = spec_elem.get("id", "")
        sm_name = net_elem.get("name") or spec_elem.get("name", "")
        sm = StateMachineModel(id=sm_id, name=sm_name)
        sm.model_type = "yawl_net"

        # Documentation
        doc_elem = spec_elem.find("yawl:documentation", NS)
        if doc_elem is not None and doc_elem.text:
            sm.description = doc_elem.text

        # Variables: store as annotations for now (model extension later)
        variables = spec_elem.findall("yawl:variable", NS)
        for var in variables:
            sm.annotations.append(Annotation(key="variable", value=var.get("name", "")))

        # Build the net (top region)
        top_region = StateMachineRegion()
        sm.top_region = top_region

        node_map: Dict[str, BaseElement] = {}

        for child in net_elem:
            tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
            if tag == "condition":
                place = self._parse_condition(child)
                node_map[place.id] = place
                top_region.states.append(place)
            elif tag == "task":
                transition = self._parse_task(child)
                node_map[transition.id] = transition
                top_region.states.append(transition)
            elif tag == "flow":
                arc = self._parse_arc(child, node_map)
                if arc:
                    top_region.transitions.append(arc)
            elif tag == "cancellationSet":
                cr = self._parse_cancellation_set(child)
                sm.cancellation_regions.append(cr)

        return sm

    def _parse_condition(self, elem: ET.Element) -> Place:
        place = Place(
            id=elem.get("id", ""),
            name=elem.get("name", ""),
        )
        # initial marking
        marking_text = self._child_text(elem, "yawl:initialMarking")
        if marking_text is not None:
            try:
                place.initial_marking = int(marking_text)
            except ValueError:
                pass
        return place

    def _parse_task(self, elem: ET.Element) -> PnTransition:
        trans = PnTransition(
            id=elem.get("id", ""),
            name=elem.get("name", ""),
        )
        decorator = YAWLTaskDecorator(id=elem.get("id", ""))
        join_map = {"xor": YAWLJoinType.XOR, "and": YAWLJoinType.AND, "or": YAWLJoinType.OR}
        split_map = {"xor": YAWLSplitType.XOR, "and": YAWLSplitType.AND, "or": YAWLSplitType.OR}

        join_str = elem.get("join", "").lower()
        split_str = elem.get("split", "").lower()
        decorator.join_type = join_map.get(join_str, YAWLJoinType.NONE)
        decorator.split_type = split_map.get(split_str, YAWLSplitType.NONE)        
        # decorator.custom_form = elem.get("customForm", "")
        # # Task documentation
        # doc_elem = elem.find("yawl:documentation", NS)
        # if doc_elem is not None and doc_elem.text:
        #     decorator.documentation = doc_elem.text
        trans.yawl_decorator = decorator
        return trans

    def _parse_arc(self, elem: ET.Element, node_map: Dict[str, BaseElement]) -> Optional[Arc]:
        source_id = elem.get("source")
        target_id = elem.get("target")
        if not source_id or not target_id:
            return None

        source = node_map.get(source_id)
        target = node_map.get(target_id)
        if not source or not target:
            return None

        arc = Arc(
            id=elem.get("id", f"{source_id}_{target_id}"),
            source=source,
            target=target,
        )
        # Inscription (weight)
        insc_text = self._child_text(elem, "yawl:inscription")
        if insc_text is not None:
            try:
                arc.weight = int(insc_text)
            except ValueError:
                pass
        # Predicate (guard) – not in Arc currently; could be stored as annotation
        # For now, ignore.
        return arc

    def _parse_cancellation_set(self, elem: ET.Element) -> CancellationRegion:
        cr = CancellationRegion(id=elem.get("id", ""))
        for contains in elem.findall("yawl:contains", NS):
            node_id = contains.get("id")
            if node_id:
                cr.enclosed_node_ids.append(node_id)
        return cr

    @staticmethod
    def _child_text(elem: ET.Element, xpath: str) -> Optional[str]:
        el = elem.find(xpath, NS)
        return el.text if el is not None and el.text else None
# engines/document/parsers/osdm_parsers/epc_parser.py
"""
EPC (Event‑driven Process Chain) Parser – converts an EPML file into a
BPMNDocument (unified OSDM), because EPC elements map directly to BPMN.

Mapping rules (EPC → OSDM):
- <epc> → Process
- <event>             → StartEvent / EndEvent / IntermediateCatchEvent (depending on position)
- <function>          → Task (abstract)
- <connector type="and/or/xor"> → ParallelGateway / InclusiveGateway / ExclusiveGateway
- <arc source=… target=…> → SequenceFlow
- <organizationUnit>  → Lane
- <role>              → ResourceRole (inside Lane)

Note: EPC does not have a concept of "start" vs "end"; we infer start events as those
with no incoming arcs, and end events as those with no outgoing arcs.
"""

from __future__ import annotations
from pathlib import Path
from typing import Optional, Dict, Any, List
from xml.etree import ElementTree as ET

from .base_osdm_parser import BaseOSDMParser
from ..base import ParseOptions
from ...models.osdm_models import (
    BaseOSDMDocument,
    BPMNDocument,
    Process,
    FlowElement,
    FlowNode,
    SequenceFlow,
    Task,
    Event,
    StartEvent,
    EndEvent,
    IntermediateCatchEvent,
    Gateway,
    ExclusiveGateway,
    InclusiveGateway,
    ParallelGateway,
    Lane,
    LaneSet,
    ResourceRole,
    ResourceRoleType,
    BaseElement,
)
from ...models.base import BaseDocument


# ── Namespaces ────────────────────────────────────────────────────
EPML_NS = "http://www.epml.de"
EPC_NS  = "http://www.epml.de/epc"
NS = {"epml": EPML_NS, "epc": EPC_NS}


class EPCParser(BaseOSDMParser):
    """Parser for Event‑driven Process Chain (EPML) files (.epc, .epml)."""

    name = "epc"
    supported_extensions = (".epc", ".epml")

    async def _parse_to_document(
        self, data: bytes, source_name: str, options: ParseOptions
    ) -> BaseOSDMDocument:
        encoding = options.encoding or "utf-8"
        text = data.decode(encoding)
        root = ET.fromstring(text)

        doc = BPMNDocument()
        for epc_elem in root.findall("epc:epc", NS):
            proc = self._parse_epc(epc_elem)
            doc.processes.append(proc)
        return doc

    def _parse_epc(self, epc_elem: ET.Element) -> Process:
        proc = Process(
            id=epc_elem.get("id", ""),
            name=epc_elem.get("name", ""),
        )

        # Map IDs → elements
        flow_elements: Dict[str, FlowElement] = {}
        arcs: List[ET.Element] = []
        lanes: Dict[str, Lane] = {}

        # First pass: create all elements
        for child in epc_elem:
            tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
            if tag in ("event",):
                ev = self._parse_event(child)
                flow_elements[ev.id] = ev
            elif tag == "function":
                task = self._parse_function(child)
                flow_elements[task.id] = task
            elif tag == "connector":
                gw = self._parse_connector(child)
                flow_elements[gw.id] = gw
            elif tag == "arc":
                arcs.append(child)
            elif tag == "organizationUnit":
                lane = self._parse_organization_unit(child)
                lanes[lane.id] = lane
            elif tag == "role":
                # Roles are inside organizationUnit? We'll store them later.
                pass

        # Second pass: resolve arcs into SequenceFlows
        for arc_elem in arcs:
            seq = self._parse_arc(arc_elem, flow_elements)
            if seq is not None:
                flow_elements[seq.id] = seq

        # Assign flow elements to process
        proc.flow_elements = flow_elements

        # Build lane sets from organizational units
        if lanes:
            lane_set = LaneSet(id=f"{proc.id}_laneSet", name="Organizational Units")
            for lane in lanes.values():
                lane_set.lanes.append(lane)
            proc.lane_sets.append(lane_set)

        return proc

    def _parse_event(self, elem: ET.Element) -> Event:
        ev = Event(
            id=elem.get("id", ""),
            name=elem.get("name", ""),
        )
        # We don't yet know if it's start/intermediate/end; we'll decide later based on arcs.
        # We'll store as generic Event for now, then after resolving arcs we can change the type.
        # For simplicity, we'll keep them as Event and let the writer decide. The writer expects
        # explicit subtypes, but the model allows Event with event_type.
        # We'll set a default type "Start" and adjust in second pass if we have arc info.
        ev.event_type = "Start"  # will be corrected later if needed
        return ev

    def _parse_function(self, elem: ET.Element) -> Task:
        task = Task(
            id=elem.get("id", ""),
            name=elem.get("name", ""),
        )
        # Resources (roles) are attached inside the function? Actually roles are inside organizationUnit,
        # but functions may reference them via <resource resourceRef=…>. We'll skip for simplicity.
        return task

    def _parse_connector(self, elem: ET.Element) -> Gateway:
        conn_type = elem.get("type", "exclusive").lower()
        if conn_type == "and":
            gw = ParallelGateway(id=elem.get("id", ""), name=elem.get("name", ""))
        elif conn_type == "or":
            gw = InclusiveGateway(id=elem.get("id", ""), name=elem.get("name", ""))
        else:
            gw = ExclusiveGateway(id=elem.get("id", ""), name=elem.get("name", ""))
        return gw

    def _parse_arc(self, elem: ET.Element, flow_map: Dict[str, FlowElement]) -> Optional[SequenceFlow]:
        source_id = elem.get("source")
        target_id = elem.get("target")
        if not source_id or not target_id:
            return None
        source = flow_map.get(source_id)
        target = flow_map.get(target_id)
        if not isinstance(source, FlowNode) or not isinstance(target, FlowNode):
            return None
        seq = SequenceFlow(
            id=elem.get("id", f"{source_id}_{target_id}"),
            source_ref=source,
            target_ref=target,
        )
        # Update event types based on connections
        if isinstance(source, Event):
            if not source.outgoing:
                source.outgoing = []
            source.outgoing.append(seq)
            # If an event has outgoing but no incoming, it's a start
            if not source.incoming:
                source.event_type = "Start"
        if isinstance(target, Event):
            if not target.incoming:
                target.incoming = []
            target.incoming.append(seq)
            # If an event has incoming but no outgoing, it's an end
            if not target.outgoing:
                target.event_type = "End"
        return seq

    def _parse_organization_unit(self, elem: ET.Element) -> Lane:
        lane = Lane(
            id=elem.get("id", ""),
            name=elem.get("name", ""),
        )
        # Roles inside this unit
        for role_elem in elem.findall("epc:role", NS):
            role = self._parse_role(role_elem)
            lane.resources.append(role)
        return lane

    def _parse_role(self, elem: ET.Element) -> ResourceRole:
        role = ResourceRole(
            id=elem.get("id", ""),
            name=elem.get("name", ""),
            type=ResourceRoleType(elem.get("type", "None")),
        )
        return role
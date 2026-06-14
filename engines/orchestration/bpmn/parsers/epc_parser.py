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

from xml.etree import ElementTree as ET

from engines.document.models.media_types import MEDIA_TYPES
from ..models.bpmn_models import (
    BaseOSDMDocument, BPMNDocument, Event, EventType, ExclusiveGateway,
    FlowElement, FlowNode, Gateway, InclusiveGateway, Lane, LaneSet,
    ParallelGateway, Process, ResourceRole, ResourceRoleType, SequenceFlow, Task
)
from engines.document.parsers.base import ParseOptions
from ...models.parsers.base_osdm_parser import BaseOSDMParser

# Namespaces
EPML_NS = "http://www.epml.de"
EPC_NS = "http://www.epml.de/epc"
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

        doc = BPMNDocument(
            document_id=root.get("id", source_name),
            title=root.get("name", source_name),
            media_type=MEDIA_TYPES.get("epc_xml", MEDIA_TYPES["xml"])
        )
        doc.source_file = source_name

        for epc_elem in root.findall("epc:epc", NS):
            proc = self._parse_epc(epc_elem)
            doc.processes.append(proc)
        return doc

    def _parse_epc(self, epc_elem: ET.Element) -> Process:
        proc = Process(
            id=epc_elem.get("id", ""),
            name=epc_elem.get("name", ""),
        )

        flow_elements: dict[str, FlowElement] = {}
        arcs: list[ET.Element] = []
        lanes: dict[str, Lane] = {}

        # First pass: create all elements
        for child in epc_elem:
            tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
            if tag == "event":
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
                # Roles are inside organizationUnit; handled there.
                pass

        # Second pass: resolve arcs into SequenceFlows
        for arc_elem in arcs:
            seq = self._parse_arc(arc_elem, flow_elements)
            if seq is not None:
                flow_elements[seq.id] = seq

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
            event_type=EventType.START,  # will be corrected later based on arcs
        )
        return ev

    def _parse_function(self, elem: ET.Element) -> Task:
        task = Task(
            id=elem.get("id", ""),
            name=elem.get("name", ""),
        )
        return task

    def _parse_connector(self, elem: ET.Element) -> Gateway:
        conn_type = elem.get("type", "exclusive").lower()
        gw_id = elem.get("id", "")
        gw_name = elem.get("name", "")
        if conn_type == "and":
            return ParallelGateway(id=gw_id, name=gw_name)
        elif conn_type == "or":
            return InclusiveGateway(id=gw_id, name=gw_name)
        else:
            return ExclusiveGateway(id=gw_id, name=gw_name)

    def _parse_arc(self, elem: ET.Element, flow_map: dict[str, FlowElement]) -> SequenceFlow | None:
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
            # Ensure the containers exist (mypy workaround)
            if not hasattr(source, "outgoing"):
                source.outgoing = []
            source.outgoing.append(seq)
            # If source event has no incoming arcs, it's a start event
            if not source.incoming:
                source.event_type = EventType.START
            else:
                # If it has both incoming and outgoing, it's intermediate
                source.event_type = EventType.INTERMEDIATE_CATCH

        if isinstance(target, Event):
            if not hasattr(target, "incoming"):
                target.incoming = []
            target.incoming.append(seq)
            # If target event has no outgoing arcs, it's an end event
            if not target.outgoing:
                target.event_type = EventType.END
            else:
                # If it has both incoming and outgoing, it's intermediate
                target.event_type = EventType.INTERMEDIATE_CATCH

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
        role_type_str = elem.get("type", "None")
        try:
            role_type = ResourceRoleType(role_type_str)
        except ValueError:
            role_type = ResourceRoleType.NONE
        role = ResourceRole(
            id=elem.get("id", ""),
            name=elem.get("name", ""),
            type=role_type,
        )
        return role
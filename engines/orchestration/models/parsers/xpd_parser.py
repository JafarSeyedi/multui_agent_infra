# engines/document/parsers/osdm_parsers/xpd_parser.py
"""
XPDL 2.x Parser – converts a .xpdl file into a BPMNDocument (unified OSDM).

Mapping rules (XPDL → BPMN / OSDM):
- <Package>                              → BPMNDocument (document_id, title)
- <WorkflowProcesses>/<WorkflowProcess>  → Process
- <Activities>/<Activity> (Task, SubFlow, Route) → Task / CallActivity / Gateway
- <Activities>/<Event>                   → StartEvent / EndEvent / IntermediateCatchEvent
- <Transitions>/<Transition>             → SequenceFlow
- <Participants>/<Participant>           → Participant
- <Lanes>/<Lane>                         → Lane (via LaneSet)
- <DataFields>/<DataField>               → Property
- <DataObjects>/<DataObject>             → DataObject
- <Artifacts>/*                          → Artifact (Association etc.)
- <Associations>/<Association>           → Association (directional)
- <Loop>                                 → StandardLoopCharacteristics (if present)
- <RedefinableHeader>                    (ignored)
"""
from __future__ import annotations

import uuid
from typing import Any
from xml.etree import ElementTree as ET

from engines.document.models.media_types import MEDIA_TYPES
from engines.orchestration.models.osdm_models import (
    Artifact, Association, AssociationDirection, BaseOSDMDocument,
    BPMNDocument, CallActivity, Collaboration, DataObject, EndEvent,
    ExclusiveGateway, FlowElement, FlowNode, FormalExpression, Group,
    IntermediateCatchEvent, Lane, LaneSet, Participant, Process, ProcessType,
    Property, SequenceFlow, StartEvent, Task, TextAnnotation
)
from engines.document.parsers.base import ParseOptions
from .base_osdm_parser import BaseOSDMParser

XPDL_NS = "http://www.wfmc.org/2008/XPDL2.1"
NS = {"xpdl": XPDL_NS}


class XPDLParser(BaseOSDMParser):
    """Parser for XPDL 2.x files (.xpdl)."""

    name = "xpd"
    supported_extensions = (".xpdl",)

    async def _parse_to_document(
        self, data: bytes, source_name: str, options: ParseOptions
    ) -> BaseOSDMDocument:
        encoding = options.encoding or "utf-8"
        text = data.decode(encoding)
        root = ET.fromstring(text)

        doc = BPMNDocument(
            document_id=root.get("Id", source_name),
            title=root.get("Name", source_name),
            media_type=MEDIA_TYPES.get("xpd_xml", MEDIA_TYPES["xml"])
        )
        doc.source_file = source_name
        doc.source_format = MEDIA_TYPES.get("xpd_xml", MEDIA_TYPES["xml"]).format if "xpd_xml" in MEDIA_TYPES else None

        # Store all root elements for reference resolution
        all_elements: dict[str, Any] = {}

        # Parse Participants (will be used for Collaboration and Lane mapping)
        participants: dict[str, Participant] = {}
        participants_elem = root.find("xpdl:Participants", NS)
        if participants_elem is not None:
            for part_elem in participants_elem.findall("xpdl:Participant", NS):
                participant = self._parse_participant(part_elem)
                participants[participant.id] = participant

        # Build a Collaboration holding all participants
        if participants:
            collab = Collaboration(id="collaboration", name="Collaboration")
            collab.participants = list(participants.values())
            doc.collaborations.append(collab)

        # Parse WorkflowProcesses – first pass: create all elements
        processes: list[Process] = []
        processes_elem = root.find("xpdl:WorkflowProcesses", NS)
        if processes_elem is not None:
            for wp_elem in processes_elem.findall("xpdl:WorkflowProcess", NS):
                proc, proc_elements = self._parse_workflow_process_first_pass(wp_elem, participants)
                processes.append(proc)
                all_elements.update(proc_elements)
                # Also add process itself to all_elements
                all_elements[proc.id] = proc

        doc.processes = processes

        # Second pass: resolve cross-references (CalledElement, Associations)
        self._resolve_references(doc, all_elements)

        return doc

    def _parse_workflow_process_first_pass(
        self, wp_elem: ET.Element, participants: dict[str, Participant]
    ) -> tuple[Process, dict[str, FlowElement]]:
        proc = Process(
            id=wp_elem.get("Id", ""),
            name=wp_elem.get("Name", ""),
            process_type=self._map_process_type(wp_elem.get("ProcessType", "None")),
        )

        flow_elements: dict[str, FlowElement] = {}

        # Activities
        activities_elem = wp_elem.find("xpdl:Activities", NS)
        if activities_elem is not None:
            for act_elem in activities_elem:
                flow = self._parse_activity_first_pass(act_elem)
                if flow:
                    flow_elements[flow.id] = flow

        # Transitions (Sequence Flows) – may need source/target IDs, we postpone resolution
        transitions_elem = wp_elem.find("xpdl:Transitions", NS)
        if transitions_elem is not None:
            for trans_elem in transitions_elem.findall("xpdl:Transition", NS):
                seq = self._parse_transition_first_pass(trans_elem)
                if seq:
                    flow_elements[seq.id] = seq

        # Lanes
        lanes_elem = wp_elem.find("xpdl:Lanes", NS)
        if lanes_elem is not None:
            lane_set = LaneSet(id=f"{proc.id}_laneset", name="Lanes")
            for lane_elem in lanes_elem.findall("xpdl:Lane", NS):
                lane = self._parse_lane(lane_elem)
                lane_set.lanes.append(lane)
            proc.lane_sets.append(lane_set)

        # Data Fields (Properties)
        data_fields_elem = wp_elem.find("xpdl:DataFields", NS)
        if data_fields_elem is not None:
            for df_elem in data_fields_elem.findall("xpdl:DataField", NS):
                prop = self._parse_data_field(df_elem)
                proc.properties.append(prop)

        # Data Objects
        data_objects_elem = wp_elem.find("xpdl:DataObjects", NS)
        if data_objects_elem is not None:
            for do_elem in data_objects_elem.findall("xpdl:DataObject", NS):
                dobj = self._parse_data_object(do_elem)
                flow_elements[dobj.id] = dobj

        # Artifacts (Groups, TextAnnotations)
        artifacts_elem = wp_elem.find("xpdl:Artifacts", NS)
        if artifacts_elem is not None:
            for art_elem in artifacts_elem:
                artifact = self._parse_artifact_first_pass(art_elem)
                if artifact:
                    proc.artifacts.append(artifact)

        # Associations (may need source/target IDs, postpone)
        assoc_elem = wp_elem.find("xpdl:Associations", NS)
        if assoc_elem is not None:
            for a_elem in assoc_elem.findall("xpdl:Association", NS):
                assoc = self._parse_association_first_pass(a_elem)
                if assoc:
                    proc.artifacts.append(assoc)

        proc.flow_elements = flow_elements
        return proc, flow_elements

    def _parse_activity_first_pass(self, elem: ET.Element) -> FlowElement | None:
        tag = elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag
        act_id = elem.get("Id", "")
        act_name = elem.get("Name", "")

        if tag == "Activity":
            activity_type = elem.get("ActivityType", "Task")
            if activity_type == "Route":
                return ExclusiveGateway(id=act_id, name=act_name)
            elif activity_type == "SubFlow":
                sub_flow = CallActivity(id=act_id, name=act_name)
                # Store the called element ID for later resolution
                called_id = elem.get("CalledElement")
                if called_id:
                    # Use a temporary private attribute to store the ID for later resolution
                    setattr(sub_flow, "_called_element_id", called_id)
                return sub_flow
            else:
                task = Task(id=act_id, name=act_name)
                loop_elem = elem.find("xpdl:Loop", NS)
                if loop_elem is not None:
                    from engines.orchestration.models.osdm_models import StandardLoopCharacteristics
                    loop = StandardLoopCharacteristics(id=f"{act_id}_loop")
                    loop.test_before = loop_elem.get("LoopType", "Standard") == "Standard"
                    cond = loop_elem.find("xpdl:LoopCondition", NS)
                    if cond is not None:
                        loop.loop_condition = FormalExpression(
                            id=str(uuid.uuid4().hex),
                            body=cond.text or ""
                        )
                    task.loop_characteristics = loop
                return task
        elif tag == "Event":
            event_type = elem.get("EventType", "Start")
            if event_type == "Start":
                return StartEvent(id=act_id, name=act_name)
            elif event_type == "End":
                return EndEvent(id=act_id, name=act_name)
            elif event_type == "Intermediate":
                return IntermediateCatchEvent(id=act_id, name=act_name)
        return None

    def _parse_transition_first_pass(self, elem: ET.Element) -> SequenceFlow | None:
        trans_id = elem.get("Id", "")
        from_id = elem.get("From")
        to_id = elem.get("To")
        if not from_id or not to_id:
            return None

        seq = SequenceFlow(
            id=trans_id,
            name=elem.get("Name"),
            source_ref=None,
            target_ref=None,
        )
        # Store source/target IDs in temporary attributes
        seq.source_ref_id = from_id
        seq.target_ref_id = to_id

        cond_elem = elem.find("xpdl:Condition", NS)
        if cond_elem is not None:
            body = cond_elem.get("Expression", cond_elem.text or "")
            seq.condition_expression = FormalExpression(
                id=str(uuid.uuid4().hex),
                body=body
            )
        return seq

    def _parse_association_first_pass(self, elem: ET.Element) -> Association | None:
        assoc_id = elem.get("Id", "")
        source = elem.get("Source")
        target = elem.get("Target")
        direction = elem.get("Direction", "None")
        if not source or not target:
            return None
        assoc = Association(
            id=assoc_id,
            source_ref=None,
            target_ref=None,
            direction=self._map_association_direction(direction),
        )
        assoc.source_ref_id = source
        assoc.target_ref_id = target
        return assoc

    def _parse_artifact_first_pass(self, elem: ET.Element) -> Artifact | None:
        tag = elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag
        art_id = elem.get("Id", "")
        elem.get("Name", "")
        if tag == "Group":
            return Group(id=art_id)
        elif tag == "TextAnnotation":
            text_elem = elem.find("xpdl:Text", NS)
            text = text_elem.text if text_elem is not None and text_elem.text is not None else ""
            return TextAnnotation(id=art_id, text=text)
        return None

    def _parse_participant(self, elem: ET.Element) -> Participant:
        part = Participant(id=elem.get("Id", ""), name=elem.get("Name", ""))
        part.process_ref_id = elem.get("ProcessRef")  # store ID, resolve later
        return part

    def _parse_lane(self, elem: ET.Element) -> Lane:
        return Lane(id=elem.get("Id", ""), name=elem.get("Name", ""))

    def _parse_data_field(self, elem: ET.Element) -> Property:
        return Property(id=elem.get("Id", ""), name=elem.get("Name", ""))

    def _parse_data_object(self, elem: ET.Element) -> DataObject:
        return DataObject(
            id=elem.get("Id", ""),
            name=elem.get("Name", ""),
            is_collection=elem.get("IsCollection", "false") == "true",
        )

    def _resolve_references(self, doc: BPMNDocument, all_elements: dict[str, Any]) -> None:
        """Resolve all cross‑references (CalledElement, source/target, etc.)."""
        # First, collect all elements including processes
        all_by_id: dict[str, Any] = dict(all_elements)
        for proc in doc.processes:
            all_by_id[proc.id] = proc

        # Resolve CallActivity.called_element
        for proc in doc.processes:
            for flow in proc.flow_elements.values():
                if isinstance(flow, CallActivity):
                    called_id = getattr(flow, "_called_element_id", None)
                    if called_id and called_id in all_by_id:
                        flow.called_element = all_by_id[called_id]
                    elif called_id:
                        # Could be a GlobalTask or Process not yet in dictionary; fallback to None
                        flow.called_element = None

        # Resolve SequenceFlow source/target
        for proc in doc.processes:
            for flow in proc.flow_elements.values():
                if isinstance(flow, SequenceFlow):
                    if flow.source_ref_id and flow.source_ref_id in all_by_id:
                        src = all_by_id[flow.source_ref_id]
                        if isinstance(src, FlowNode):
                            flow.source_ref = src
                    if flow.target_ref_id and flow.target_ref_id in all_by_id:
                        tgt = all_by_id[flow.target_ref_id]
                        if isinstance(tgt, FlowNode):
                            flow.target_ref = tgt

        # Resolve Association source/target
        for proc in doc.processes:
            for art in proc.artifacts:
                if isinstance(art, Association):
                    if art.source_ref_id and art.source_ref_id in all_by_id:
                        art.source_ref = all_by_id[art.source_ref_id]
                    if art.target_ref_id and art.target_ref_id in all_by_id:
                        art.target_ref = all_by_id[art.target_ref_id]

        # Resolve Participant.process_ref
        for collab in doc.collaborations:
            for part in collab.participants:
                if part.process_ref_id and part.process_ref_id in all_by_id:
                    part.process_ref = all_by_id[part.process_ref_id]

    @staticmethod
    def _map_process_type(value: str) -> ProcessType:
        mapping = {"None": ProcessType.NONE, "Public": ProcessType.PUBLIC, "Private": ProcessType.PRIVATE}
        return mapping.get(value, ProcessType.NONE)

    @staticmethod
    def _map_association_direction(value: str) -> AssociationDirection:
        mapping = {"None": AssociationDirection.NONE,
                   "One": AssociationDirection.ONE,
                   "Both": AssociationDirection.BOTH}
        return mapping.get(value, AssociationDirection.NONE)
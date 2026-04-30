# engines/document/parsers/osdm_parsers/xpd_parser.py
"""
XPDL 2.x Parser – converts a .xpdl file into a BPMNDocument (unified OSDM).

Mapping rules (XPDL → BPMN / OSDM):
- <Package>                              → BPMNDocument (id, name)
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
from pathlib import Path
from typing import Optional, Dict, Any, List, Union
from xml.etree import ElementTree as ET

from .base_osdm_parser import BaseOSDMParser
from ..base import ParseOptions
from ...models.osdm_models import (
    BaseOSDMDocument,
    BPMNDocument,
    Process,
    Collaboration,
    Participant,
    FlowElement,
    FlowNode,
    SequenceFlow,
    Task,
    StartEvent,
    EndEvent,
    IntermediateCatchEvent,
    Lane,
    LaneSet,
    Property,
    DataObject,
    Artifact,
    Association,
    Group,
    TextAnnotation,
    CallActivity,
    Gateway,
    ExclusiveGateway,
    InclusiveGateway,
    ParallelGateway,
    FormalExpression,
    ScriptLanguage,
)
from ...models.base import BaseDocument

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

        doc = BPMNDocument()
        doc.id = root.get("Id", source_name)
        doc.name = root.get("Name", source_name)

        # Parse Participants (will be used for Collaboration and Lane mapping)
        participants: Dict[str, Participant] = {}
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

        # Parse WorkflowProcesses
        processes_elem = root.find("xpdl:WorkflowProcesses", NS)
        if processes_elem is not None:
            for wp_elem in processes_elem.findall("xpdl:WorkflowProcess", NS):
                proc = self._parse_workflow_process(wp_elem, participants)
                doc.processes.append(proc)

        return doc

    # ── WorkflowProcess → Process ────────────────────────────────
    def _parse_workflow_process(self, wp_elem: ET.Element,
                                participants: Dict[str, Participant]) -> Process:
        proc = Process(
            id=wp_elem.get("Id", ""),
            name=wp_elem.get("Name", ""),
            process_type=wp_elem.get("ProcessType", "None"),
        )

        # Activities
        activities_elem = wp_elem.find("xpdl:Activities", NS)
        if activities_elem is not None:
            for act_elem in activities_elem:
                flow = self._parse_activity(act_elem)
                if flow:
                    proc.flow_elements[flow.id] = flow

        # Transitions (Sequence Flows)
        transitions_elem = wp_elem.find("xpdl:Transitions", NS)
        if transitions_elem is not None:
            for trans_elem in transitions_elem.findall("xpdl:Transition", NS):
                seq = self._parse_transition(trans_elem, proc.flow_elements)
                if seq:
                    proc.flow_elements[seq.id] = seq

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
                proc.flow_elements[dobj.id] = dobj

        # Artifacts (Associations, Groups, Text Annotations)
        artifacts_elem = wp_elem.find("xpdl:Artifacts", NS)
        if artifacts_elem is not None:
            for art_elem in artifacts_elem:
                artifact = self._parse_artifact(art_elem)
                if artifact:
                    proc.artifacts.append(artifact)

        # Associations (often under Artifacts, but handle separately if present)
        assoc_elem = wp_elem.find("xpdl:Associations", NS)
        if assoc_elem is not None:
            for a_elem in assoc_elem.findall("xpdl:Association", NS):
                assoc = self._parse_association(a_elem)
                if assoc:
                    proc.artifacts.append(assoc)

        return proc

    # ── Activity → FlowElement ────────────────────────────────────
    def _parse_activity(self, elem: ET.Element) -> Optional[FlowElement]:
        tag = elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag
        act_id = elem.get("Id", "")
        act_name = elem.get("Name", "")

        if tag == "Activity":
            activity_type = elem.get("ActivityType", "Task")
            if activity_type == "Route":
                # Route becomes a Gateway (exclusive by default)
                gw = ExclusiveGateway(id=act_id, name=act_name)
                return gw
            elif activity_type == "SubFlow":
                sub_flow = CallActivity(id=act_id, name=act_name)
                sub_flow.called_element = elem.get("CalledElement")
                return sub_flow
            else:
                task = Task(id=act_id, name=act_name)
                # Handle Loop (StandardLoopCharacteristics)
                loop_elem = elem.find("xpdl:Loop", NS)
                if loop_elem is not None:
                    from ...models.osdm_models import StandardLoopCharacteristics, FormalExpression
                    loop = StandardLoopCharacteristics(id=f"{act_id}_loop")
                    loop.test_before = loop_elem.get("LoopType", "Standard") == "Standard"
                    cond = loop_elem.find("xpdl:LoopCondition", NS)
                    if cond is not None:
                        loop.loop_condition = FormalExpression(body=cond.text or "")
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

    # ── Transition → SequenceFlow ────────────────────────────────
    def _parse_transition(self, elem: ET.Element,
                          flow_map: Dict[str, FlowElement]) -> Optional[SequenceFlow]:
        trans_id = elem.get("Id", "")
        from_id = elem.get("From")
        to_id = elem.get("To")
        if not from_id or not to_id:
            return None

        source = flow_map.get(from_id)
        target = flow_map.get(to_id)
        if not isinstance(source, FlowNode) or not isinstance(target, FlowNode):
            return None

        seq = SequenceFlow(
            id=trans_id,
            name=elem.get("Name"),
            source_ref=source,
            target_ref=target,
        )

        # Condition
        cond_elem = elem.find("xpdl:Condition", NS)
        if cond_elem is not None:
            body = cond_elem.get("Expression", cond_elem.text or "")
            seq.condition_expression = FormalExpression(body=body)

        return seq

    # ── Lane → Lane ──────────────────────────────────────────────
    def _parse_lane(self, elem: ET.Element) -> Lane:
        lane = Lane(id=elem.get("Id", ""), name=elem.get("Name", ""))
        # Lane members: <Member> elements? XPDL may have; we'll skip.
        return lane

    # ── DataField → Property ─────────────────────────────────────
    def _parse_data_field(self, elem: ET.Element) -> Property:
        return Property(id=elem.get("Id", ""), name=elem.get("Name", ""))

    # ── DataObject → DataObject ──────────────────────────────────
    def _parse_data_object(self, elem: ET.Element) -> DataObject:
        dobj = DataObject(
            id=elem.get("Id", ""),
            name=elem.get("Name", ""),
            is_collection=elem.get("IsCollection", "false") == "true",
        )
        return dobj

    # ── Participant → Participant ────────────────────────────────
    def _parse_participant(self, elem: ET.Element) -> Participant:
        part = Participant(id=elem.get("Id", ""), name=elem.get("Name", ""))
        part.process_ref = elem.get("ProcessRef")
        return part

    # ── Artifact ──────────────────────────────────────────────────
    def _parse_artifact(self, elem: ET.Element) -> Optional[Artifact]:
        tag = elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag
        art_id = elem.get("Id", "")
        art_name = elem.get("Name", "")

        if tag == "Group":
            return Group(id=art_id)
        elif tag == "TextAnnotation":
            text_elem = elem.find("xpdl:Text", NS)
            text = text_elem.text if text_elem is not None else ""
            return TextAnnotation(id=art_id, text=text)
        return None

    # ── Association (Artifact) ───────────────────────────────────
    def _parse_association(self, elem: ET.Element) -> Optional[Association]:
        assoc_id = elem.get("Id", "")
        source = elem.get("Source")
        target = elem.get("Target")
        direction = elem.get("Direction", "None")
        return Association(
            id=assoc_id,
            source_ref=source,
            target_ref=target,
            direction=direction,
        )
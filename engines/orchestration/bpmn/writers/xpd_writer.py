# engines/document/writers/osdm_writers/xpd_writer.py
"""
XPDL 2.2 Writer – maps OSDM Process and Collaboration objects to XPDL XML.

Since XPDL is semantically equivalent to BPMN 2.0, this writer reuses the
same OSDM classes (Process, Activity, SequenceFlow, etc.) and produces a
valid XPDL Package containing WorkflowProcesses and Participants.
"""
from __future__ import annotations

from typing import cast
from xml.etree.ElementTree import Element
from xml.etree.ElementTree import SubElement
from xml.etree.ElementTree import tostring

from ..models.bpmn_models import BaseOSDMDocument
from ..models.bpmn_models import BPMNDocument
from ..models.bpmn_models import Event
from ..models.bpmn_models import FlowElement
from ..models.bpmn_models import Participant
from ..models.bpmn_models import Process
from ..models.bpmn_models import SequenceFlow
from ..models.bpmn_models import SubProcess
from ..models.bpmn_models import Task
from ...models.writers.base_osdm_writer import BaseOSDMWriter
from ...models.writers.base_osdm_writer import OSDMWriteOptions


XPDL_NS = "http://www.wfmc.org/2008/XPDL2.1"
XSI_NS = "http://www.w3.org/2001/XMLSchema-instance"


class XPDLWriter(BaseOSDMWriter):
    """Serialises an OSDM Process to XPDL 2.2 XML."""

    name = "xpd"
    supported_extensions = (".xpdl",)

    def __init__(self, options: OSDMWriteOptions | None = None):
        super().__init__(options)

    async def _write_design(self, base_document: BaseOSDMDocument) -> bytes:
        document=cast(BPMNDocument, base_document)
        if document:
            # XPDL typically contains one Package with multiple WorkflowProcesses and Participants
            root = Element(f"{{{XPDL_NS}}}Package", {
                "xmlns": XPDL_NS,
                "xmlns:xsi": XSI_NS,
                "Id": document.document_id or "osdm_package",
                "Name": document.title or "OSDM Package",
            })
            # Package header
            header = SubElement(root, f"{{{XPDL_NS}}}PackageHeader")
            SubElement(header, f"{{{XPDL_NS}}}XPDLVersion").text = "2.2"
            SubElement(header, f"{{{XPDL_NS}}}Vendor").text = "OSDM"
            SubElement(header, f"{{{XPDL_NS}}}Created").text = "2025-01-01"  # could use current date

            # Participants (from Collaborations)
            participants_elem = SubElement(root, f"{{{XPDL_NS}}}Participants")
            for collab in document.collaborations:
                for participant in collab.participants:
                    self._write_participant(participants_elem, participant)

            # WorkflowProcesses (from Processes)
            processes_elem = SubElement(root, f"{{{XPDL_NS}}}WorkflowProcesses")
            for process in document.processes:
                self._write_workflow_process(processes_elem, process)
        else:
            root = Element(f"{{{XPDL_NS}}}Package", {
                "xmlns": XPDL_NS,
                "xmlns:xsi": XSI_NS,
                "Id": "osdm_package",
                "Name": "OSDM Package",
            })

        xml_bytes = tostring(root, encoding="unicode", method="xml")
        return xml_bytes.encode(getattr(self.options, "encoding", "utf-8") or "utf-8")

    def get_supported_media_types(self) -> list[str]:
        return ["application/xml"]

    def get_supported_extensions(self) -> list[str]:
        return list(self.supported_extensions)

    # ── Participant ────────────────────────────────────────────────
    def _write_participant(self, parent: Element, participant: Participant) -> None:
        elem = SubElement(parent, f"{{{XPDL_NS}}}Participant", {
            "Id": participant.id,
            "Name": participant.name or participant.id,
        })
        if participant.process_ref:
            elem.set("ProcessRef", participant.process_ref.id)

    # ── WorkflowProcess ────────────────────────────────────────────
    def _write_workflow_process(self, parent: Element, process: Process) -> None:
        elem = SubElement(parent, f"{{{XPDL_NS}}}WorkflowProcess", {
            "Id": process.id,
            "Name": process.name or process.id,
            "ProcessType": process.process_type.value if process.process_type else "None",
        })

        # Activities
        activities_elem = SubElement(elem, f"{{{XPDL_NS}}}Activities")
        for flow in process.flow_elements.values():
            if isinstance(flow, (Task, SubProcess, Event)):
                self._write_activity(activities_elem, flow)

        # Transitions (Sequence Flows)
        transitions_elem = SubElement(elem, f"{{{XPDL_NS}}}Transitions")
        for flow in process.flow_elements.values():
            if isinstance(flow, SequenceFlow):
                self._write_transition(transitions_elem, flow)

        # Lanes (organisational units)
        if process.lane_sets:
            participants_elem = SubElement(elem, f"{{{XPDL_NS}}}Participants")
            for lane_set in process.lane_sets:
                for lane in lane_set.lanes:
                    # XPDL uses "Participant" for lanes? We'll map lane to a participant inside the process.
                    p = SubElement(participants_elem, f"{{{XPDL_NS}}}Participant", {
                        "Id": lane.id,
                        "Name": lane.name or lane.id,
                    })
                    # Members (flow nodes)
                    for flow_node in lane.flow_node_refs:
                        SubElement(p, f"{{{XPDL_NS}}}Member", {"Id": flow_node.id})

        # Data fields (Properties)
        if process.properties:
            data_fields = SubElement(elem, f"{{{XPDL_NS}}}DataFields")
            for prop in process.properties:
                _df = SubElement(data_fields, f"{{{XPDL_NS}}}DataField", {
                    "Id": prop.id,
                    "Name": prop.name or prop.id,
                    "DataType": "STRING",
                })

    # ── Activity ───────────────────────────────────────────────────
    def _write_activity(self, parent: Element, flow: FlowElement) -> None:
        tag = "Activity"
        if isinstance(flow, Event):
            # XPDL has Event types: StartEvent, EndEvent, IntermediateEvent
            if flow.event_type == "Start":
                tag = "StartEvent"
            elif flow.event_type == "End":
                tag = "EndEvent"
            else:
                tag = "IntermediateEvent"
        _activity = SubElement(parent, f"{{{XPDL_NS}}}{tag}", {
            "Id": flow.id,
            "Name": flow.name or flow.id,
        })
        # If it's a Task, we could add Implementation
        if isinstance(flow, Task):
            # Implementation details omitted
            pass

    # ── Transition ─────────────────────────────────────────────────
    def _write_transition(self, parent: Element, seq: SequenceFlow) -> None:
        if seq.source_ref and seq.target_ref:
            trans = SubElement(parent, f"{{{XPDL_NS}}}Transition", {
                "Id": seq.id,
                "From": seq.source_ref.id,
                "To": seq.target_ref.id,
            })
            if seq.name:
                trans.set("Name", seq.name)
            if seq.condition_expression and seq.condition_expression.body:
                cond = SubElement(trans, f"{{{XPDL_NS}}}Condition", {
                    "Type": "CONDITION",
                })
                cond.text = seq.condition_expression.body

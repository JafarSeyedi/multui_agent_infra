# engines/document/writers/osdm_writers/epc_writer.py
"""
EPC (Event‑driven Process Chain) Writer – maps an OSDM Process to EPML format.
BPMN tasks become EPC functions, events become EPC events, gateways become
connectors (AND/OR/XOR), and sequence flows become arcs.
"""
from __future__ import annotations

from typing import cast
from xml.etree.ElementTree import Element
from xml.etree.ElementTree import SubElement
from xml.etree.ElementTree import tostring

from ...models.osdm_models import BaseOSDMDocument
from ...models.osdm_models import BPMNDocument
from ...models.osdm_models import Event
from ...models.osdm_models import Gateway
from ...models.osdm_models import Process
from ...models.osdm_models import SequenceFlow
from ...models.osdm_models import Task
from .base_osdm_writer import BaseOSDMWriter
from .base_osdm_writer import OSDMWriteOptions


# ── Namespaces ────────────────────────────────────────────────────
EPML_NS = "http://www.epml.de"
EPC_NS  = "http://www.epml.de/epc"


class EPCWriter(BaseOSDMWriter):
    """Serialises an OSDM Process to EPML (EPC XML)."""

    name = "epc"
    supported_extensions = (".epc", ".epml")

    def __init__(self, options: OSDMWriteOptions | None = None):
        super().__init__(options)

    async def _write_design(self, base_document: BaseOSDMDocument) -> bytes:
        document = cast(BPMNDocument, base_document)
        root = Element(f"{{{EPML_NS}}}epml", {
            "xmlns:epml": EPML_NS,
            "xmlns:epc": EPC_NS,
        })
        if document:
            # Write each process as an EPC (if multiple, wrap in separate models? EPML can have multiple <epc>)
            for process in document.processes:
                self._write_process(root, process)

        xml_bytes = tostring(root, encoding="unicode", method="xml")
        return xml_bytes.encode(getattr(self.options, "encoding", "utf-8") or "utf-8")

    def get_supported_media_types(self) -> list[str]:
        return ["application/xml"]

    def get_supported_extensions(self) -> list[str]:
        return list(self.supported_extensions)

    # ── Process ────────────────────────────────────────────────────
    def _write_process(self, root: Element, process: Process):
        epc = SubElement(root, f"{{{EPC_NS}}}epc", {
            "id": process.id,
            "name": process.name or process.id,
        })

        # Write organisational units (lanes / participants) – simplified as roles
        self._write_organisational_units(epc, process)

        # Write all flow elements: events, functions (tasks), connectors (gateways)
        for flow in process.flow_elements.values():
            if isinstance(flow, Event):
                self._write_event(epc, flow)
            elif isinstance(flow, Task):
                self._write_function(epc, flow)
            elif isinstance(flow, Gateway):
                self._write_connector(epc, flow)
            elif isinstance(flow, SequenceFlow):
                self._write_arc(epc, flow)

    def _write_organisational_units(self, epc: Element, process: Process):
        """Write lanes as organisational units."""
        for lane_set in process.lane_sets:
            for lane in lane_set.lanes:
                # Each lane is an organisational unit
                ou = SubElement(epc, f"{{{EPC_NS}}}organizationUnit", {
                    "id": lane.id,
                    "name": lane.name or lane.id,
                })
                # Optionally write resources (roles) inside
                for role in lane.resources:
                    _role_elem = SubElement(ou, f"{{{EPC_NS}}}role", {
                        "id": role.id,
                        "name": role.name or role.id,
                        "type": role.type.value if role.type else "",
                    })

    def _write_event(self, epc: Element, event: Event):
        SubElement(epc, f"{{{EPC_NS}}}event", {
            "id": event.id,
            "name": event.name or event.id,
        })

    def _write_function(self, epc: Element, task: Task):
        func = SubElement(epc, f"{{{EPC_NS}}}function", {
            "id": task.id,
            "name": task.name or task.id,
        })
        # If task has resources, add an organisational unit reference
        for role in task.resources:
            if role.resource_ref:
                SubElement(func, f"{{{EPC_NS}}}resource", {
                    "resourceRef": role.resource_ref.id,
                })

    def _write_connector(self, epc: Element, gw: Gateway):
        conn_type = gw.gateway_type.value.lower() if gw.gateway_type else "exclusive"
        SubElement(epc, f"{{{EPC_NS}}}connector", {
            "id": gw.id,
            "name": gw.name or gw.id,
            "type": conn_type,
        })

    def _write_arc(self, epc: Element, seq: SequenceFlow):
        if seq.source_ref and seq.target_ref:
            SubElement(epc, f"{{{EPC_NS}}}arc", {
                "id": seq.id,
                "source": seq.source_ref.id,
                "target": seq.target_ref.id,
            })

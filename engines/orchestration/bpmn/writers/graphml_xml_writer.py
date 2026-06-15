# engines/document/writers/osdm_writers/graphml_xml_writer.py
"""
GraphML XML Writer – serialises a unified OSDM StateMachineModel to GraphML.
The unified model uses State for nodes and StateTransition for edges.
Node/edge types are stored in dedicated fields (node_type, edge_type).
Ports (Locator objects) are written as GraphML <port> elements.
"""
from __future__ import annotations

from typing import cast
from xml.etree.ElementTree import Element, SubElement, tostring

from ...models.shared_models import BaseElement, BaseOSDMDocument
from ...state_machine.models.state_machine_models import (
    State, StateMachineDocument, StateMachineModel,
    StateMachineRegion, StateTransition
)
from ...models.base_osdm_writer import BaseOSDMWriter, OSDMWriteOptions

GRAPHML_NS = "http://graphml.graphdrawing.org/xmlns"
XSI_NS = "http://www.w3.org/2001/XMLSchema-instance"
SCHEMA_LOCATION = "http://graphml.graphdrawing.org/xmlns http://graphml.graphdrawing.org/xmlns/1.0/graphml.xsd"


class GraphMLXMLWriter(BaseOSDMWriter):
    name = "graphml_xml"
    supported_extensions = (".graphml",)

    def __init__(self, options: OSDMWriteOptions | None = None):
        super().__init__(options)

    async def _write_design(self, base_document: BaseOSDMDocument) -> bytes:
        document = cast(StateMachineDocument, base_document)
        root = Element(f"{{{GRAPHML_NS}}}graphml", {
            "xmlns": GRAPHML_NS,
            "xmlns:xsi": XSI_NS,
            f"{{{XSI_NS}}}schemaLocation": SCHEMA_LOCATION,
        })
        self._define_attributes(root)

        if document:
            for sm in document.state_machines:
                self._write_graph(root, sm)

        xml_bytes = tostring(root, encoding="unicode", method="xml")
        return xml_bytes.encode(getattr(self.options, "encoding", "utf-8") or "utf-8")

    def get_supported_media_types(self) -> list[str]:
        return ["application/xml"]

    def get_supported_extensions(self) -> list[str]:
        return list(self.supported_extensions)

    # ── Attribute definitions ───────────────────────────────────
    def _define_attributes(self, root: Element) -> None:
        SubElement(root, f"{{{GRAPHML_NS}}}key", {
            "id": "node_type", "for": "node", "attr.name": "node_type", "attr.type": "string"
        })
        SubElement(root, f"{{{GRAPHML_NS}}}key", {
            "id": "edge_type", "for": "edge", "attr.name": "edge_type", "attr.type": "string"
        })
        for port_attr in ("x", "y"):
            SubElement(root, f"{{{GRAPHML_NS}}}key", {
                "id": port_attr, "for": "port", "attr.name": port_attr, "attr.type": "double"
            })

    # ── Write a single graph ─────────────────────────────────────
    def _write_graph(self, root: Element, sm: StateMachineModel) -> None:
        graph = SubElement(root, f"{{{GRAPHML_NS}}}graph", {
            "id": sm.id, "edgedefault": "directed"
        })
        if sm.name:
            graph.set("name", sm.name)

        all_states: list[State] = []
        self._collect_states(sm.top_region, all_states)
        all_transitions: list[StateTransition] = []
        self._collect_transitions(sm.top_region, all_transitions)

        for state in all_states:
            self._write_node(graph, state)
        for trans in all_transitions:
            self._write_edge(graph, trans)

    def _collect_states(self, region: StateMachineRegion, all_states: list[State]) -> None:
        for state in region.states:
            all_states.append(state)
            for sub_region in state.regions:
                self._collect_states(sub_region, all_states)

    def _collect_transitions(self, region: StateMachineRegion, all_transitions: list[StateTransition]) -> None:
        # region.transitions is already list[StateTransition]
        all_transitions.extend(region.transitions)
        for state in region.states:
            # state.outgoing_transitions is list[Transition] – filter only StateTransition
            for t in state.outgoing_transitions:
                if isinstance(t, StateTransition):
                    all_transitions.append(t)
            for sub_region in state.regions:
                self._collect_transitions(sub_region, all_transitions)

    # ── Write node ────────────────────────────────────────────────
    def _write_node(self, parent: Element, state: State) -> None:
        node = SubElement(parent, f"{{{GRAPHML_NS}}}node", {"id": state.id})
        if state.name:
            node.set("name", state.name)

        # Node type from dedicated field
        if state.node_type:
            SubElement(node, f"{{{GRAPHML_NS}}}data", {"key": "node_type"}).text = state.node_type

        # Locators (ports) – from the locators list
        for locator in state.locators:
            self._write_locator(node, locator)

        # Nested graphs could be written but skipped for simplicity

    def _write_locator(self, parent: Element, locator) -> None:
        port = SubElement(parent, f"{{{GRAPHML_NS}}}port", {"name": locator.name or "port"})
        SubElement(port, f"{{{GRAPHML_NS}}}data", {"key": "x"}).text = str(locator.x)
        SubElement(port, f"{{{GRAPHML_NS}}}data", {"key": "y"}).text = str(locator.y)

    # ── Write edge ────────────────────────────────────────────────
    def _write_edge(self, parent: Element, trans: StateTransition) -> None:
        if not trans.source or not trans.target:
            return
        edge = SubElement(parent, f"{{{GRAPHML_NS}}}edge", {
            "id": trans.id,
            "source": trans.source.id,
            "target": trans.target.id,
        })
        if trans.edge_type:
            SubElement(edge, f"{{{GRAPHML_NS}}}data", {"key": "edge_type"}).text = trans.edge_type

        for locator in trans.locators:
            self._write_locator(edge, locator)
# engines/document/writers/osdm_writers/graphml_xml_writer.py
"""
GraphML XML Writer – serialises a unified OSDM StateMachineModel to GraphML.
The unified model uses State for nodes and StateTransition for edges.
Node/edge types are preserved via annotations (e.g., "node_type", "edge_type").
Ports (Locators) are represented as nested elements on nodes/edges.
"""

from __future__ import annotations
from pathlib import Path
from typing import Optional, Dict, Any, List, cast
from xml.etree.ElementTree import Element, SubElement, tostring

from .base_osdm_writer import BaseOSDMWriter, OSDMWriteOptions
from ...models.osdm_models import (
    BaseOSDMDocument, StateMachineDocument,
    StateMachineModel,
    State,
    StateTransition,
    StateMachineRegion,
    BaseElement,
)
from ...models.base import BaseDocument


GRAPHML_NS = "http://graphml.graphdrawing.org/xmlns"
XSI_NS = "http://www.w3.org/2001/XMLSchema-instance"
SCHEMA_LOCATION = "http://graphml.graphdrawing.org/xmlns http://graphml.graphdrawing.org/xmlns/1.0/graphml.xsd"


class GraphMLXMLWriter(BaseOSDMWriter):
    """Serialises OSDM state machines to GraphML XML."""

    name = "graphml_xml"
    supported_extensions = (".graphml",)

    def __init__(self, options: Optional[OSDMWriteOptions] = None):
        super().__init__(options)

    async def _write_design(self, base_document: BaseOSDMDocument) -> bytes:
        document = cast(StateMachineDocument, base_document)
        root = Element(f"{{{GRAPHML_NS}}}graphml", {
            "xmlns": GRAPHML_NS,
            "xmlns:xsi": XSI_NS,
            f"{{{XSI_NS}}}schemaLocation": SCHEMA_LOCATION,
        })

        # Define attributes for node type, edge type, and port coordinates
        self._define_attributes(root)

        # Each state machine becomes a <graph> element
        if document:
            for sm in document.state_machines:
                self._write_graph(root, sm)

        xml_bytes = tostring(root, encoding="unicode", method="xml")
        return xml_bytes.encode(self.options.encoding or "utf-8")

    def get_supported_media_types(self) -> list[str]:
        return ["application/xml"]

    def get_supported_extensions(self) -> list[str]:
        return list(self.supported_extensions)

    # ── Attribute definitions ───────────────────────────────────
    def _define_attributes(self, root: Element) -> None:
        # Node type attribute
        key_node_type = SubElement(root, f"{{{GRAPHML_NS}}}key", {
            "id": "node_type",
            "for": "node",
            "attr.name": "node_type",
            "attr.type": "string",
        })
        # Edge type attribute
        key_edge_type = SubElement(root, f"{{{GRAPHML_NS}}}key", {
            "id": "edge_type",
            "for": "edge",
            "attr.name": "edge_type",
            "attr.type": "string",
        })
        # Locator attributes (for ports)
        for port_attr in ("x", "y"):
            SubElement(root, f"{{{GRAPHML_NS}}}key", {
                "id": port_attr,
                "for": "port",
                "attr.name": port_attr,
                "attr.type": "double",
            })

    # ── Write a single graph ─────────────────────────────────────
    def _write_graph(self, root: Element, sm: StateMachineModel) -> None:
        graph = SubElement(root, f"{{{GRAPHML_NS}}}graph", {
            "id": sm.id,
            "edgedefault": "directed",   # OSDM transitions are directed
        })
        if sm.name:
            graph.set("name", sm.name)

        # Collect all states recursively from the top region
        all_states: List[State] = []
        self._collect_states(sm.top_region, all_states)
        # Collect all transitions
        all_transitions: List[StateTransition] = []
        self._collect_transitions(sm.top_region, all_transitions)

        # Write nodes
        for state in all_states:
            self._write_node(graph, state)

        # Write edges
        for trans in all_transitions:
            self._write_edge(graph, trans)

    def _collect_states(self, region: StateMachineRegion, all_states: List[State]) -> None:
        for state in region.states:
            all_states.append(state)
            for sub_region in state.regions:
                self._collect_states(sub_region, all_states)

    def _collect_transitions(self, region: StateMachineRegion, all_transitions: List[StateTransition]) -> None:
        all_transitions.extend(region.transitions)
        for state in region.states:
            # Transitions owned by the state itself (outgoing)
            all_transitions.extend(state.outgoing_transitions)
            for sub_region in state.regions:
                self._collect_transitions(sub_region, all_transitions)

    # ── Write node ────────────────────────────────────────────────
    def _write_node(self, parent: Element, state: State) -> None:
        node = SubElement(parent, f"{{{GRAPHML_NS}}}node", {"id": state.id})
        if state.name:
            node.set("name", state.name)

        # Node type from annotation (saved by parser)
        node_type = self._get_annotation(state, "node_type")
        if node_type:
            SubElement(node, f"{{{GRAPHML_NS}}}data", {"key": "node_type"}).text = node_type

        # Locators (ports) – we don't have Locator objects in the unified model, but the parser could store them as annotations.
        # We'll output any locator annotation as a <port> element.
        self._write_locators(node, state)

        # Nested graphs: if a state is composite, we don't have a nested GraphML graph; we could output a nested <graph> but GraphML allows graphs inside nodes. We'll skip for simplicity.

    def _write_locators(self, parent: Element, obj: BaseElement) -> None:
        """If the object has locator annotations, write them as <port> elements."""
        for ann in getattr(obj, 'annotations', []):
            if ann.key == "locator":
                parts = ann.value.split(",")
                port = SubElement(parent, f"{{{GRAPHML_NS}}}port", {"name": ann.name or "port"})
                if len(parts) == 2:
                    SubElement(port, f"{{{GRAPHML_NS}}}data", {"key": "x"}).text = parts[0].strip()
                    SubElement(port, f"{{{GRAPHML_NS}}}data", {"key": "y"}).text = parts[1].strip()

    # ── Write edge ────────────────────────────────────────────────
    def _write_edge(self, parent: Element, trans: StateTransition) -> None:
        # Need source and target ids
        source = trans.source.id if trans.source else None
        target = trans.target.id if trans.target else None
        if not source or not target:
            return
        edge = SubElement(parent, f"{{{GRAPHML_NS}}}edge", {
            "id": trans.id,
            "source": source,
            "target": target,
        })
        # Edge type from annotation
        edge_type = self._get_annotation(trans, "edge_type")
        if edge_type:
            SubElement(edge, f"{{{GRAPHML_NS}}}data", {"key": "edge_type"}).text = edge_type

        # Locators on the edge
        self._write_locators(edge, trans)

    # ── Annotation helper ───────────────────────────────────────
    @staticmethod
    def _get_annotation(obj: BaseElement, key: str) -> Optional[str]:
        for ann in getattr(obj, 'annotations', []):
            if ann.key == key:
                return ann.value
        return None
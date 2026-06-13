# engines/document/parsers/osdm_parsers/graphml_xml_parser.py
"""
GraphML XML Parser – converts a .graphml file into a StateMachineDocument (unified OSDM).

Mapping rules:
- <graphml> → root container (ignored except for attribute definitions)
- <graph> → StateMachineModel (top‑level) or a nested region (composite state)
- <node> → State (node_type stored in dedicated field)
- <edge> → StateTransition (edge_type stored in dedicated field)
- <port> → Locator (attached to the parent node/edge)
- Nested <graph> inside a node → composite state with a sub‑region
"""
from __future__ import annotations

import uuid
from xml.etree import ElementTree as ET

from engines.document.models.media_types import MEDIA_TYPES
from engines.orchestration.models.osdm_models import (
    BaseOSDMDocument, Locator, State, StateMachineDocument,
    StateMachineModel, StateMachineRegion, StateTransition
)
from engines.document.parsers.base import ParseOptions
from .base_osdm_parser import BaseOSDMParser

GRAPHML_NS = "http://graphml.graphdrawing.org/xmlns"
NS = {"g": GRAPHML_NS}


class GraphMLXMLParser(BaseOSDMParser):
    """Parser for GraphML files (.graphml)."""

    name = "graphml_xml"
    supported_extensions = (".graphml",)

    async def _parse_to_document(
        self, data: bytes, source_name: str, options: ParseOptions
    ) -> BaseOSDMDocument:
        encoding = options.encoding or "utf-8"
        text = data.decode(encoding)
        root = ET.fromstring(text)

        doc = StateMachineDocument(
            document_id=root.get("id", source_name),
            title=root.get("name", source_name),
            media_type=MEDIA_TYPES.get("graphml", MEDIA_TYPES["xml"])
        )
        doc.source_file = source_name

        # Process top‑level <graph> elements
        for graph_elem in root.findall("g:graph", NS):
            sm = self._parse_graph(graph_elem)
            doc.state_machines.append(sm)

        return doc

    def _parse_graph(self, graph_elem: ET.Element) -> StateMachineModel:
        graph_id = graph_elem.get("id", "")
        graph_name = graph_elem.get("name", graph_id)
        sm = StateMachineModel(id=graph_id, name=graph_name)
        top_region = StateMachineRegion(id=str(uuid.uuid4().hex), name="top_region")
        sm.top_region = top_region

        # Temporary map of node id → State
        node_map: dict[str, State] = {}
        edges: list[ET.Element] = []

        # Process children: nodes, edges, nested graphs
        for child in graph_elem:
            tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
            if tag == "node":
                state = self._parse_node(child)
                node_map[state.id] = state
                top_region.states.append(state)
            elif tag == "edge":
                edges.append(child)

        # Now resolve edges after all nodes are known
        for edge_elem in edges:
            trans = self._parse_edge(edge_elem, node_map)
            if trans:
                top_region.transitions.append(trans)

        return sm

    def _parse_node(self, elem: ET.Element) -> State:
        node_id = elem.get("id", "")
        node_name = elem.get("name", node_id)
        state = State(id=node_id, name=node_name)

        # Extract node_type from <data key="node_type">
        for data_elem in elem.findall("g:data", NS):
            key = data_elem.get("key", "")
            if key == "node_type":
                state.node_type = data_elem.text

        # Parse <port> elements → Locator objects
        for port_elem in elem.findall("g:port", NS):
            locator = self._parse_port(port_elem)
            state.locators.append(locator)

        # Check for nested <graph> (composite state)
        nested_graph = elem.find("g:graph", NS)
        if nested_graph is not None:
            sub_sm = self._parse_graph(nested_graph)
            # The sub‑state machine becomes a sub‑region
            sub_region = StateMachineRegion(
                id=str(uuid.uuid4().hex),
                states=sub_sm.top_region.states,
                transitions=sub_sm.top_region.transitions,
                initial_state=sub_sm.top_region.initial_state,
            )
            state.regions.append(sub_region)
            state.is_composite = True

        return state

    def _parse_edge(self, elem: ET.Element, node_map: dict[str, State]) -> StateTransition | None:
        source_id = elem.get("source")
        target_id = elem.get("target")
        if not source_id or not target_id:
            return None
        source = node_map.get(source_id)
        target = node_map.get(target_id)
        if not source or not target:
            return None

        trans = StateTransition(
            id=elem.get("id", str(uuid.uuid4().hex)),
            source=source,
            target=target,
            directed=elem.get("directed", "true").lower() == "true",
        )

        # Extract edge_type from <data key="edge_type">
        for data_elem in elem.findall("g:data", NS):
            key = data_elem.get("key", "")
            if key == "edge_type":
                trans.edge_type = data_elem.text

        # Parse <port> elements → Locator objects
        for port_elem in elem.findall("g:port", NS):
            locator = self._parse_port(port_elem)
            trans.locators.append(locator)

        return trans

    def _parse_port(self, elem: ET.Element) -> Locator:
        port_id = elem.get("id", str(uuid.uuid4().hex))
        port_name = elem.get("name", "")
        locator = Locator(id=port_id, name=port_name)
        # Coordinates stored as data elements
        for data_elem in elem.findall("g:data", NS):
            key = data_elem.get("key", "")
            if key == "x":
                locator.x = float(data_elem.text or 0)
            elif key == "y":
                locator.y = float(data_elem.text or 0)
        return locator
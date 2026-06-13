"""Mixin for BPMN Diagram/DI parsers — BPMNDiagram, BPMNShape, BPMNEdge, BPMNLabel."""

from __future__ import annotations

from xml.etree import ElementTree as ET

from engines.orchestration.models.osdm_models import (
    AlignmentKind, BPMNDiagram, BPMNEdge, BPMNLabel, BPMNShape, Bounds,
)
from .bpmn_constants import NS


class BPMNDiagramParser:
    """Mixin providing BPMN diagram layout parsing methods."""

    def _parse_diagram(self, elem: ET.Element) -> BPMNDiagram:
        diagram = BPMNDiagram(
            id=elem.get("id", ""),
            name=elem.get("name"),
            model_element=None,
        )
        diagram.model_element_id = elem.get("bpmnElement")
        plane = elem.find("bpmndi:BPMNPlane", NS)
        if plane is not None:
            for shape in plane.findall("bpmndi:BPMNShape", NS):
                diagram.owned_elements.append(self._parse_bpmn_shape(shape))
            for edge in plane.findall("bpmndi:BPMNEdge", NS):
                diagram.owned_elements.append(self._parse_bpmn_edge(edge))
        return diagram

    def _parse_bpmn_shape(self, elem: ET.Element) -> BPMNShape:
        shape = BPMNShape(
            id=elem.get("id", ""),
            model_element=None,
            is_horizontal=elem.get("isHorizontal", "true") == "true",
            is_expanded=elem.get("isExpanded", "false") == "true",
            is_marker_visible=elem.get("isMarkerVisible", "false") == "true",
            is_message_visible=elem.get("isMessageVisible", "false") == "true",
        )
        shape.model_element_id = elem.get("bpmnElement")
        bounds = elem.find("dc:Bounds", NS)
        if bounds is not None:
            shape.bounds = Bounds(
                x=float(bounds.get("x", 0)),
                y=float(bounds.get("y", 0)),
                width=float(bounds.get("width", 0)),
                height=float(bounds.get("height", 0)),
            )
        label = elem.find("bpmndi:BPMNLabel", NS)
        if label is not None:
            shape.label = self._parse_bpmn_label(label)
        return shape

    def _parse_bpmn_edge(self, elem: ET.Element) -> BPMNEdge:
        edge = BPMNEdge(
            id=elem.get("id", ""),
            model_element=None,
        )
        edge.model_element_id = elem.get("bpmnElement")
        label = elem.find("bpmndi:BPMNLabel", NS)
        if label is not None:
            edge.label = self._parse_bpmn_label(label)
        return edge

    def _parse_bpmn_label(self, elem: ET.Element) -> BPMNLabel:
        text = elem.get("labelStyle", "")
        bounds = elem.find("dc:Bounds", NS)
        return BPMNLabel(
            text=text,
            bounds=Bounds(
                x=float(bounds.get("x", 0)) if bounds is not None else 0,
                y=float(bounds.get("y", 0)) if bounds is not None else 0,
                width=float(bounds.get("width", 0)) if bounds is not None else 0,
                height=float(bounds.get("height", 0)) if bounds is not None else 0,
            ),
            alignment=AlignmentKind.LEFT,
        )

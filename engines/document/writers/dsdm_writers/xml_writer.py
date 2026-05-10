# engines/document/writers/dsdm_writers/xml_writer.py
"""XML writer that converts any DSDM tree into well‑formed XML."""
from __future__ import annotations

from typing import Any
from xml.etree.ElementTree import Element, SubElement, tostring

from ...models.dsdm_models import DataNode, DataNodeKind
from .base_dsdm_writer import BaseDSDMWriter, DSDMWriteOptions


class XMLWriter(BaseDSDMWriter):
    name = "xml"
    supported_extensions = (".xml",)
    media_type_str = "application/xml"  # for get_supported_media_types (implemented below)

    def get_supported_media_types(self) -> list[str]:
        return [self.media_type_str]

    def get_supported_extensions(self) -> list[str]:
        return list(self.supported_extensions)

    async def _serialise_root(self, root_node: DataNode, options: DSDMWriteOptions) -> bytes:
        self._check_required_fields(root_node, options)
        elem = self._node_to_xml(root_node, options, tag="document")
        return tostring(elem, encoding=options.encoding)

    async def _serialise_node(self, node: DataNode, options: DSDMWriteOptions) -> bytes:
        elem = self._node_to_xml(node, options)
        return tostring(elem, encoding=options.encoding)

    def _node_to_xml(self, node: DataNode, options: DSDMWriteOptions, tag: str | None = None) -> Element:
        if node.kind == DataNodeKind.XML_ELEMENT:
            return self._native_xml_element(node, options)
        elif node.kind == DataNodeKind.XML_ATTRIBUTE:
            raise ValueError("XML_ATTRIBUTE node cannot be serialised as a standalone element")
        elif node.kind == DataNodeKind.XML_TEXT:
            el = Element(tag or "text")
            el.text = str(node.value.value) if node.value else ""
            return el
        elif node.kind == DataNodeKind.OBJECT:
            el = Element(tag or node.name or "object")
            self._add_object_children(el, node, options)
            return el
        elif node.kind == DataNodeKind.ARRAY:
            el = Element(tag or node.name or "array")
            self._add_array_children(el, node, options)
            return el
        elif node.kind == DataNodeKind.SCALAR:
            el = Element(tag or node.name or "value")
            if node.value is not None:
                el.text = self._scalar_to_str(node.value)
            return el
        else:
            # COMMENT, PI, etc. – treat as comment element
            el = Element(tag or "comment")
            el.text = str(node.value.value) if node.value else ""
            return el

    def _native_xml_element(self, node: DataNode, options: DSDMWriteOptions) -> Element:
        tag = node.name or "element"
        if node.namespace:
            tag = f"{{{node.namespace}}}{tag}"
        elem = Element(tag)

        # Attributes
        for attr_node in node.attributes:
            attr_name = attr_node.name
            if attr_name is None:
                continue
            if attr_node.namespace:
                attr_name = f"{{{attr_node.namespace}}}{attr_name}"
            elem.set(attr_name, str(attr_node.value.value) if attr_node.value else "")

        # Text content
        if node.value is not None:
            elem.text = str(node.value.value)
        else:
            text_child = next((c for c in node.children if c.kind == DataNodeKind.XML_TEXT), None)
            if text_child:
                elem.text = str(text_child.value.value) if text_child.value else ""

        # Child ordering via schema
        ordering = self._get_attribute_order(node, options)
        if ordering:
            ordered_groups: dict[str, list[DataNode]] = {name: [] for name in ordering}
            for child in node.children:
                if child.kind != DataNodeKind.XML_TEXT:
                    name = child.name or ""
                    if name in ordered_groups:
                        ordered_groups[name].append(child)
            for name in ordering:
                for child in ordered_groups[name]:
                    if self._should_include_field(name, node, options):
                        sub_elem = self._node_to_xml(child, options)
                        elem.append(sub_elem)
        else:
            for child in node.children:
                if child.kind != DataNodeKind.XML_TEXT and self._should_include_field(child.name or "", node, options):
                    sub_elem = self._node_to_xml(child, options)
                    elem.append(sub_elem)
        return elem

    def _add_object_children(self, parent: Element, node: DataNode, options: DSDMWriteOptions):
        ordering = self._get_attribute_order(node, options)
        if ordering:
            child_map: dict[str, list[DataNode]] = {}
            for child in node.children:
                name = child.name or ""
                child_map.setdefault(name, []).append(child)
            for name in ordering:
                for child in child_map.get(name, []):
                    if self._should_include_field(name, node, options):
                        sub_elem = self._node_to_xml(child, options, tag=name)
                        parent.append(sub_elem)
        else:
            for child in node.children:
                name = child.name or "field"
                if self._should_include_field(name, node, options):
                    sub_elem = self._node_to_xml(child, options, tag=name)
                    parent.append(sub_elem)

    def _add_array_children(self, parent: Element, node: DataNode, options: DSDMWriteOptions):
        for child in node.children:
            sub_elem = self._node_to_xml(child, options, tag="item")
            parent.append(sub_elem)

    def _scalar_to_str(self, dv) -> str:
        if dv is None:
            return ""
        if isinstance(dv.value, bytes):
            import base64
            return base64.b64encode(dv.value).decode()
        return str(dv.value)
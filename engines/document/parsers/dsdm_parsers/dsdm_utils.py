# engines/document/parsers/dsdm_parsers/dsdm_utils.py
"""
Conversion helpers between Python native structures and DSDM DataNode trees.
"""

from __future__ import annotations

import base64
from typing import Any

from ...models.dsdm_models import (
    DataNode,
    DataNodeKind,
    DataValue,
    ScalarType,
)


def scalar_value(value: Any) -> DataValue:
    if value is None:
        return DataValue(scalar_type=ScalarType.NULL, value=None, lexical_value="null")
    if isinstance(value, bool):
        return DataValue(scalar_type=ScalarType.BOOLEAN, value=value, lexical_value=str(value).lower())
    if isinstance(value, int) and not isinstance(value, bool):
        return DataValue(scalar_type=ScalarType.INT, value=value, lexical_value=str(value))
    if isinstance(value, float):
        return DataValue(scalar_type=ScalarType.FLOAT, value=value, lexical_value=repr(value))
    if isinstance(value, (bytes, bytearray)):
        b = bytes(value)
        b64 = base64.b64encode(b).decode('ascii')
        return DataValue(scalar_type=ScalarType.BINARY, value=b, lexical_value=b64)
    return DataValue(scalar_type=ScalarType.STRING, value=str(value), lexical_value=str(value))


def build_node_from_python(
    value: Any,
    path: str = "$",
    name: str | None = None,
    node_id_prefix: str = "node",
    parent_kind: DataNodeKind | None = None,
) -> DataNode:
    node_id = f"{node_id_prefix}:{path}"

    if isinstance(value, dict):
        xml_keys = {"@attributes", "#text", "@xmlns", "@special"}
        is_xml_element = any(key in value for key in xml_keys) or parent_kind == DataNodeKind.XML_ELEMENT

        if is_xml_element:
            return _build_xml_element_from_dict(value, path, name, node_id, node_id_prefix)
        else:
            node = DataNode(node_id=node_id, kind=DataNodeKind.OBJECT, path=path, name=name)
            for key, child_value in value.items():
                child_path = f"{path}.{key}" if path != "$" else f"$.{key}"
                node.children.append(
                    build_node_from_python(
                        child_value,
                        path=child_path,
                        name=str(key),
                        node_id_prefix=node_id_prefix,
                        parent_kind=DataNodeKind.OBJECT,
                    )
                )
            return node

    if isinstance(value, list):
        node = DataNode(node_id=node_id, kind=DataNodeKind.ARRAY, path=path, name=name)
        for index, child_value in enumerate(value):
            child_path = f"{path}[{index}]"
            node.children.append(
                build_node_from_python(
                    child_value,
                    path=child_path,
                    name=str(index),
                    node_id_prefix=node_id_prefix,
                    parent_kind=DataNodeKind.ARRAY,
                )
            )
        return node

    return DataNode(
        node_id=node_id,
        kind=DataNodeKind.SCALAR,
        path=path,
        name=name,
        value=scalar_value(value),
    )


def node_to_python(node: DataNode) -> Any:
    if node.kind == DataNodeKind.XML_ELEMENT:
        return _xml_element_to_dict(node)

    if node.kind == DataNodeKind.XML_TEXT:
        return node.value.value if node.value else ""

    if node.kind == DataNodeKind.XML_ATTRIBUTE:
        return node.value.value if node.value else ""

    if node.kind in {
        DataNodeKind.XML_PROCESSING_INSTRUCTION,
        DataNodeKind.XML_DOCTYPE,
        DataNodeKind.XML_COMMENT,
        DataNodeKind.XML_CDATA,
    }:
        return {
            "@type": node.kind.value,
            "@content": node.value.value if node.value else "",
        }

    if node.kind == DataNodeKind.OBJECT:
        result: dict[str, Any] = {}
        for child in node.children:
            child_value = node_to_python(child)
            if child.name is not None:
                if child.name in result:
                    if not isinstance(result[child.name], list):
                        result[child.name] = [result[child.name]]
                    result[child.name].append(child_value)
                else:
                    result[child.name] = child_value
        return result

    if node.kind == DataNodeKind.ARRAY:
        return [node_to_python(child) for child in node.children]

    if node.value is None:
        return None

    if node.value.scalar_type == ScalarType.DATETIME:
        if isinstance(node.value.value, str):
            from datetime import datetime
            try:
                return datetime.fromisoformat(node.value.value.replace("Z", "+00:00"))
            except (ValueError, AttributeError):
                return node.value.value
    elif node.value.scalar_type == ScalarType.TIMESTAMP:
        if isinstance(node.value.value, (int, float)):
            from datetime import datetime
            return datetime.fromtimestamp(node.value.value)

    return node.value.value


def xml_to_python_dict(root_node: DataNode) -> dict[str, Any]:
    if root_node.kind == DataNodeKind.XML_ELEMENT:
        result = _xml_element_to_dict(root_node)
        doc_meta = {k: v for k, v in root_node.metadata.items() if not k.startswith("_")}
        if doc_meta:
            if not result:
                result = {}
            result["@document"] = doc_meta
        return {root_node.name or "root": result}

    if root_node.kind == DataNodeKind.OBJECT:
        result = {}
        for child in root_node.children:
            if child.kind == DataNodeKind.XML_ELEMENT:
                child_result = _xml_element_to_dict(child)
                result[child.name or f"element_{len(result)}"] = child_result
        return result

    return {}


# ---------------------------------------------------------------------------
# Internal XML conversion helpers
# ---------------------------------------------------------------------------

def _build_xml_element_from_dict(
    value: dict,
    path: str,
    name: str | None,
    node_id: str,
    node_id_prefix: str,
) -> DataNode:
    attributes = value.get("@attributes", {})
    text_content = value.get("#text", "")
    xmlns = value.get("@xmlns")
    special_nodes = value.get("@special", [])

    node = DataNode(
        node_id=node_id,
        kind=DataNodeKind.XML_ELEMENT,
        path=path,
        name=name,
    )

    if xmlns:
        node.metadata["xmlns"] = xmlns

    for attr_name, attr_value in attributes.items():
        attr_path = f"{path}@{attr_name}"
        attr_node = DataNode(
            node_id=f"{node_id_prefix}:{attr_path}",
            kind=DataNodeKind.XML_ATTRIBUTE,
            path=attr_path,
            name=attr_name,
            value=scalar_value(attr_value),
        )
        if ":" in attr_name:
            attr_node.namespace, attr_node.name = attr_name.split(":", 1)
        node.attributes.append(attr_node)

    if text_content:
        text_path = f"{path}#text"
        text_node = DataNode(
            node_id=f"{node_id_prefix}:{text_path}",
            kind=DataNodeKind.XML_TEXT,
            path=text_path,
            name="#text",
            value=scalar_value(text_content),
        )
        node.children.append(text_node)

    for special in special_nodes:
        if isinstance(special, dict) and "@type" in special:
            special_path = f"{path}@{special['@type']}"
            special_node = DataNode(
                node_id=f"{node_id_prefix}:{special_path}",
                kind=DataNodeKind(special["@type"]),
                path=special_path,
                value=scalar_value(special.get("@content", "")),
            )
            node.children.append(special_node)

    for key, child_value in value.items():
        if key.startswith("@") or key == "#text":
            continue
        child_path = f"{path}.{key}" if path != "$" else f"$.{key}"
        if isinstance(child_value, list):
            for index, item in enumerate(child_value):
                item_path = f"{child_path}[{index}]"
                child_node = build_node_from_python(
                    item,
                    path=item_path,
                    name=key,
                    node_id_prefix=node_id_prefix,
                    parent_kind=DataNodeKind.XML_ELEMENT,
                )
                node.children.append(child_node)
        else:
            child_node = build_node_from_python(
                child_value,
                path=child_path,
                name=key,
                node_id_prefix=node_id_prefix,
                parent_kind=DataNodeKind.XML_ELEMENT,
            )
            node.children.append(child_node)

    return node


def _xml_element_to_dict(node: DataNode) -> dict[str, Any] | None:
    result: dict[str, Any] = {}

    element_name = node.name or ""
    if node.namespace:
        element_name = f"{node.namespace}:{element_name}"

    if node.attributes:
        attrs = {}
        for attr in node.attributes:
            attr_name = attr.name or ""
            if attr.namespace:
                attr_name = f"{attr.namespace}:{attr_name}"
            attrs[attr_name] = node_to_python(attr)
        result["@attributes"] = attrs

    if node.metadata.get("xmlns"):
        result["@xmlns"] = node.metadata["xmlns"]

    child_elements = []
    text_parts = []
    other_nodes = []

    for child in node.children:
        if child.kind == DataNodeKind.XML_ELEMENT:
            child_elements.append(child)
        elif child.kind == DataNodeKind.XML_TEXT:
            text_parts.append(node_to_python(child))
        elif child.kind == DataNodeKind.XML_CDATA:
            text_parts.append(node_to_python(child))
        else:
            other_nodes.append(child)

    if text_parts:
        text_content = "".join(str(part) for part in text_parts).strip()
        if text_content:
            result["#text"] = text_content

    if other_nodes:
        result["@special"] = [node_to_python(n) for n in other_nodes]

    if child_elements:
        children_by_name: dict[str, list] = {}
        for child in child_elements:
            child_name = child.name or ""
            if child.namespace:
                child_name = f"{child.namespace}:{child_name}"

            child_value = _xml_element_to_dict(child)
            if isinstance(child_value, dict) and "#text" in child_value and len(child_value) == 1:
                child_value = child_value["#text"]

            children_by_name.setdefault(child_name, []).append(child_value)

        for child_name, child_values in children_by_name.items():
            result[child_name] = child_values[0] if len(child_values) == 1 else child_values

    if len(result) == 1 and "#text" in result:
        return result["#text"]

    return result if result else None
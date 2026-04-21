# engines/document/models/dsdm_models

from __future__ import annotations

import base64
import hashlib
from enum import Enum
from datetime import datetime
from decimal import Decimal
from uuid import UUID
from typing import Optional, Dict, Any, List, Union, Literal

from pydantic import BaseModel, Field, ConfigDict
from dataclasses import dataclass, field

from engines.document.models.base import BaseDocument

class DataNodeKind(str, Enum):
    OBJECT = "object"
    ARRAY = "array"
    SCALAR = "scalar"
    XML_ELEMENT = "xml_element"
    XML_ATTRIBUTE = "xml_attribute"
    XML_TEXT = "xml_text"

    # XML-specific
    XML_PROCESSING_INSTRUCTION = "xml_processing_instruction"
    XML_DOCTYPE = "xml_doctype"
    XML_COMMENT = "xml_comment"
    XML_CDATA = "xml_cdata"
        
    # General
    COMMENT = "comment"  # For JSON/YAML comments

class ScalarType(str, Enum):
    # Existing types
    NULL = "null"
    BOOLEAN = "boolean"
    INTEGER = "integer"
    FLOAT = "float"
    STRING = "string"
    
    # Extended types for binary formats
    BINARY = "binary"  # Raw bytes
    DATETIME = "datetime"
    TIMESTAMP = "timestamp"  # Unix timestamp
    DECIMAL = "decimal"
    OBJECT_ID = "object_id"  # MongoDB ObjectId
    UUID = "uuid"
    REGEX = "regex"  # Regular expression

    DATE = "date"
    TIME = "time"
    DURATION = "duration"
    URI = "uri"
    EMAIL = "email"
    CUSTOM = "custom"

class DataValue(BaseModel):
    scalar_type: ScalarType
    value: Any = None
    lexical_value: Optional[str] = None


class DataSchemaReference(BaseModel):
    name: Optional[str] = None
    uri: Optional[str] = None
    version: Optional[str] = None


class DataDocumentCapabilities(BaseModel):
    supports_comments: bool = False
    supports_namespaces: bool = False
    supports_attributes: bool = False
    supports_tags: bool = False
    supports_binary_payloads: bool = False
    ordered_mappings: bool = True


class DataNode(BaseModel):
    """گره داده در ساختار سلسله‌مراتبی"""
    
    node_id: str
    path: str
    name: Optional[str] = None
    # key: str = Field(..., description="کلید گره")
    kind: DataNodeKind = Field(..., description="نوع گره")
    value: Optional[DataValue] = None #"مقدار گره"

    # برای ساختارهای سلسله‌مراتبی
    children: List['DataNode'] = Field(default_factory=list, description="گره‌های فرزند")
    # parent_key: Optional[str] = Field(None, description="کلید گره والد")

    # متادیتا
    metadata: Dict[str, Any] = Field(default_factory=dict, description="متادیتای گره")
    # schema_info: Optional[Dict[str, Any]] = Field(None, description="اطلاعات schema")

    attributes: List["DataNode"] = Field(default_factory=list)
    namespace: Optional[str] = None

    # اعتبارسنجی
    is_required: bool = Field(default=False, description="آیا گره اجباری است؟")
    validation_rules: List[str] = Field(default_factory=list, description="قوانین اعتبارسنجی")
    
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        validate_assignment=True
    )
    
    @property
    def is_leaf(self) -> bool:
        """آیا گره برگ است (فرزندی ندارد)؟"""
        return len(self.children) == 0
    
    # @property
    # def depth(self) -> int:
    #     """عمق گره در ساختار سلسله‌مراتبی"""
    #     if not self.parent_key:
    #         return 0
    #     # محاسبه بازگشتی (نیازمند پیاده‌سازی کامل)
    #     return 1

class DataDocument(BaseDocument):
    # ساختار داده
    root: DataNode # "گره ریشه ساختار داده"
    # nodes: List[DataNode] = Field(default_factory=list, description="تمام گره‌های سند")
    schema_ref: Optional[DataSchemaReference] = None
    capabilities: DataDocumentCapabilities = Field(default_factory=DataDocumentCapabilities)
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        validate_assignment=True
    )

def scalar_value(value: Any) -> DataValue:
    if value is None:
        return DataValue(scalar_type=ScalarType.NULL, value=None, lexical_value="null")
    if isinstance(value, bool):
        return DataValue(scalar_type=ScalarType.BOOLEAN, value=value, lexical_value=str(value).lower())
    if isinstance(value, int) and not isinstance(value, bool):
        return DataValue(scalar_type=ScalarType.INTEGER, value=value, lexical_value=str(value))
    if isinstance(value, float):
        return DataValue(scalar_type=ScalarType.FLOAT, value=value, lexical_value=repr(value))
    return DataValue(scalar_type=ScalarType.STRING, value=str(value), lexical_value=str(value))


def build_node_from_python(
    value: Any, 
    path: str = "$", 
    name: Optional[str] = None, 
    node_id_prefix: str = "node",
    parent_kind: Optional[DataNodeKind] = None
) -> DataNode:
    """
    Build DataNode from Python native structures.
    Enhanced to handle XML-like structures.
    """
    node_id = f"{node_id_prefix}:{path}"
    
    # Handle dictionaries (could be objects or XML elements)
    if isinstance(value, dict):
        # Check if this looks like an XML element representation
        is_xml_element = False
        
        # Check for XML-specific keys
        xml_keys = {"@attributes", "#text", "@xmlns", "@special"}
        if any(key in value for key in xml_keys):
            is_xml_element = True
        # Check if parent is XML element
        elif parent_kind == DataNodeKind.XML_ELEMENT:
            is_xml_element = True
        
        if is_xml_element:
            # Handle as XML element
            return _build_xml_element_from_dict(value, path, name, node_id, node_id_prefix)
        else:
            # Handle as regular object
            node = DataNode(
                node_id=node_id, 
                kind=DataNodeKind.OBJECT, 
                path=path, 
                name=name
            )
            for key, child_value in value.items():
                child_path = f"{path}.{key}" if path != "$" else f"$.{key}"
                node.children.append(
                    build_node_from_python(
                        child_value, 
                        path=child_path, 
                        name=str(key), 
                        node_id_prefix=node_id_prefix,
                        parent_kind=DataNodeKind.OBJECT
                    )
                )
            return node
    
    # Handle lists (arrays)
    if isinstance(value, list):
        node = DataNode(
            node_id=node_id, 
            kind=DataNodeKind.ARRAY, 
            path=path, 
            name=name
        )
        for index, child_value in enumerate(value):
            child_path = f"{path}[{index}]"
            node.children.append(
                build_node_from_python(
                    child_value, 
                    path=child_path, 
                    name=str(index), 
                    node_id_prefix=node_id_prefix,
                    parent_kind=DataNodeKind.ARRAY
                )
            )
        return node
    
    # Handle scalar values
    return DataNode(
        node_id=node_id, 
        kind=DataNodeKind.SCALAR, 
        path=path, 
        name=name, 
        value=scalar_value(value)
    )


def node_to_python(node: DataNode) -> Any:
    """
    Convert a DataNode tree back to Python native structures.
    Handles XML elements with duplicate child names properly.
    """
    
    # Handle XML elements
    if node.kind == DataNodeKind.XML_ELEMENT:
        return _xml_element_to_dict(node)
    
    # Handle XML text nodes
    if node.kind == DataNodeKind.XML_TEXT:
        return node.value.value if node.value else ""
    
    # Handle XML attribute nodes
    if node.kind == DataNodeKind.XML_ATTRIBUTE:
        return node.value.value if node.value else ""
    
    # Handle XML processing instructions, comments, etc.
    if node.kind in {
        DataNodeKind.XML_PROCESSING_INSTRUCTION,
        DataNodeKind.XML_DOCTYPE,
        DataNodeKind.XML_COMMENT,
        DataNodeKind.XML_CDATA
    }:
        # Return as dictionary with type and content
        return {
            "@type": node.kind.value,
            "@content": node.value.value if node.value else ""
        }
            
    # Handle objects (dictionaries)
    if node.kind == DataNodeKind.OBJECT:
        result: dict[str, Any] = {}
        for child in node.children:
            child_value = node_to_python(child)
            if child.name is not None:
                # For XML-like structures, check if we need to convert to list
                if child.name in result:
                    # If we already have this key, convert to list
                    if not isinstance(result[child.name], list):
                        result[child.name] = [result[child.name]]
                    result[child.name].append(child_value)
                else:
                    result[child.name] = child_value
        return result
    
    # Handle arrays (lists)
    if node.kind == DataNodeKind.ARRAY:
        return [node_to_python(child) for child in node.children]
    
    # Handle scalar values
    if node.value is None:
        return None
    
    # Convert scalar value based on type
    if node.value.scalar_type == ScalarType.DATETIME:
        # Return datetime object if value is string, otherwise return as-is
        if isinstance(node.value.value, str):
            from datetime import datetime
            try:
                return datetime.fromisoformat(node.value.value.replace('Z', '+00:00'))
            except (ValueError, AttributeError):
                return node.value.value
    elif node.value.scalar_type == ScalarType.TIMESTAMP:
        # Convert timestamp to datetime if it's numeric
        if isinstance(node.value.value, (int, float)):
            from datetime import datetime
            return datetime.fromtimestamp(node.value.value)
    
    return node.value.value

def _xml_element_to_dict(node: DataNode) -> Optional[Dict[str, Any]]:
    """
    Convert an XML element node to Python dictionary with proper handling of:
    - Attributes
    - Text content
    - Child elements (including duplicates)
    - Mixed content (text + elements)
    - Namespaces
    """
    result: Dict[str, Any] = {}
    
    # Add namespace prefix if present
    element_name = node.name or ""
    if node.namespace:
        element_name = f"{node.namespace}:{element_name}"
    
    # Handle attributes
    if node.attributes:
        attrs = {}
        for attr in node.attributes:
            attr_name = attr.name or ""
            if attr.namespace:
                attr_name = f"{attr.namespace}:{attr_name}"
            attrs[attr_name] = node_to_python(attr)
        result["@attributes"] = attrs
    
    # Handle namespace declarations (xmlns attributes)
    if node.metadata.get("xmlns"):
        result["@xmlns"] = node.metadata["xmlns"]
    
    # Separate child elements by type
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
    
    # Handle text content
    if text_parts:
        text_content = "".join(str(part) for part in text_parts).strip()
        if text_content:
            result["#text"] = text_content
    
    # Handle other special nodes (comments, PIs, etc.)
    if other_nodes:
        result["@special"] = [node_to_python(n) for n in other_nodes]
    
    # Handle child elements - group by name
    if child_elements:
        children_by_name: Dict[str, Any] = {}
        for child in child_elements:
            child_name = child.name or ""
            if child.namespace:
                child_name = f"{child.namespace}:{child_name}"
            
            child_value = _xml_element_to_dict(child)
            
            # If this is a simple element with only text and no attributes
            if isinstance(child_value, dict) and "#text" in child_value and len(child_value) == 1:
                child_value = child_value["#text"]
            
            if child_name in children_by_name:
                children_by_name[child_name].append(child_value)
            else:
                children_by_name[child_name] = [child_value]
        
        # Add children to result
        for child_name, child_values in children_by_name.items():
            # If only one child with this name, don't wrap in list
            if len(child_values) == 1:
                result[child_name] = child_values[0]
            else:
                result[child_name] = child_values
    
    # If element has only text and no attributes or children, return just the text
    if len(result) == 1 and "#text" in result:
        return result["#text"]
    
    # If element has only attributes and text, keep as dict
    if not result:
        return None
    
    return result


def xml_to_python_dict(root_node: DataNode) -> Dict[str, Any]:
    """
    Convert an entire XML document (root element) to Python dictionary.
    Handles multiple root elements and document-level metadata.
    """
    # If root is XML_ELEMENT, convert it
    if root_node.kind == DataNodeKind.XML_ELEMENT:
        result = _xml_element_to_dict(root_node)
        
        # Add document-level metadata if present
        if root_node.metadata:
            doc_meta = {k: v for k, v in root_node.metadata.items() 
                       if not k.startswith("_")}
            if doc_meta:
                if not result:
                    result = {}
                result["@document"] = doc_meta
        
        return {root_node.name or "root": result}
    
    # If root has multiple XML children (like multiple root elements)
    if root_node.kind == DataNodeKind.OBJECT:
        result = {}
        for child in root_node.children:
            if child.kind == DataNodeKind.XML_ELEMENT:
                child_result = _xml_element_to_dict(child)
                result[child.name or f"element_{len(result)}"] = child_result
        
        return result
    
    return {}


def _build_xml_element_from_dict(
    value: dict, 
    path: str, 
    name: Optional[str], 
    node_id: str,
    node_id_prefix: str
) -> DataNode:
    """
    Build XML element DataNode from dictionary representation.
    """
    # Extract XML-specific parts
    attributes = value.get("@attributes", {})
    text_content = value.get("#text", "")
    xmlns = value.get("@xmlns")
    special_nodes = value.get("@special", [])
     
    # Create element node
    node = DataNode(
        node_id=node_id,
        kind=DataNodeKind.XML_ELEMENT,
        path=path,
        name=name
    )
    
    # Add namespace metadata
    if xmlns:
        node.metadata["xmlns"] = xmlns
    
    # Add attributes
    for attr_name, attr_value in attributes.items():
        attr_path = f"{path}@{attr_name}"
        attr_node = DataNode(
            node_id=f"{node_id_prefix}:{attr_path}",
            kind=DataNodeKind.XML_ATTRIBUTE,
            path=attr_path,
            name=attr_name,
            value=scalar_value(attr_value)
        )
        # Handle namespace in attribute name
        if ":" in attr_name:
            attr_node.namespace, attr_node.name = attr_name.split(":", 1)
        node.attributes.append(attr_node)
    
    # Add text content if present
    if text_content:
        text_path = f"{path}#text"
        text_node = DataNode(
            node_id=f"{node_id_prefix}:{text_path}",
            kind=DataNodeKind.XML_TEXT,
            path=text_path,
            name="#text",
            value=scalar_value(text_content)
        )
        node.children.append(text_node)
    
    # Add special nodes (comments, PIs, etc.)
    for special in special_nodes:
        if isinstance(special, dict) and "@type" in special:
            special_path = f"{path}@{special['@type']}"
            special_node = DataNode(
                node_id=f"{node_id_prefix}:{special_path}",
                kind=DataNodeKind(special["@type"]),
                path=special_path,
                value=scalar_value(special.get("@content", ""))
            )
            node.children.append(special_node)
    
    # Add child elements (all keys that aren't XML-specific)
    for key, child_value in value.items():
        if key.startswith("@") or key == "#text":
            continue
            
        child_path = f"{path}.{key}" if path != "$" else f"$.{key}"
        
        # Handle multiple children with same name
        if isinstance(child_value, list):
            for index, item in enumerate(child_value):
                item_path = f"{child_path}[{index}]"
                child_node = build_node_from_python(
                    item,
                    path=item_path,
                    name=key,
                    node_id_prefix=node_id_prefix,
                    parent_kind=DataNodeKind.XML_ELEMENT
                )
                node.children.append(child_node)
        else:
            child_node = build_node_from_python(
                child_value,
                path=child_path,
                name=key,
                node_id_prefix=node_id_prefix,
                parent_kind=DataNodeKind.XML_ELEMENT
            )
            node.children.append(child_node)
    
    return node


DataNode.model_rebuild()

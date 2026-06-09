# engines/document/models/dsdm_models.py
"""
DSDM – Data Standard Definition Model
========================================
Format‑independent representation of instance data (JSON, XML, YAML, ...).
Every DataNode can be linked to its MSDM definition for validation,
default injection, and schema extraction.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .base import BaseDocument
from .msdm_models import (
    MSDMDocument,
    Entity,
    Attribute,
    Constraint,
    ScalarType,
    DataType,
    EntityKind,
)


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class DataNodeKind(str, Enum):
    OBJECT = "object"
    ARRAY = "array"
    SCALAR = "scalar"
    XML_ELEMENT = "xml_element"
    XML_ATTRIBUTE = "xml_attribute"
    XML_TEXT = "xml_text"
    XML_PROCESSING_INSTRUCTION = "xml_processing_instruction"
    XML_DOCTYPE = "xml_doctype"
    XML_COMMENT = "xml_comment"
    XML_CDATA = "xml_cdata"
    COMMENT = "comment"


class DataValue(BaseModel):
    scalar_type: ScalarType
    value: Any = None
    lexical_value: str | None = None


class DataSchemaReference(BaseModel):
    name: str | None = None
    uri: str | None = None
    data_struct: Optional[MSDMDocument] = None
    version: str | None = None


class DataDocumentCapabilities(BaseModel):
    supports_comments: bool = False
    supports_namespaces: bool = False
    supports_attributes: bool = False
    supports_tags: bool = False
    supports_binary_payloads: bool = False
    ordered_mappings: bool = True


# ---------------------------------------------------------------------------
# SchemaBinding
# ---------------------------------------------------------------------------

class SchemaBinding(BaseModel):
    """Links a DataNode to exactly one schema element."""
    entity: Optional[Entity] = None
    attribute: Optional[Attribute] = None
    source_schema: Optional[MSDMDocument] = None

    @model_validator(mode='after')
    def check_one_binding(self):
        if self.entity is None and self.attribute is None:
            raise ValueError("SchemaBinding must define either an entity or an attribute")
        return self


# ---------------------------------------------------------------------------
# DataNode
# ---------------------------------------------------------------------------

class DataNode(BaseModel):
    node_id: str
    path: str
    name: str | None = None
    kind: DataNodeKind = Field(..., description="Node kind")
    value: DataValue | None = None

    children: list[DataNode] = Field(default_factory=list)
    attributes: list[DataNode] = Field(default_factory=list)   # XML attributes

    metadata: dict[str, Any] = Field(default_factory=dict)
    namespace: str | None = None

    is_required: bool = Field(default=False)
    validation_rules: list[str] = Field(default_factory=list)  # deprecated in favour of schema_binding

    schema_binding: Optional[SchemaBinding] = None

    model_config = ConfigDict(arbitrary_types_allowed=True, validate_assignment=True)

    @property
    def is_leaf(self) -> bool:
        return len(self.children) == 0


# ---------------------------------------------------------------------------
# DataDocument
# ---------------------------------------------------------------------------

class DataDocument(BaseDocument):
    root: DataNode
    schema_ref: Optional[DataSchemaReference] = None
    capabilities: DataDocumentCapabilities = Field(default_factory=DataDocumentCapabilities)

    model_config = ConfigDict(arbitrary_types_allowed=True, validate_assignment=True)

    def validate_against_schema(self) -> list[str]:
        errors: list[str] = []
        self._validate_node(self.root, errors)
        return errors

    def _validate_node(self, node: DataNode, errors: list[str]) -> None:
        if node.schema_binding is None:
            return

        attr = node.schema_binding.attribute
        if attr is not None:
            self._check_attribute_constraints(node, attr, errors)

        for child in node.children:
            self._validate_node(child, errors)
        for attr_node in node.attributes:
            self._validate_node(attr_node, errors)

    @staticmethod
    def _check_attribute_constraints(node: DataNode, attr: Attribute, errors: list[str]) -> None:
        if attr.required and node.value is None and not node.children:
            errors.append(f"Required field '{attr.name}' at path {node.path} is missing")
            return

        for constraint in attr.constraints:
            if constraint.type.value == "pattern" and constraint.value and node.value is not None:
                import re
                pattern = constraint.value
                if not re.match(pattern, str(node.value.value)):
                    errors.append(f"Pattern mismatch for '{attr.name}' at {node.path}: {node.value.value}")

    @classmethod
    def infer_msdm(
        cls,
        data_document: DataDocument,
        entity_name: str = "Root",
        kind: EntityKind = EntityKind.OBJECT,
    ) -> MSDMDocument:
        """Create an MSDMDocument schema from the data tree.
        Nested objects become separate entities referenced via ref_entity.
        """
        entities: list[Entity] = []
        root_entity = cls._entity_from_node(data_document.root, entity_name, kind, entities)
        entities.insert(0, root_entity)  # root entity at front
        return MSDMDocument(
            title=f"Inferred schema for {entity_name}",
            document_id=f"inferred:{entity_name}",
            media_type=data_document.media_type,
            entities=entities,
        )

    @classmethod
    def _entity_from_node(cls, node: DataNode, entity_name: str, kind: EntityKind, entities: list[Entity]) -> Entity:
        if node.kind != DataNodeKind.OBJECT:
            raise ValueError("Can only infer an Entity from an OBJECT DataNode")
        attributes = []
        for child in node.children:
            attr = cls._attribute_from_child(child, entities)
            if attr:
                attributes.append(attr)
        return Entity(name=entity_name, kind=kind, attributes=attributes)

    @classmethod
    def _attribute_from_child(cls, child: DataNode, entities: list[Entity]) -> Optional[Attribute]:
        name = child.name or "unknown"
        data_type = cls._infer_data_type(child, entities)
        return Attribute(name=name, data_type=data_type, required=True)

    @classmethod
    def _infer_data_type(cls, node: DataNode, entities: list[Entity]) -> DataType:
        if node.kind == DataNodeKind.OBJECT:
            # Create a separate entity for this nested object
            sub_name = node.name or f"inline_{len(entities)}"
            sub_entity = cls._entity_from_node(node, sub_name, EntityKind.OBJECT, entities)
            entities.append(sub_entity)
            return DataType(base=ScalarType.STRUCT, ref_entity=sub_entity)
        elif node.kind == DataNodeKind.ARRAY:
            elem = cls._infer_data_type(node.children[0], entities) if node.children else DataType(base=ScalarType.ANY)
            return DataType(base=ScalarType.ARRAY, element_type=elem)
        else:
            if node.value is None:
                return DataType(base=ScalarType.NULL)
            return DataType(base=node.value.scalar_type)


# Resolve forward references for pydantic v2
DataNode.model_rebuild()
DataDocument.model_rebuild()
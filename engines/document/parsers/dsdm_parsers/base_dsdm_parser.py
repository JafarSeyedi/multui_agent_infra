# engines/document/parsers/dsdm_parsers/base_dsdm_parser.py
"""
Base parser for all DSDM formats.
Schema binding, default injection, and validation are shared.
"""

from __future__ import annotations

from abc import abstractmethod
from typing import Any, Optional

from ...models.dsdm_models import (
    DataDocument,
    DataNode,
    DataNodeKind,
    SchemaBinding,
    DataValue,
    DataSchemaReference,   # added missing import
)
from ...models.msdm_models import (
    MSDMDocument,
    Entity,
    Attribute,
    ScalarType,
    DataType,
    EntityKind,
)
from ...models.media_types import MEDIA_TYPES, MediaType
from ..base import BaseDocumentParser, ParseOptions
from .dsdm_utils import scalar_value


class DSDMParseOptions(ParseOptions):
    msdm_schema: Optional[MSDMDocument] = None
    inject_defaults: bool = True
    validate_against_schema: bool = True


class BaseDSDMParser(BaseDocumentParser):
    name = "dsdm_base"

    async def parse_bytes(
        self,
        data: bytes,
        document_id: str,
        source_name: str,
        metadata: dict[str, Any] | None = None,
        options: ParseOptions | None = None,
    ) -> DataDocument:
        opts = DSDMParseOptions(**(options.dict() if options else {}))
        root_node = await self._parse_to_datanode(data, opts)

        media_str = self._detect_media_type(source_name)
        media_type = MEDIA_TYPES.get(media_str, MEDIA_TYPES["binary"])

        doc = DataDocument(
            title=source_name,
            document_id=document_id,
            media_type=media_type,
            root=root_node,
            metadata=metadata or {},
            validation_errors=[],
        )

        if opts.msdm_schema:
            self._bind_schema(doc, opts.msdm_schema, opts.inject_defaults, opts.validate_against_schema)

        if opts.validate_against_schema and opts.msdm_schema:
            doc.validation_errors = self._collect_validation_errors(doc.root)

        return doc

    @abstractmethod
    async def _parse_to_datanode(self, raw_bytes: bytes, options: DSDMParseOptions) -> DataNode:
        ...

    @abstractmethod
    def _detect_media_type(self, source_name: str) -> str:
        ...

    # ------------------------------------------------------------------
    # Schema integration
    # ------------------------------------------------------------------

    def _bind_schema(
        self,
        doc: DataDocument,
        schema: MSDMDocument,
        inject_defaults: bool,
        validate: bool,
    ) -> None:
        doc.schema_ref = DataSchemaReference(
            data_struct=schema,
            name=schema.schema_name,
        )
        root_entity = schema.entities[0] if schema.entities else None
        if root_entity:
            self._bind_node(doc.root, root_entity, schema, inject_defaults, validate)

    def _bind_node(
        self,
        node: DataNode,
        entity: Entity,
        full_schema: MSDMDocument,
        inject_defaults: bool,
        validate: bool,
    ) -> None:
        attr_map: dict[str, Attribute] = {attr.name: attr for attr in entity.attributes}

        for child in node.children:
            if child.name is None:
                continue
            attr_def = attr_map.get(child.name)
            if attr_def is None:
                continue

            child.schema_binding = SchemaBinding(
                attribute=attr_def,
                source_schema=full_schema,
            )

            if inject_defaults and attr_def.default_value is not None and child.value is None and not child.children:
                child.value = self._coerce_default_value(attr_def)

            if validate and attr_def.required and (child.value is None and not child.children):
                child.metadata["_required_missing"] = True

            # recursively bind for struct/array of struct
            if attr_def.data_type.base == ScalarType.STRUCT and child.kind == DataNodeKind.OBJECT:
                ref_entity = attr_def.data_type.ref_entity
                if ref_entity is not None:
                    sub_entity = self._resolve_entity(ref_entity, full_schema)
                    self._bind_node(child, sub_entity, full_schema, inject_defaults, validate)
                # else: no inline struct, skip
            elif attr_def.data_type.base == ScalarType.ARRAY and child.kind == DataNodeKind.ARRAY:
                elem_type = attr_def.data_type.element_type
                if elem_type and elem_type.base == ScalarType.STRUCT and elem_type.ref_entity is not None:
                    sub_entity = self._resolve_entity(elem_type.ref_entity, full_schema)
                    for item in child.children:
                        if item.kind == DataNodeKind.OBJECT:
                            self._bind_node(item, sub_entity, full_schema, inject_defaults, validate)

    def _coerce_default_value(self, attr: Attribute) -> DataValue:
        default_str = attr.default_value
        if default_str is None:
            return DataValue(scalar_type=ScalarType.NULL, value=None, lexical_value="null")
        dt = attr.data_type.base
        try:
            if dt == ScalarType.INT:
                return DataValue(scalar_type=ScalarType.INT, value=int(default_str), lexical_value=default_str)
            if dt == ScalarType.LONG:
                return DataValue(scalar_type=ScalarType.LONG, value=int(default_str), lexical_value=default_str)
            if dt == ScalarType.FLOAT:
                return DataValue(scalar_type=ScalarType.FLOAT, value=float(default_str), lexical_value=default_str)
            if dt == ScalarType.DOUBLE:
                return DataValue(scalar_type=ScalarType.DOUBLE, value=float(default_str), lexical_value=default_str)
            if dt == ScalarType.DECIMAL:
                from decimal import Decimal
                return DataValue(scalar_type=ScalarType.DECIMAL, value=Decimal(default_str), lexical_value=default_str)
            if dt == ScalarType.BOOLEAN:
                val = default_str.lower() in ('true', '1', 'yes')
                return DataValue(scalar_type=ScalarType.BOOLEAN, value=val, lexical_value=default_str)
            if dt == ScalarType.DATETIME:
                from datetime import datetime
                return DataValue(scalar_type=ScalarType.DATETIME, value=datetime.fromisoformat(default_str).isoformat(), lexical_value=default_str)
            if dt == ScalarType.DATE:
                from datetime import date
                return DataValue(scalar_type=ScalarType.DATE, value=date.fromisoformat(default_str).isoformat(), lexical_value=default_str)
            if dt == ScalarType.TIME:
                from datetime import time
                return DataValue(scalar_type=ScalarType.TIME, value=time.fromisoformat(default_str).isoformat(), lexical_value=default_str)
            if dt == ScalarType.BINARY:
                import base64
                return DataValue(scalar_type=ScalarType.BINARY, value=base64.b64decode(default_str), lexical_value=default_str)
            return scalar_value(default_str)
        except Exception:
            return scalar_value(default_str)

    def _collect_validation_errors(self, node: DataNode) -> list[str]:
        errors: list[str] = []
        self._collect_errors_recursive(node, errors)
        return errors

    def _collect_errors_recursive(self, node: DataNode, errors: list[str]) -> None:
        if node.metadata.get("_required_missing"):
            errors.append(f"Required field '{node.name}' at path {node.path} is missing")
        if node.schema_binding and node.schema_binding.attribute:
            attr = node.schema_binding.attribute
            for constraint in attr.constraints:
                if constraint.type.value == "pattern" and constraint.value and node.value is not None:
                    import re
                    if not re.match(constraint.value, str(node.value.value)):
                        errors.append(f"Pattern mismatch for '{attr.name}' at {node.path}: {node.value.value}")
        for child in node.children:
            self._collect_errors_recursive(child, errors)
        for attr_node in node.attributes:
            self._collect_errors_recursive(attr_node, errors)

    def _resolve_entity(self, ref, full_schema: MSDMDocument) -> Entity:
        if isinstance(ref, Entity):
            return ref
        for ent in full_schema.entities:
            if ent.name == ref:
                return ent
        raise ValueError(f"Entity '{ref}' not found in schema")
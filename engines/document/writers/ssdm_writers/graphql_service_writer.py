# engines/document/writers/ssdm_writers/graphql_service_writer.py
"""
GraphQL Service Writer – converts an SSDM_DOCUMENT into a GraphQL SDL string.

Uses the MSDM type definitions inside the SSDM document to reconstruct
the complete GraphQL schema.  Root operation types are taken from the
graphql_service.schema_entity (or from MSDM document annotations).
"""

from __future__ import annotations
from pathlib import Path
from typing import Optional, List, Dict, cast

from .base_ssdm_writer import BaseSSDMWriter, SSDMWriteOptions
from ...models.ssdm_models import SSDM_DOCUMENT
from ...models.msdm_models import (
    MSDMDocument,
    Entity,
    Attribute,
    ScalarType,
    ConstraintType,
)
from ...models.base import BaseDocument


class GraphQLServiceWriter(BaseSSDMWriter):
    """Serialises an SSDM_DOCUMENT to GraphQL SDL."""

    name = "graphql_service"
    supported_extensions = (".graphql", ".gql")

    def __init__(self, options: Optional[SSDMWriteOptions] = None):
        super().__init__(options)

    async def _write_design(self, document: SSDM_DOCUMENT) -> bytes:
        lines: List[str] = []
        msdm = document.type_definitions
        if msdm is None:
            # Nothing to write
            sdl = ""
            return sdl.encode(self.options.encoding or "utf-8")

        # 1. Schema definition
        schema_block = self._build_schema_definition(document, msdm)
        if schema_block:
            lines.append(schema_block)
            lines.append("")

        # 2. Scalars
        for entity in msdm.entities:
            if self._is_scalar_type(entity):
                lines.append(self._build_scalar(entity))
                lines.append("")

        # 3. Enums
        for entity in msdm.entities:
            if self._is_enum_type(entity):
                lines.append(self._build_enum(entity))
                lines.append("")

        # 4. Interfaces
        for entity in msdm.entities:
            if self._is_interface_type(entity):
                lines.append(self._build_interface(entity))
                lines.append("")

        # 5. Objects
        for entity in msdm.entities:
            if self._is_object_type(entity):
                lines.append(self._build_object(entity))
                lines.append("")

        # 6. Unions
        for entity in msdm.entities:
            if self._is_union_type(entity):
                lines.append(self._build_union(entity))
                lines.append("")

        # 7. Inputs
        for entity in msdm.entities:
            if self._is_input_type(entity):
                lines.append(self._build_input(entity))
                lines.append("")

        sdl = "\n".join(lines).strip()
        return sdl.encode(self.options.encoding or "utf-8")

    def get_supported_media_types(self) -> list[str]:
        return ["application/graphql"]

    def get_supported_extensions(self) -> list[str]:
        return list(self.supported_extensions)

    # ── Type detection helpers (reuse annotations from MSDM parser) ──
    def _is_scalar_type(self, entity: Entity) -> bool:
        # Scalars have no fields and are not enums/unions/inputs
        return (not entity.attributes
                and not self._has_annotation(entity, "enum_member")
                and not self._has_annotation(entity, "union_members")
                and not self._has_annotation(entity, "input"))

    def _is_enum_type(self, entity: Entity) -> bool:
        return self._has_annotation(entity, "enum_member")

    def _is_interface_type(self, entity: Entity) -> bool:
        return self._has_annotation(entity, "interface") == "true"

    def _is_object_type(self, entity: Entity) -> bool:
        return (not self._is_interface_type(entity)
                and not self._is_enum_type(entity)
                and not self._is_union_type(entity)
                and not self._is_input_type(entity)
                and not self._is_scalar_type(entity))

    def _is_union_type(self, entity: Entity) -> bool:
        return self._has_annotation(entity, "union_members")

    def _is_input_type(self, entity: Entity) -> bool:
        return self._has_annotation(entity, "input") == "true"

    # ── Build schema block ──────────────────────────────────────────
    def _build_schema_definition(self, ssdm_doc: SSDM_DOCUMENT, msdm: MSDMDocument) -> Optional[str]:
        query = None
        mutation = None
        subscription = None
        # Try to get from graphql_service first
        if ssdm_doc.graphql_service and ssdm_doc.graphql_service.schema_entity:
            root_entity = ssdm_doc.graphql_service.schema_entity
            # The root entity likely has fields named "query", "mutation", "subscription"
            for attr in root_entity.attributes:
                if attr.name == "query":
                    query = attr.data_type.ref_entity or "Query"
                elif attr.name == "mutation":
                    mutation = attr.data_type.ref_entity or "Mutation"
                elif attr.name == "subscription":
                    subscription = attr.data_type.ref_entity or "Subscription"
        # Fallback: look for annotations on the MSDM document (from MSDM parser round‑trip)
        if query is None:
            query = self._get_doc_annotation(msdm, "root_query")
        if mutation is None:
            mutation = self._get_doc_annotation(msdm, "root_mutation")
        if subscription is None:
            subscription = self._get_doc_annotation(msdm, "root_subscription")

        if query or mutation or subscription:
            lines = ["schema {"]
            if query:
                lines.append(f"  query: {query}")
            if mutation:
                lines.append(f"  mutation: {mutation}")
            if subscription:
                lines.append(f"  subscription: {subscription}")
            lines.append("}")
            return "\n".join(lines)
        return None

    # ── Build scalar ─────────────────────────────────────────────────
    def _build_scalar(self, entity: Entity) -> str:
        desc = entity.description
        result = ""
        if desc:
            result += f'"""{desc}"""\n'
        result += f"scalar {entity.name}"
        return result

    # ── Build enum ───────────────────────────────────────────────────
    def _build_enum(self, entity: Entity) -> str:
        desc = entity.description
        lines = []
        if desc:
            lines.append(f'"""{desc}"""')
        lines.append(f"enum {entity.name} {{")
        for ann in entity.annotations:
            if ann.key == "enum_member":
                value = ann.value.split("=")[0].strip()
                lines.append(f"  {value}")
        lines.append("}")
        return "\n".join(lines)

    # ── Build interface ──────────────────────────────────────────────
    def _build_interface(self, entity: Entity) -> str:
        desc = entity.description
        lines = []
        if desc:
            lines.append(f'"""{desc}"""')
        header = f"interface {entity.name} {{"
        lines.append(header)
        for attr in entity.attributes:
            lines.append(f"  {self._field_to_graphql(attr)}")
        lines.append("}")
        return "\n".join(lines)

    # ── Build object type ────────────────────────────────────────────
    def _build_object(self, entity: Entity) -> str:
        desc = entity.description
        lines = []
        if desc:
            lines.append(f'"""{desc}"""')
        implements = []
        for iface in entity.implements:
            implements.append(iface)
        header = f"type {entity.name}"
        if implements:
            header += " implements " + " & ".join(implements)
        header += " {"
        lines.append(header)
        for attr in entity.attributes:
            lines.append(f"  {self._field_to_graphql(attr)}")
        lines.append("}")
        return "\n".join(lines)

    # ── Build union ─────────────────────────────────────────────────
    def _build_union(self, entity: Entity) -> str:
        desc = entity.description
        lines = []
        if desc:
            lines.append(f'"""{desc}"""')
        members_raw = self._get_annotation(entity, "union_members")
        if members_raw:
            import json
            try:
                members = json.loads(members_raw)
            except json.JSONDecodeError:
                members = [members_raw]
        else:
            members = []
        member_str = " | ".join(members) if members else " /* no members */"
        lines.append(f"union {entity.name} = {member_str}")
        return "\n".join(lines)

    # ── Build input type ────────────────────────────────────────────
    def _build_input(self, entity: Entity) -> str:
        desc = entity.description
        lines = []
        if desc:
            lines.append(f'"""{desc}"""')
        lines.append(f"input {entity.name} {{")
        for attr in entity.attributes:
            field_str = f"  {attr.name}: {self._type_to_graphql(attr)}"
            lines.append(field_str)
        lines.append("}")
        return "\n".join(lines)

    # ── Field formatting ────────────────────────────────────────────
    def _field_to_graphql(self, attr: Attribute) -> str:
        name = attr.name
        # Arguments (stored as annotation "arguments" by MSDM parser)
        args_str = ""
        args_raw = self._get_annotation(attr, "arguments")
        if args_raw:
            import json
            try:
                args_list = json.loads(args_raw)
            except json.JSONDecodeError:
                args_list = []
            if args_list:
                arg_parts = []
                for arg in args_list:
                    arg_def = f"{arg['name']}: {arg['type']}"
                    if arg.get("defaultValue"):
                        arg_def += f" = {arg['defaultValue']}"
                    arg_parts.append(arg_def)
                args_str = f"({', '.join(arg_parts)})"

        type_str = self._type_to_graphql(attr)
        # Directives (stored as annotation)
        dirs = ""
        for ann in attr.annotations:
            if ann.key == "directive":
                dirs += f" {ann.value}"
        return f"{name}{args_str}: {type_str}{dirs}"

    # ── Type string conversion ─────────────────────────────────────
    def _type_to_graphql(self, attr: Attribute) -> str:
        # If the parser stored the original type string, use it for round‑trip
        orig = self._get_annotation(attr, "graphql_type")
        if orig:
            return orig
        dt = attr.data_type
        base = dt.base
        if base == ScalarType.ARRAY:
            inner = self._datatype_to_gql(dt.element_type) if dt.element_type else "String"
            return f"[{inner}]"
        if base == ScalarType.REF:
            return dt.ref_entity or "Unknown"
        if base == ScalarType.STRUCT:
            # Should be a reference; fallback
            return dt.ref_entity or "Object"
        graphql_name = self._scalar_to_gql(base)
        if attr.required and not graphql_name.endswith("!"):
            graphql_name += "!"
        return graphql_name

    @staticmethod
    def _scalar_to_gql(base: ScalarType) -> str:
        mapping = {
            ScalarType.STRING: "String",
            ScalarType.INT: "Int",
            ScalarType.LONG: "Int",
            ScalarType.FLOAT: "Float",
            ScalarType.DOUBLE: "Float",
            ScalarType.BOOLEAN: "Boolean",
            ScalarType.UUID: "ID",
            ScalarType.DATE: "String",
            ScalarType.TIMESTAMP: "String",
            ScalarType.TIME: "String",
            ScalarType.DURATION: "String",
            ScalarType.BINARY: "String",
            ScalarType.DECIMAL: "Float",
            ScalarType.ANY: "String",
        }
        return mapping.get(base, "String")

    @staticmethod
    def _datatype_to_gql(dt) -> str:
        from ...models.msdm_models import DataType
        if dt is None:
            return "String"
        return GraphQLServiceWriter._scalar_to_gql(dt.base)

    # ── Annotation helpers (fallback for MSDM round‑trip data) ────
    @staticmethod
    def _get_annotation(obj, key: str) -> Optional[str]:
        for ann in getattr(obj, 'annotations', []):
            if ann.key == key:
                return ann.value
        return None

    @staticmethod
    def _has_annotation(obj, key: str) -> bool:
        return GraphQLServiceWriter._get_annotation(obj, key) is not None

    @staticmethod
    def _get_doc_annotation(msdm: MSDMDocument, key: str) -> Optional[str]:
        for ann in msdm.annotations:
            if ann.key == key:
                return ann.value
        return None
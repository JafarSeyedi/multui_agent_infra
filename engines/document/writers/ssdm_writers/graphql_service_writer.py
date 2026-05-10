# engines/document/writers/ssdm_writers/graphql_service_writer.py
"""
GraphQL Service Writer – converts an SSDMDocument into a GraphQL SDL string.

Uses the MSDM type definitions inside the SSDM document to reconstruct
the complete GraphQL schema. Root operation types are taken from the
document metadata (keys "graphql:query_type", "graphql:mutation_type",
"graphql:subscription_type") set by the GraphQL parser.
"""
from __future__ import annotations

import json

from ...models.msdm_models import Attribute
from ...models.msdm_models import Entity
from ...models.msdm_models import MSDMDocument
from ...models.msdm_models import ScalarType
from ...models.ssdm_models import SSDMDocument
from .base_ssdm_writer import BaseSSDMWriter
from .base_ssdm_writer import SSDMWriteOptions


class GraphQLServiceWriter(BaseSSDMWriter):
    """Serialises an SSDMDocument to GraphQL SDL."""

    name = "graphql_service"
    supported_extensions = (".graphql", ".gql")

    def __init__(self, options: SSDMWriteOptions | None = None):
        super().__init__(options)

    async def _write_design(self, document: SSDMDocument) -> bytes:
        lines: list[str] = []
        msdm = document.type_definitions
        if msdm is None:
            # Nothing to write
            sdl = ""
            return sdl.encode(getattr(self.options, "encoding", "utf-8") or "utf-8")

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

        # 4. Objects
        for entity in msdm.entities:
            if self._is_object_type(entity):
                lines.append(self._build_object(entity))
                lines.append("")

        # 5. Unions
        for entity in msdm.entities:
            if self._is_union_type(entity):
                lines.append(self._build_union(entity))
                lines.append("")

        # 6. Inputs
        for entity in msdm.entities:
            if self._is_input_type(entity):
                lines.append(self._build_input(entity))
                lines.append("")

        sdl = "\n".join(lines).strip()
        return sdl.encode(getattr(self.options, "encoding", "utf-8") or "utf-8")

    def get_supported_media_types(self) -> list[str]:
        return ["application/graphql"]

    def get_supported_extensions(self) -> list[str]:
        return list(self.supported_extensions)

    # ── Type detection helpers (using annotations) ──
    def _get_annotation(self, obj, key: str) -> str | None:
        for ann in getattr(obj, 'annotations', []):
            if ann.key == key:
                return ann.value
        return None

    def _has_annotation(self, obj, key: str) -> bool:
        return self._get_annotation(obj, key) is not None

    def _is_scalar_type(self, entity: Entity) -> bool:
        return self._has_annotation(entity, "graphql:scalar") or (not entity.attributes
                and not self._has_annotation(entity, "enum_values")
                and not self._has_annotation(entity, "union_members")
                and not self._has_annotation(entity, "input"))

    def _is_enum_type(self, entity: Entity) -> bool:
        return self._has_annotation(entity, "enum_values")

    def _is_object_type(self, entity: Entity) -> bool:
        return (not self._is_scalar_type(entity)
                and not self._is_enum_type(entity)
                and not self._is_union_type(entity)
                and not self._is_input_type(entity))

    def _is_union_type(self, entity: Entity) -> bool:
        return self._has_annotation(entity, "union_members")

    def _is_input_type(self, entity: Entity) -> bool:
        return self._has_annotation(entity, "input") or entity.name.endswith("Input")

    # ── Build schema block ──────────────────────────────────────────
    def _build_schema_definition(self, ssdm_doc: SSDMDocument, msdm: MSDMDocument) -> str | None:
        # Try to get from document metadata (set by GraphQL parser)
        query = ssdm_doc.metadata.get("graphql:query_type")
        mutation = ssdm_doc.metadata.get("graphql:mutation_type")
        subscription = ssdm_doc.metadata.get("graphql:subscription_type")

        if not query and not mutation and not subscription:
            return None

        lines = ["schema {"]
        if query:
            lines.append(f"  query: {query}")
        if mutation:
            lines.append(f"  mutation: {mutation}")
        if subscription:
            lines.append(f"  subscription: {subscription}")
        lines.append("}")
        return "\n".join(lines)

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
        enum_vals = self._get_annotation(entity, "enum_values")
        if enum_vals:
            for val in enum_vals.split(","):
                lines.append(f"  {val.strip()}")
        lines.append("}")
        return "\n".join(lines)

    # ── Build object type ────────────────────────────────────────────
    def _build_object(self, entity: Entity) -> str:
        desc = entity.description
        lines = []
        if desc:
            lines.append(f'"""{desc}"""')
        implements = []
        impl_ann = self._get_annotation(entity, "implements")
        if impl_ann:
            implements = impl_ann.split(",")
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
        members = []
        # Try to get from composition first
        if entity.composition and entity.composition.composition_type == "oneOf":
            members = entity.composition.member_ids
        else:
            members_raw = self._get_annotation(entity, "union_members")
            if members_raw:
                try:
                    members = json.loads(members_raw)
                except json.JSONDecodeError:
                    members = [members_raw]
        member_str = " | ".join(members) if members else "/* no members */"
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
        # Arguments (stored as annotation "arguments")
        args_str = ""
        args_raw = self._get_annotation(attr, "arguments")
        if args_raw:
            try:
                args_list = json.loads(args_raw)
            except json.JSONDecodeError:
                args_list = []
            if args_list:
                arg_parts = []
                for arg in args_list:
                    # arg may be a tuple or dict; assume tuple (name, type, default)
                    if isinstance(arg, (list, tuple)) and len(arg) >= 2:
                        arg_name = arg[0]
                        arg_type = arg[1]
                        arg_default = arg[2] if len(arg) > 2 else None
                        arg_def = f"{arg_name}: {arg_type}"
                        if arg_default:
                            arg_def += f" = {arg_default}"
                    else:
                        continue
                    arg_parts.append(arg_def)
                args_str = f"({', '.join(arg_parts)})"

        type_str = self._type_to_graphql(attr)
        # Directives (stored as annotation "directives")
        dirs = ""
        dir_val = self._get_annotation(attr, "directives")
        if dir_val:
            try:
                dir_dict = json.loads(dir_val)
                parts = []
                for dname, dargs in dir_dict.items():
                    if dargs:
                        args_str_dir = ",".join(f"{k}:{v}" for k, v in dargs.items())
                        parts.append(f"@{dname}({args_str_dir})")
                    else:
                        parts.append(f"@{dname}")
                dirs = " " + " ".join(parts)
            except (json.JSONDecodeError, TypeError):
                dirs = f" {dir_val}"
        return f"{name}{args_str}: {type_str}{dirs}"

    # ── Type string conversion ─────────────────────────────────────
    def _type_to_graphql(self, attr: Attribute) -> str:
        # If the parser stored the original type string, use it
        orig = self._get_annotation(attr, "graphql_type")
        if orig:
            typ = orig
        else:
            dt = attr.data_type
            base = dt.base
            if base == ScalarType.ARRAY:
                inner = self._datatype_to_gql(dt.element_type) if dt.element_type else "String"
                typ = f"[{inner}]"
            elif base == ScalarType.REF:
                ref_name = dt.ref_entity_id or (dt.ref_entity.name if dt.ref_entity else None)
                if ref_name is None:
                    ref_name = "Unknown"
                typ = ref_name
            elif base == ScalarType.STRUCT:
                ref_name = dt.ref_entity_id or (dt.ref_entity.name if dt.ref_entity else None)
                if ref_name is None:
                    ref_name = "Object"
                typ = ref_name
            else:
                typ = self._scalar_to_gql(base)
        if attr.required and not typ.endswith("!"):
            typ += "!"
        return typ

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
        if dt is None:
            return "String"
        if dt.base == ScalarType.REF:
            return dt.ref_entity_id or "Unknown"
        return GraphQLServiceWriter._scalar_to_gql(dt.base)
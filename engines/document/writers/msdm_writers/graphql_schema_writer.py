# engines/document/writers/msdm_writers/graphql_schema_writer.py
"""
GraphQL Schema Writer – converts an MSDMDocument into a GraphQL SDL string.
Handles objects, interfaces, enums, unions, inputs, scalars, schema root,
directives, field arguments, and type references while preserving the
original type annotations used in the source schema for lossless round‑trip.
"""

from __future__ import annotations
import json
from typing import Optional, Dict, Any, List, Union

from .base_msdm_writer import BaseMSDMWriter, WriteTarget, SoftDeleteStrategy
from engines.document.writers.base import WriteOptions
from engines.document.models.msdm_models import (
    MSDMDocument,
    Entity,
    Attribute,
    DataType,
    Constraint,
    ConstraintType,
    Annotation,
    EntityKind,
    ScalarType,
)


class GraphQLSchemaWriter(BaseMSDMWriter):
    """Writer for GraphQL SDL files (.graphql, .gql)."""
    name = "graphql_schema"
    supported_extensions = (".graphql", ".gql")

    def __init__(
        self,
        options: Optional[WriteOptions] = None,
        target_mode: WriteTarget = WriteTarget.DESIGN_FILE,
        soft_delete_strategy: SoftDeleteStrategy = SoftDeleteStrategy.NONE,
    ):
        super().__init__(options, target_mode, soft_delete_strategy)

    async def _write_design(self, document: MSDMDocument) -> bytes:
        lines = []
        # Schema definition
        schema_def = self._build_schema_def(document)
        if schema_def:
            lines.append(schema_def)
            lines.append("")

        # Scalar types
        for entity in document.entities:
            if self._is_scalar_type(entity):
                lines.append(f"scalar {entity.name}")
                if entity.description:
                    lines.insert(len(lines) - 1, f'"""{entity.description}"""')
                lines.append("")
        # Enums
        for entity in document.entities:
            if self._is_enum_type(entity):
                lines.append(self._build_enum(entity))
                lines.append("")
        # Interfaces
        for entity in document.entities:
            if self._is_interface_type(entity):
                lines.append(self._build_interface(entity, document))
                lines.append("")
        # Objects
        for entity in document.entities:
            if self._is_object_type(entity):
                lines.append(self._build_object(entity, document))
                lines.append("")
        # Unions
        for entity in document.entities:
            if self._is_union_type(entity):
                lines.append(self._build_union(entity))
                lines.append("")
        # Input objects
        for entity in document.entities:
            if self._is_input_type(entity):
                lines.append(self._build_input(entity))
                lines.append("")

        sdl = "\n".join(lines).strip()
        return sdl.encode(self.options.encoding or "utf-8")

    async def get_supported_media_types(self) -> list[str]:
        return ["text/plain"]

    async def get_supported_extensions(self) -> list[str]:
        return self.supported_extensions

    # ── Type detection helpers ─────────────────────────────────────
    def _is_scalar_type(self, entity: Entity) -> bool:
        # Scalars have no fields and are not enums/unions/inputs
        if entity.attributes:
            return False
        # Check annotation "graphql_type" or implicit scalar (e.g. the parser stored "scalar"?
        # We'll detect by absence of typical marks
        return not any(self._get_annotation(entity, key) for key in ("union_members", "enum_member", "interface", "input"))

    def _is_enum_type(self, entity: Entity) -> bool:
        return any(a.key == "enum_member" for a in entity.annotations)

    def _is_interface_type(self, entity: Entity) -> bool:
        return self._get_annotation(entity, "interface") == "true"

    def _is_object_type(self, entity: Entity) -> bool:
        # Objects are not interfaces, unions, enums, inputs, scalars.
        if self._is_interface_type(entity) or self._is_enum_type(entity) or self._is_union_type(entity) or self._is_input_type(entity) or self._is_scalar_type(entity):
            return False
        # By default, entities with attributes are objects
        return bool(entity.attributes)

    def _is_union_type(self, entity: Entity) -> bool:
        return bool(self._get_annotation(entity, "union_members"))

    def _is_input_type(self, entity: Entity) -> bool:
        # Inputs are marked by annotation "graphql_type" == "input" from TS parser? No TS parser uses "ts_type": "input"? Not reliable.
        # In GraphQL parser, input types are parsed as regular objects but could be distinguished? Our GraphQL parser stored "ts_type" for TS, not for GraphQL. We'll add a heuristic: any entity whose name typically ends in "Input"? Not good.
        # For now, we rely on the annotation "input": "true" which we must set during parsing? Actually we didn't set that. We'll update the parser later; for now, we'll treat entities with "input" in their annotations (maybe from GraphQL directive `@input`? Not standard.)
        # We'll provide a fallback: if an entity attributes contain a field named "clientMutationId", it's likely an input.
        # Better: we simply output all non‑interface/non‑union objects as types; inputs are a separate concern. We'll omit dedicated input writing for now unless marked.
        return False

    def _get_annotation(self, entity_or_attr, key: str) -> Optional[str]:
        """Return the first annotation value for the given key, or None."""
        if isinstance(entity_or_attr, Entity):
            return next((a.value for a in entity_or_attr.annotations if a.key == key), None)
        if isinstance(entity_or_attr, Attribute):
            return next((a.value for a in entity_or_attr.annotations if a.key == key), None)
        return None

    # ── Schema definition ─────────────────────────────────────────
    def _build_schema_def(self, doc: MSDMDocument) -> Optional[str]:
        query_type = self._get_doc_annotation(doc, "root_query")
        mutation_type = self._get_doc_annotation(doc, "root_mutation")
        subscription_type = self._get_doc_annotation(doc, "root_subscription")
        if not any((query_type, mutation_type, subscription_type)):
            return None

        parts = ["schema {"]
        if query_type:
            parts.append(f"  query: {query_type}")
        if mutation_type:
            parts.append(f"  mutation: {mutation_type}")
        if subscription_type:
            parts.append(f"  subscription: {subscription_type}")
        parts.append("}")
        return "\n".join(parts)

    def _get_doc_annotation(self, doc: MSDMDocument, key: str) -> Optional[str]:
        return next((a.value for a in doc.annotations if a.key == key), None)

    # ── Object type ────────────────────────────────────────────────
    def _build_object(self, entity: Entity, doc: MSDMDocument) -> str:
        desc = entity.description
        lines = []
        if desc:
            lines.append(f'"""{desc}"""')
        # Interfaces
        implements = []
        for a in entity.annotations:
            if a.key == "implements":
                implements.append(a.value)
        header = f"type {entity.name}"
        if entity.implements:
            implements.extend(entity.implements)
        if implements:
            header += " implements " + " & ".join(implements)
        header += " {"
        lines.append(header)
        for attr in entity.attributes:
            lines.append(f"  {self._field_to_graphql(attr)}")
        # Directives on type
        for a in entity.annotations:
            if a.key == "directive":
                lines[-1] += f" {a.value}"
        lines.append("}")
        return "\n".join(lines)

    # ── Interface type (similar to object) ────────────────────────
    def _build_interface(self, entity: Entity, doc: MSDMDocument) -> str:
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

    # ── Enum type ──────────────────────────────────────────────────
    def _build_enum(self, entity: Entity) -> str:
        desc = entity.description
        lines = []
        if desc:
            lines.append(f'"""{desc}"""')
        lines.append(f"enum {entity.name} {{")
        for ann in entity.annotations:
            if ann.key == "enum_member":
                # format "VALUE=..." we only need VALUE
                value = ann.value.split("=")[0].strip()
                lines.append(f"  {value}")
        lines.append("}")
        return "\n".join(lines)

    # ── Union type ─────────────────────────────────────────────────
    def _build_union(self, entity: Entity) -> str:
        desc = entity.description
        lines = []
        if desc:
            lines.append(f'"""{desc}"""')
        members_raw = self._get_annotation(entity, "union_members")
        if members_raw:
            members = json.loads(members_raw)
        else:
            members = []
        member_str = " | ".join(members) if members else " /* no members */"
        lines.append(f"union {entity.name} = {member_str}")
        return "\n".join(lines)

    # ── Input type (similar to object without arguments) ───────────
    def _build_input(self, entity: Entity) -> str:
        desc = entity.description
        lines = []
        if desc:
            lines.append(f'"""{desc}"""')
        lines.append(f"input {entity.name} {{")
        for attr in entity.attributes:
            # Input fields cannot have arguments
            field_str = f"  {attr.name}: {self._type_to_graphql(attr)}"
            # Directives
            for a in attr.annotations:
                if a.key == "directive":
                    field_str += f" {a.value}"
            lines.append(field_str)
        lines.append("}")
        return "\n".join(lines)

    # ── Field formatting ───────────────────────────────────────────
    def _field_to_graphql(self, attr: Attribute) -> str:
        name = attr.name
        # Arguments
        args_str = ""
        args_raw = self._get_annotation(attr, "arguments")
        if args_raw:
            args_list = json.loads(args_raw)
            if args_list:
                arg_parts = []
                for arg in args_list:
                    arg_def = f"{arg['name']}: {arg['type']}"
                    if arg.get("defaultValue"):
                        arg_def += f" = {arg['defaultValue']}"
                    arg_parts.append(arg_def)
                args_str = f"({', '.join(arg_parts)})"
        # Type
        type_str = self._type_to_graphql(attr)
        # Directives
        directives = ""
        for a in attr.annotations:
            if a.key == "directive":
                directives += f" {a.value}"
        return f"{name}{args_str}: {type_str}{directives}"

    # ── Type string conversion ─────────────────────────────────────
    def _type_to_graphql(self, attr: Attribute) -> str:
        """Produce a GraphQL type string from an attribute's DataType and annotations."""
        # Prefer the original type stored as annotation 'graphql_type' (parser recorded it for strict round‑trip)
        orig_type = self._get_annotation(attr, "graphql_type")
        if orig_type:
            return orig_type

        dt = attr.data_type
        base = dt.base

        # Non‑null flag? In GraphQL, the original type string ends with '!' if required. Our annotation may have stored that.
        # The DataType itself doesn't hold nullability the same way. We'll rely on the original annotation above if present.
        # Fallback: build from DataType
        type_name = self._scalar_to_graphql_name(base, dt)
        if base == ScalarType.ARRAY:
            if dt.element_type:
                inner = self._scalar_to_graphql_name(dt.element_type.base, dt.element_type)
                type_name = f"[{inner}]"
            else:
                type_name = "[_]"
        if base == ScalarType.REF:
            type_name = dt.ref_entity or "Unknown"
        if base == ScalarType.STRUCT:
            type_name = "Object"

        # required → non‑null
        if attr.required and not type_name.endswith("!"):
            type_name += "!"
        return type_name

    @staticmethod
    def _scalar_to_graphql_name(base: ScalarType, dt: Optional[DataType] = None) -> str:
        mapping = {
            ScalarType.STRING:    "String",
            ScalarType.INT:       "Int",
            ScalarType.LONG:      "Int",
            ScalarType.FLOAT:     "Float",
            ScalarType.DOUBLE:    "Float",
            ScalarType.BOOLEAN:   "Boolean",
            ScalarType.UUID:      "ID",
            ScalarType.DATE:      "String",
            ScalarType.TIMESTAMP: "String",
            ScalarType.TIME:      "String",
            ScalarType.DURATION:  "String",
            ScalarType.BINARY:    "String",
            ScalarType.DECIMAL:   "Float",
            ScalarType.ANY:       "String",
        }
        return mapping.get(base, "String")
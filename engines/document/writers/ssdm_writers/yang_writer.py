# engines/document/writers/ssdm_writers/yang_writer.py
"""
YANG 1.1 Writer – converts an SSDMDocument to YANG syntax.

Design decisions:
- choice → Entity.composition (ONE_OF) → output choice with cases
- grouping → Entity.is_template = True → output grouping
- uses → Attribute.template → output uses
- list → Attribute of ARRAY of REF → output list with entry entity
- container → Attribute of REF → output container
- leaf / leaf-list → direct attributes (leaf-list if ARRAY of scalar)
- must/when → Constraint (MUST/WHEN) on entity/attribute
- config/status → Entity/Attribute.is_config / version_status
- augment → Entity with augment_target_path annotation → output augment
- deviations → Entity.yang_deviate_targets → output deviation statements
- header metadata → doc.metadata (imports, includes, etc.)
- revisions → doc.metadata["yang_revisions"] -> revision statements
"""
from __future__ import annotations

from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any

from ...models.base import BaseDocument
from ...models.msdm_models import (
    Attribute, CompositionType, ConstraintType, DataType, Entity,
    ScalarType, VersionStatus
)
from ...models.ssdm_models import ServiceOperation, OperationType, SSDMDocument, YangMetadata
from ..base import BaseDocumentWriter, WriteOptions


class YANGWriter(BaseDocumentWriter):
    name = "yang"
    supported_extensions = (".yang",)

    def __init__(self, options: WriteOptions | None = None):
        super().__init__(options)

    async def write_stream(self, document: BaseDocument) -> AsyncIterator[bytes]:
        yield await self.write(document)

    async def write(self, document: BaseDocument) -> bytes:
        if not isinstance(document, SSDMDocument):
            raise TypeError(f"Expected SSDMDocument, got {type(document)}")
        return await self._write_yang(document)

    async def write_to_file(
        self, document: BaseDocument, target: Path, options: dict[str, Any] | None = None
    ) -> None:
        data = await self.write(document)
        with open(target, "wb") as f:
            f.write(data)

    def get_supported_media_types(self) -> list[str]:
        return ["text/plain", "application/yang"]

    def get_supported_extensions(self) -> list[str]:
        return list(self.supported_extensions)

    # ------------------------------------------------------------------
    # Main serialisation
    # ------------------------------------------------------------------
    async def _write_yang(self, doc: SSDMDocument) -> bytes:
        lines: list[str] = []

        # Module header
        module_name = doc.title or doc.metadata.get("yang_module_name", "unnamed")
        lines.append(f"module {self._quote_name(module_name)} {{")
        lines.append("")

        # yang-version
        lines.append(f"  yang-version {doc.metadata.get('yang_version', '1.1')};")
        # namespace
        ns = doc.metadata.get("yang_namespace")
        if not ns and doc.servers:
            ns = doc.servers[0].url
        if ns:
            lines.append(f"  namespace \"{ns}\";")
        else:
            raise ValueError("Missing namespace in YANG module")
        # prefix
        prefix = doc.metadata.get("yang_prefix") or (module_name[0].lower() if module_name else "mod")
        lines.append(f"  prefix {prefix};")
        # description
        if doc.description:
            lines.append(f"  description {self._quote_string(doc.description)};")
        # contact
        if doc.contact and doc.contact.name:
            contact_str = doc.contact.name
            if doc.contact.email:
                contact_str += f" <{doc.contact.email}>"
            lines.append(f"  contact \"{contact_str}\";")
        # organization
        if "yang_organization" in doc.metadata:
            lines.append(f"  organization {self._quote_string(doc.metadata['yang_organization'])};")
        # revisions
        revisions = doc.metadata.get("yang_revisions", [])
        if revisions:
            for rev_date, rev_desc in sorted(revisions, key=lambda x: x[0], reverse=True):
                lines.append(f"  revision {self._quote_string(rev_date)} {{")
                if rev_desc:
                    lines.append(f"    description {self._quote_string(rev_desc)};")
                lines.append("  }")
        elif doc.version and doc.version != "1.0.0":
            lines.append(f"  revision {self._quote_string(doc.version)} {{}}")

        lines.append("")
        # imports, includes
        for imp in doc.metadata.get("yang_imports", []):
            lines.append(f"  import {self._quote_name(imp)} {{")
            lines.append("    prefix imp;")
            lines.append("  }")
        for inc in doc.metadata.get("yang_includes", []):
            lines.append(f"  include {self._quote_string(inc)};")
        # features, identities, extensions
        for feat in doc.metadata.get("yang_features", []):
            lines.append(f"  feature {self._quote_name(feat)};")
        for ident in doc.metadata.get("yang_identities", []):
            lines.append(f"  identity {self._quote_name(ident)} {{}}")
        for ext in doc.metadata.get("yang_extensions", []):
            lines.append(f"  extension {self._quote_name(ext)} {{}}")
        lines.append("")

        # Type definitions (typedefs, groupings, containers, lists, choices)
        if doc.type_definitions:
            for entity in doc.type_definitions.entities:
                self._write_entity_definition(entity, lines, indent=2)

        # Top‑level data nodes (from doc.root_entity attributes)
        if doc.root_entity:
            for attr in doc.root_entity.attributes:
                self._write_attribute_as_node(attr, lines, indent=2, parent_entity=doc.root_entity, is_top_level=True)

        # Augments (must be written after all definitions)
        self._write_augments(doc, lines, indent=2)

        # RPCs and notifications
        for op in doc.operations:
            if op.type == OperationType.REQUEST_RESPONSE:
                self._write_rpc(op, lines, indent=2)
            elif op.type == OperationType.NOTIFICATION:
                self._write_notification(op, lines, indent=2)

        lines.append("}")
        yang = "\n".join(lines) + "\n"
        return yang.encode(getattr(self.options, "encoding", "utf-8") or "utf-8")

    # ------------------------------------------------------------------
    # Entity definition writer (typedef, grouping, container, list, choice)
    # ------------------------------------------------------------------
    def _write_entity_definition(self, entity: Entity, lines: list[str], indent: int) -> None:
        """Write a top‑level YANG entity (not part of the root tree)."""
        # Skip if this entity is an augment block – augments are written separately
        if any(a.key == "__augment_target_path" for a in entity.annotations):
            return

        if entity.is_template:
            self._write_grouping(entity, lines, indent)
        elif entity.composition and entity.composition.composition_type == CompositionType.ONE_OF:
            self._write_choice(entity, lines, indent)
        elif len(entity.attributes) == 1 and entity.attributes[0].name == "value":
            self._write_typedef(entity, lines, indent)
        # otherwise skip (containers are written inline)

    def _write_typedef(self, entity: Entity, lines: list[str], indent: int) -> None:
        prefix = "  " * indent
        lines.append(f"{prefix}typedef {self._quote_name(entity.name)} {{")
        if entity.description:
            lines.append(f"{prefix}  description {self._quote_string(entity.description)};")
        attr = next((a for a in entity.attributes if a.name == "value"), None)
        if attr:
            self._write_type(attr, lines, indent + 1)
            if attr.default_value:
                lines.append(f"{prefix}  default {self._quote_string(attr.default_value)};")
        lines.append(f"{prefix}}}")

    def _write_grouping(self, entity: Entity, lines: list[str], indent: int) -> None:
        prefix = "  " * indent
        lines.append(f"{prefix}grouping {self._quote_name(entity.name)} {{")
        if entity.description:
            lines.append(f"{prefix}  description {self._quote_string(entity.description)};")
        for attr in entity.attributes:
            self._write_attribute_as_node(attr, lines, indent + 1, parent_entity=entity, is_top_level=False)
        lines.append(f"{prefix}}}")

    def _write_choice(self, entity: Entity, lines: list[str], indent: int) -> None:
        prefix = "  " * indent
        lines.append(f"{prefix}choice {self._quote_name(entity.name)} {{")
        if entity.description:
            lines.append(f"{prefix}  description {self._quote_string(entity.description)};")
        if entity.composition:
            for case_entity in entity.composition.members:
                lines.append(f"{prefix}  case {self._quote_name(case_entity.name)} {{")
                if case_entity.description:
                    lines.append(f"{prefix}    description {self._quote_string(case_entity.description)};")
                for attr in case_entity.attributes:
                    self._write_attribute_as_node(attr, lines, indent + 2, parent_entity=case_entity, is_top_level=False)
                lines.append(f"{prefix}  }}")
        lines.append(f"{prefix}}}")

    # ------------------------------------------------------------------
    # Attribute / node writer (used inline inside containers, lists, etc.)
    # ------------------------------------------------------------------
    def _write_attribute_as_node(self, attr: Attribute, lines: list[str], indent: int, parent_entity: Entity, is_top_level: bool) -> None:
        prefix = "  " * indent
        dt = attr.data_type
        # 1) uses (template reference)
        if attr.template:
            lines.append(f"{prefix}uses {self._quote_name(attr.template.name)};")
            return
        # 2) anydata / anyxml
        if dt.base == ScalarType.YANG_ANYDATA:
            lines.append(f"{prefix}anydata {self._quote_name(attr.name)};")
            return
        # 3) list (attribute of ARRAY of REF to entry entity)
        if dt.base == ScalarType.ARRAY and dt.element_type and dt.element_type.base == ScalarType.REF:
            entry_entity = dt.element_type.ref_entity
            if entry_entity:
                self._write_list(attr.name, entry_entity, lines, indent)
                return
        # 4) container (attribute of REF to a nested entity)
        if dt.base == ScalarType.REF and dt.ref_entity:
            container_entity = dt.ref_entity
            if container_entity:
                self._write_container(attr.name, container_entity, lines, indent)
                return
        # 5) leaf or leaf-list
        is_leaf_list = (dt.base == ScalarType.ARRAY and dt.element_type and
                        dt.element_type.base not in (ScalarType.REF, ScalarType.STRUCT, ScalarType.ARRAY, ScalarType.MAP))
        if is_leaf_list:
            keyword = "leaf-list"
            elem_type = dt.element_type
        else:
            keyword = "leaf"
            elem_type = dt
        lines.append(f"{prefix}{keyword} {self._quote_name(attr.name)} {{")
        if attr.description:
            lines.append(f"{prefix}  description {self._quote_string(attr.description)};")
        self._write_type(attr, lines, indent + 1, type_dt=elem_type)
        if attr.default_value:
            lines.append(f"{prefix}  default {self._quote_string(attr.default_value)};")
        if attr.required:
            lines.append(f"{prefix}  mandatory true;")
        # must / when constraints
        for c in attr.constraints:
            if c.expression:
                if c.type == ConstraintType.MUST:
                    lines.append(f"{prefix}  must {self._quote_string(c.expression)};")
                elif c.type == ConstraintType.WHEN:
                    lines.append(f"{prefix}  when {self._quote_string(c.expression)};")
        # config / status
        if attr.is_config is not None:
            lines.append(f"{prefix}  config {str(attr.is_config).lower()};")
        if attr.version_status:
            lines.append(f"{prefix}  status {attr.version_status.value};")
        lines.append(f"{prefix}}}")

    def _write_container(self, name: str, container_entity: Entity, lines: list[str], indent: int) -> None:
        prefix = "  " * indent
        lines.append(f"{prefix}container {self._quote_name(name)} {{")
        if container_entity.description:
            lines.append(f"{prefix}  description {self._quote_string(container_entity.description)};")
        for attr in container_entity.attributes:
            self._write_attribute_as_node(attr, lines, indent + 1, parent_entity=container_entity, is_top_level=False)
        lines.append(f"{prefix}}}")

    def _write_list(self, name: str, entry_entity: Entity, lines: list[str], indent: int) -> None:
        prefix = "  " * indent
        lines.append(f"{prefix}list {self._quote_name(name)} {{")
        if entry_entity.description:
            lines.append(f"{prefix}  description {self._quote_string(entry_entity.description)};")
        if entry_entity.list_key:
            lines.append(f"{prefix}  key \"{entry_entity.list_key}\";")
        for attr in entry_entity.attributes:
            self._write_attribute_as_node(attr, lines, indent + 1, parent_entity=entry_entity, is_top_level=False)
        lines.append(f"{prefix}}}")

    def _write_type(self, attr: Attribute, lines: list[str], indent: int, type_dt: DataType | None = None) -> None:
        prefix = "  " * indent
        dt = type_dt if type_dt is not None else attr.data_type
        base_map = {
            ScalarType.STRING: "string",
            ScalarType.INT: "int32",
            ScalarType.LONG: "int64",
            ScalarType.DECIMAL: "decimal64",
            ScalarType.BOOLEAN: "boolean",
            ScalarType.BINARY: "binary",
            ScalarType.YANG_ANYDATA: "anydata",
            ScalarType.REF: "leafref",
        }
        base_name = base_map.get(dt.base, "string")
        lines.append(f"{prefix}type {base_name} {{")
        for c in attr.constraints:
            if c.expression:
                if c.type == ConstraintType.PATTERN:
                    lines.append(f"{prefix}  pattern {self._quote_string(c.expression)};")
                elif c.type == ConstraintType.LENGTH:
                    lines.append(f"{prefix}  length {self._quote_string(c.expression)};")
                elif c.type == ConstraintType.RANGE:
                    lines.append(f"{prefix}  range {self._quote_string(c.expression)};")
                elif c.type == ConstraintType.ENUMERATION:
                    lines.append(f"{prefix}  enum {self._quote_name(c.expression)};")
        lines.append(f"{prefix}}}")

    # ------------------------------------------------------------------
    # Augments (written from entities that have "__augment_target_path" annotation)
    # ------------------------------------------------------------------
    def _write_augments(self, doc: SSDMDocument, lines: list[str], indent: int) -> None:
        if not doc.type_definitions:
            return
        for entity in doc.type_definitions.entities:
            target_path = next((a.value for a in entity.annotations if a.key == "__augment_target_path"), None)
            if target_path:
                self._write_augment(target_path, entity, lines, indent)

    def _write_augment(self, target_path: str, augment_entity: Entity, lines: list[str], indent: int) -> None:
        prefix = "  " * indent
        lines.append(f"{prefix}augment {self._quote_string(target_path)} {{")
        for attr in augment_entity.attributes:
            self._write_attribute_as_node(attr, lines, indent + 1, parent_entity=augment_entity, is_top_level=False)
        lines.append(f"{prefix}}}")

    # ------------------------------------------------------------------
    # RPC / notification writers
    # ------------------------------------------------------------------
    def _write_rpc(self, op: ServiceOperation, lines: list[str], indent: int) -> None:
        prefix = "  " * indent
        lines.append(f"{prefix}rpc {self._quote_name(op.name)} {{")
        if op.description:
            lines.append(f"{prefix}  description {self._quote_string(op.description)};")
        if op.yang:
            if op.yang.must:
                lines.append(f"{prefix}  must {self._quote_string(op.yang.must)};")
            if op.yang.when:
                lines.append(f"{prefix}  when {self._quote_string(op.yang.when)};")
            if op.yang.config is not None:
                lines.append(f"{prefix}  config {str(op.yang.config).lower()};")
            if op.yang.status:
                lines.append(f"{prefix}  status {op.yang.status};")
            if op.yang.deviation:
                lines.append(f"{prefix}  deviation {self._quote_string(op.yang.deviation)} {{}}")
        if op.request_body and op.request_body.content_entity:
            self._write_rpc_io("input", op.request_body.content_entity, lines, indent + 1)
        if op.responses and op.responses[0].content_entity:
            self._write_rpc_io("output", op.responses[0].content_entity, lines, indent + 1)
        lines.append(f"{prefix}}}")

    def _write_rpc_io(self, direction: str, entity: Entity, lines: list[str], indent: int) -> None:
        prefix = "  " * indent
        lines.append(f"{prefix}{direction} {{")
        for attr in entity.attributes:
            self._write_attribute_as_node(attr, lines, indent + 1, parent_entity=entity, is_top_level=False)
        lines.append(f"{prefix}}}")

    def _write_notification(self, op: ServiceOperation, lines: list[str], indent: int) -> None:
        prefix = "  " * indent
        lines.append(f"{prefix}notification {self._quote_name(op.name)} {{")
        if op.description:
            lines.append(f"{prefix}  description {self._quote_string(op.description)};")
        if op.yang:
            if op.yang.must:
                lines.append(f"{prefix}  must {self._quote_string(op.yang.must)};")
            if op.yang.when:
                lines.append(f"{prefix}  when {self._quote_string(op.yang.when)};")
        # Removed `op.extensions` access – not available in the model
        lines.append(f"{prefix}}}")

    # ------------------------------------------------------------------
    # String helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _quote_name(name: str) -> str:
        if name.startswith('"') and name.endswith('"'):
            return name
        return f'"{name}"'

    @staticmethod
    def _quote_string(s: str) -> str:
        if s is None:
            return '""'
        escaped = s.replace('\\', '\\\\').replace('"', '\\"')
        return f'"{escaped}"'
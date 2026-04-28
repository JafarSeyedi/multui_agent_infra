# engines/document/writers/msdm_writers/plantuml_writer.py
"""
PlantUML Writer – converts an MSDMDocument into a PlantUML class diagram (.puml).
Outputs class definitions, attributes, methods, and relationships with full
round‑trip fidelity.  Raw relation lines stored by the parser take precedence;
otherwise relationships are generated from the model.  Soft‑delete is ignored.
"""

from __future__ import annotations
import re
from typing import Optional, Dict, Any, List, Tuple

from .base_msdm_writer import BaseMSDMWriter, WriteTarget, SoftDeleteStrategy
from engines.document.writers.base import WriteOptions
from engines.document.models.msdm_models import (
    MSDMDocument,
    Entity,
    Attribute,
    DataType,
    ScalarType,
    Relationship,
    Cardinality,
    Constraint,
    ConstraintType,
    Annotation,
    EntityKind,
)


class PlantUMLWriter(BaseMSDMWriter):
    """Writer for PlantUML diagram files (.plantuml, .puml, .pu)."""
    name = "plantuml"
    supported_extensions = (".plantuml", ".puml", ".pu")

    def __init__(
        self,
        options: Optional[WriteOptions] = None,
        target_mode: WriteTarget = WriteTarget.DESIGN_FILE,
        soft_delete_strategy: SoftDeleteStrategy = SoftDeleteStrategy.NONE,
    ):
        super().__init__(options, target_mode, soft_delete_strategy)

    # ── Public API ─────────────────────────────────────────────────
    async def _write_design(self, document: MSDMDocument) -> bytes:
        lines = []

        # Optional package
        if document.namespace:
            lines.append(f"package {document.namespace}")
            lines.append("")

        # Entities → class/interface/enum blocks
        for entity in document.entities:
            block = self._entity_to_block(entity)
            if block:
                lines.append(block)
                lines.append("")

        # Relationships: prefer raw lines from parser for true round‑trip
        raw_rels = [a.value for a in document.annotations if a.key == "raw_relation"]
        if raw_rels:
            lines.extend(raw_rels)
        else:
            # Generate from inheritance and Relationship objects
            lines.extend(self._generate_relationship_lines(document))

        # Append any raw lines stored as annotations (e.g., notes, skinparams)
        for ann in document.annotations:
            if ann.key == "raw_line":
                lines.append(ann.value)

        puml = "\n".join(lines)
        return puml.encode(self.options.encoding or "utf-8")

    async def get_supported_media_types(self) -> list[str]:
        return ["text/plain"]

    async def get_supported_extensions(self) -> list[str]:
        return self.supported_extensions

    # ── Entity → class block ───────────────────────────────────────
    def _entity_to_block(self, entity: Entity) -> str:
        stereotype = self._get_annotation(entity, "stereotype") or ""
        abstract = self._get_annotation(entity, "abstract") == "true"
        is_interface = self._get_annotation(entity, "interface") == "true"

        # Determine block type
        if is_interface:
            block_type = "interface"
        elif stereotype.lower() == "enum":
            block_type = "enum"
        elif stereotype.lower() == "entity":
            block_type = "entity"
        else:
            block_type = "class"

        # Header line
        header = f"{'abstract ' if abstract else ''}{'class' if block_type == 'class' else block_type} {entity.name}"
        if stereotype and stereotype.lower() not in ("class", "interface", "enum", "entity"):
            header += f" <<{stereotype}>>"
        if entity.description:
            lines = [f"' {entity.description}", header + " {"]
        else:
            lines = [header + " {"]

        # Attributes and methods
        for attr in entity.attributes:
            if self._is_method(attr):
                lines.append("    " + self._method_to_plantuml(attr))
            else:
                lines.append("    " + self._field_to_plantuml(attr))

        # Additional body lines
        for ann in entity.annotations:
            if ann.key == "body_line":
                lines.append("    " + ann.value)

        lines.append("}")
        return "\n".join(lines)

    # ── Field formatting ───────────────────────────────────────────
    def _field_to_plantuml(self, attr: Attribute) -> str:
        visibility = self._get_annotation(attr, "visibility") or ""
        modifiers = []
        for ann in attr.annotations:
            if ann.key == "modifier" and ann.value in ("static", "abstract", "readonly"):
                modifiers.append(ann.value)

        modifier_str = " ".join(modifiers) + " " if modifiers else ""
        type_str = self._datatype_to_string(attr.data_type)
        name = attr.name
        # If name starts with "/" (e.g., "/name"), it's a derived property? Not in PlantUML, but we'll preserve.
        return f"{visibility}{modifier_str}{name} : {type_str}"

    # ── Method formatting ──────────────────────────────────────────
    def _method_to_plantuml(self, attr: Attribute) -> str:
        # Recover operation name and parameters from the stored pseudo-name
        op_name = self._get_annotation(attr, "operation_name") or attr.name
        params_str = ""
        # The parser stored the method name with params in the attribute name: "methodName(param1:type1, param2:type2)"
        # So we can extract
        m = re.match(r"(\w+)\(([^)]*)\)", attr.name)
        if m:
            op_name = m.group(1)
            params_str = m.group(2) if m.group(2) else ""

        visibility = self._get_annotation(attr, "visibility") or ""
        modifiers = []
        for ann in attr.annotations:
            if ann.key == "modifier" and ann.value in ("static", "abstract"):
                modifiers.append(ann.value)
        modifier_str = " ".join(modifiers) + " " if modifiers else ""

        return_type = self._datatype_to_string(attr.data_type)

        # If return type is void/any, we omit the colon? Keep as is for round-trip.
        if return_type and return_type != "void":
            return f"{visibility}{modifier_str}{op_name}({params_str}) : {return_type}"
        else:
            return f"{visibility}{modifier_str}{op_name}({params_str})"

    # ── Relationship generation ────────────────────────────────────
    def _generate_relationship_lines(self, document: MSDMDocument) -> List[str]:
        lines = []
        entity_names = {e.name for e in document.entities}

        # Inheritance
        for entity in document.entities:
            if entity.extends and entity.extends in entity_names:
                # PlantUML: Child --|> Parent
                lines.append(f"{entity.name} --|> {entity.extends}")

        # Explicit Relationships
        for rel in document.relationships:
            if rel.from_entity not in entity_names or rel.to_entity not in entity_names:
                continue
            arrow = self._cardinality_to_arrow(rel.cardinality_from, rel.cardinality_to)
            line = f"{rel.from_entity} {arrow} {rel.to_entity}"
            if rel.name:
                line += f" : {rel.name}"
            lines.append(line)

        return lines

    def _cardinality_to_arrow(self, from_card: Cardinality, to_card: Cardinality) -> str:
        # PlantUML syntax: e.g., "1" -- "*", "1" -- "0..1"
        # We can use the cardinality strings on the ends and "--" as connector.
        # Better: use the multiplicity on each end.
        from_str = self._card_str(from_card)
        to_str = self._card_str(to_card)
        if from_str == "1" and to_str == "1":
            return "--"
        return f'"{from_str}" -- "{to_str}"'

    @staticmethod
    def _card_str(card: Cardinality) -> str:
        mapping = {
            Cardinality.ONE: "1",
            Cardinality.MANY: "*",
            Cardinality.ZERO_OR_ONE: "0..1",
            Cardinality.ONE_OR_MANY: "1..*",
        }
        return mapping.get(card, "1")

    # ── DataType to PlantUML type string ───────────────────────────
    def _datatype_to_string(self, dt: DataType) -> str:
        base = dt.base
        if base == ScalarType.ARRAY:
            inner = self._datatype_to_string(dt.element_type) if dt.element_type else "Object"
            return f"List<{inner}>"
        if base == ScalarType.MAP:
            key = self._datatype_to_string(dt.key_type) if dt.key_type else "String"
            val = self._datatype_to_string(dt.value_type) if dt.value_type else "Object"
            return f"Map<{key},{val}>"
        if base == ScalarType.REF:
            return dt.ref_entity or "Object"
        if base == ScalarType.STRUCT:
            return "Object"
        # Scalars
        mapping = {
            ScalarType.STRING: "String",
            ScalarType.INT: "Integer",
            ScalarType.LONG: "Long",
            ScalarType.FLOAT: "Float",
            ScalarType.DOUBLE: "Double",
            ScalarType.BOOLEAN: "Boolean",
            ScalarType.DATE: "Date",
            ScalarType.TIME: "Time",
            ScalarType.TIMESTAMP: "DateTime",
            ScalarType.UUID: "UUID",
            ScalarType.BINARY: "Byte[]",
            ScalarType.DECIMAL: "Decimal",
            ScalarType.ANY: "Object",
        }
        return mapping.get(base, "Object")

    # ── Helpers ────────────────────────────────────────────────────
    def _get_annotation(self, obj, key: str) -> Optional[str]:
        if isinstance(obj, Entity):
            return next((a.value for a in obj.annotations if a.key == key), None)
        if isinstance(obj, Attribute):
            return next((a.value for a in obj.annotations if a.key == key), None)
        return None

    def _is_method(self, attr: Attribute) -> bool:
        return any(a.key == "method" and a.value == "true" for a in attr.annotations)
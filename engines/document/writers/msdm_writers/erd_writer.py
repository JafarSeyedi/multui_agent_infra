# engines/document/writers/msdm_writers/erd_writer.py
"""
ERD (Entity‑Relationship Diagram) Writer – converts an MSDMDocument into
a JSON (default) or XML representation of entities and relationships.
Soft‑delete is ignored – the writer produces a clean schema snapshot.
"""

from __future__ import annotations
import json
from typing import Optional, Dict, Any, List

from .base_msdm_writer import BaseMSDMWriter, WriteTarget, SoftDeleteStrategy
from engines.document.writers.base import WriteOptions
from engines.document.models.msdm_models import (
    MSDMDocument,
    Entity,
    Attribute,
    DataType,
    Constraint,
    ConstraintType,
    Relationship,
    Cardinality,
)


class ERDWriter(BaseMSDMWriter):
    """Writer for Entity‑Relationship Diagram files (JSON or XML)."""
    name = "erd"
    supported_extensions = (".erd", ".json", ".xml")

    def __init__(
        self,
        options: Optional[WriteOptions] = None,
        target_mode: WriteTarget = WriteTarget.DESIGN_FILE,
        soft_delete_strategy: SoftDeleteStrategy = SoftDeleteStrategy.NONE,
        output_format: str = "json",   # "json" or "xml"
    ):
        super().__init__(options, target_mode, soft_delete_strategy)
        self.output_format = output_format.lower()

    # ── Public API ─────────────────────────────────────────────────
    async def _write_design(self, document: MSDMDocument) -> bytes:
        if self.output_format == "xml":
            data = self._build_xml(document)
            return data.encode(self.options.encoding or "utf-8")
        else:
            data = self._build_json(document)
            return json.dumps(data, indent=2, ensure_ascii=False).encode(self.options.encoding or "utf-8")

    async def get_supported_media_types(self) -> list[str]:
        return ["application/json", "application/xml"]

    async def get_supported_extensions(self) -> list[str]:
        return self.supported_extensions

    # ── JSON representation ────────────────────────────────────────
    def _build_json(self, doc: MSDMDocument) -> dict:
        result = {}
        if doc.namespace:
            result["namespace"] = doc.namespace
        result["entities"] = [self._entity_to_json(e) for e in doc.entities]
        result["relationships"] = [self._relationship_to_json(r) for r in doc.relationships]
        return result

    def _entity_to_json(self, entity: Entity) -> dict:
        obj = {"name": entity.name}
        if entity.description:
            obj["description"] = entity.description
        obj["attributes"] = []
        for attr in entity.attributes:
            attr_obj = self._attribute_to_json(attr)
            obj["attributes"].append(attr_obj)
        # Primary key constraint
        pk_constraint = next((c for c in entity.constraints if c.type == ConstraintType.PRIMARY_KEY), None)
        if pk_constraint and pk_constraint.expression:
            obj["primaryKey"] = [k.strip() for k in pk_constraint.expression.split(",")]
        # Foreign keys are already on attributes
        return obj

    def _attribute_to_json(self, attr: Attribute) -> dict:
        obj = {
            "name": attr.name,
            "type": self._datatype_to_string(attr.data_type),
            "required": attr.required,
            "primaryKey": attr.primary_key,
        }
        if attr.description:
            obj["description"] = attr.description
        if attr.default_value is not None:
            obj["default"] = attr.default_value
        # Foreign key
        fk = next((c for c in attr.constraints if c.type == ConstraintType.FOREIGN_KEY), None)
        if fk:
            fk_obj = {"entity": fk.referenced_entity}
            if fk.referenced_attributes:
                fk_obj["attribute"] = fk.referenced_attributes[0]
            obj["foreignKey"] = fk_obj
        return obj

    def _relationship_to_json(self, rel: Relationship) -> dict:
        obj = {
            "from": rel.from_entity,
            "to": rel.to_entity,
            "cardinality": f"{self._cardinality_to_str(rel.cardinality_from)}:{self._cardinality_to_str(rel.cardinality_to)}",
        }
        if rel.name:
            obj["name"] = rel.name
        if rel.description:
            obj["description"] = rel.description
        if rel.foreign_key_attributes:
            obj["foreignKeyAttributes"] = rel.foreign_key_attributes
        return obj

    # ── XML representation (simple) ────────────────────────────────
    def _build_xml(self, doc: MSDMDocument) -> str:
        from xml.etree.ElementTree import Element, SubElement, tostring
        root = Element("EntityRelationship")
        entities_elem = SubElement(root, "Entities")
        for entity in doc.entities:
            self._entity_to_xml(entity, entities_elem)
        rels_elem = SubElement(root, "Relationships")
        for rel in doc.relationships:
            self._relationship_to_xml(rel, rels_elem)
        return tostring(root, encoding="unicode", method="xml")

    def _entity_to_xml(self, entity: Entity, parent: Element) -> None:
        ent_elem = Element("Entity", {"name": entity.name})
        if entity.description:
            ent_elem.set("description", entity.description)
        for attr in entity.attributes:
            attr_elem = Element("Attribute", {
                "name": attr.name,
                "type": self._datatype_to_string(attr.data_type),
                "required": str(attr.required).lower(),
                "primaryKey": str(attr.primary_key).lower(),
            })
            if attr.description:
                attr_elem.set("description", attr.description)
            if attr.default_value:
                attr_elem.set("default", attr.default_value)
            fk = next((c for c in attr.constraints if c.type == ConstraintType.FOREIGN_KEY), None)
            if fk:
                fk_elem = SubElement(attr_elem, "ForeignKey", {
                    "entity": fk.referenced_entity or "",
                })
                if fk.referenced_attributes:
                    fk_elem.set("attribute", fk.referenced_attributes[0])
            ent_elem.append(attr_elem)
        parent.append(ent_elem)

    def _relationship_to_xml(self, rel: Relationship, parent: Element) -> None:
        rel_elem = Element("Relationship", {
            "from": rel.from_entity,
            "to": rel.to_entity,
            "cardinality": f"{self._cardinality_to_str(rel.cardinality_from)}:{self._cardinality_to_str(rel.cardinality_to)}",
        })
        if rel.name:
            rel_elem.set("name", rel.name)
        if rel.description:
            rel_elem.set("description", rel.description)
        if rel.foreign_key_attributes:
            fk_elem = SubElement(rel_elem, "ForeignKeyAttributes")
            fk_elem.text = ",".join(rel.foreign_key_attributes)
        parent.append(rel_elem)

    # ── Helper ──────────────────────────────────────────────────────
    @staticmethod
    def _datatype_to_string(dt: DataType) -> str:
        """Convert DataType to a simple string for representation."""
        base = dt.base
        if base == ScalarType.ARRAY:
            inner = ERDWriter._datatype_to_string(dt.element_type) if dt.element_type else "any"
            return f"array<{inner}>"
        if base == ScalarType.MAP:
            key = ERDWriter._datatype_to_string(dt.key_type) if dt.key_type else "string"
            val = ERDWriter._datatype_to_string(dt.value_type) if dt.value_type else "any"
            return f"map<{key},{val}>"
        if base == ScalarType.REF:
            return dt.ref_entity or "ref"
        if base == ScalarType.STRUCT:
            return "object"
        # map scalars to simple names
        scalar_names = {
            ScalarType.STRING: "string",
            ScalarType.INT: "int",
            ScalarType.LONG: "long",
            ScalarType.FLOAT: "float",
            ScalarType.DOUBLE: "double",
            ScalarType.BOOLEAN: "boolean",
            ScalarType.DATE: "date",
            ScalarType.TIME: "time",
            ScalarType.TIMESTAMP: "timestamp",
            ScalarType.DECIMAL: "decimal",
            ScalarType.UUID: "uuid",
            ScalarType.BINARY: "binary",
            ScalarType.ANY: "any",
        }
        return scalar_names.get(base, "any")

    @staticmethod
    def _cardinality_to_str(card: Cardinality) -> str:
        """Convert Cardinality enum to string representation."""
        mapping = {
            Cardinality.ONE: "1",
            Cardinality.MANY: "*",
            Cardinality.ZERO_OR_ONE: "0..1",
            Cardinality.ONE_OR_MANY: "1..*",
        }
        return mapping.get(card, "1")
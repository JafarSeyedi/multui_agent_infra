# engines/document/writers/msdm_writers/erd_writer.py
"""
ERD (Entity‑EntityRelationship Diagram) Writer – converts an MSDMDocument into
a JSON (default) or XML representation of entities and relationships.
Soft‑delete is ignored – the writer produces a clean schema snapshot.
"""
from __future__ import annotations

import json
from typing import Any, Dict, List, Union
from xml.etree.ElementTree import Element, SubElement, tostring

from ...models.msdm_models import Attribute
from ...models.msdm_models import Cardinality
from ...models.msdm_models import ConstraintType
from ...models.msdm_models import DataType
from ...models.msdm_models import Entity
from ...models.msdm_models import MSDMDocument
from ...models.msdm_models import EntityRelationship, ScalarType
from ..base import WriteOptions
from .base_msdm_writer import BaseMSDMWriter
from .base_msdm_writer import SoftDeleteStrategy
from .base_msdm_writer import WriteTarget


class ERDWriter(BaseMSDMWriter):
    """Writer for Entity‑Relationship Diagram files (JSON or XML)."""
    name = "erd"
    supported_extensions = (".erd", ".json", ".xml")

    def __init__(
        self,
        options: WriteOptions | None = None,
        target_mode: WriteTarget = WriteTarget.DESIGN_FILE,
        soft_delete_strategy: SoftDeleteStrategy = SoftDeleteStrategy.NONE,
        output_format: str = "json",   # "json" or "xml"
    ):
        super().__init__(options, target_mode, soft_delete_strategy)
        self.output_format = output_format.lower()

    # ── Public API ─────────────────────────────────────────────────
    async def _write_design(self, document: MSDMDocument) -> bytes:
        if self.output_format == "xml":
            x_data = self._build_xml(document)
            return x_data.encode(getattr(self.options, "encoding", "utf-8") or "utf-8")
        else:
            j_data = self._build_json(document)
            return json.dumps(j_data, indent=2, ensure_ascii=False).encode(
                getattr(self.options, "encoding", "utf-8") or "utf-8"
            )

    def get_supported_media_types(self) -> list[str]:
        return ["application/json", "application/xml"]

    def get_supported_extensions(self) -> list[str]:
        return list(self.supported_extensions)

    # ── JSON representation ────────────────────────────────────────
    def _build_json(self, doc: MSDMDocument) -> dict[str, Any]:
        result: dict[str, Any] = {}
        if doc.namespace:
            result["namespace"] = doc.namespace
        entities: list[dict] = []
        for e in doc.entities:
            entities.append(self._entity_to_json(e))
        result["entities"] = entities
        relationships: list[dict] = []
        for r in doc.relationships:
            relationships.append(self._relationship_to_json(r))
        result["relationships"] = relationships
        return result

    def _entity_to_json(self, entity: Entity) -> dict[str, Any]:
        obj: dict[str, Any] = {"name": entity.name}
        if entity.description:
            obj["description"] = entity.description
        attributes: list[dict] = []
        for attr in entity.attributes:
            attributes.append(self._attribute_to_json(attr))
        obj["attributes"] = attributes
        # Primary key constraint
        pk_constraint = next((c for c in entity.constraints if c.type == ConstraintType.PRIMARY_KEY), None)
        if pk_constraint and pk_constraint.expression:
            obj["primaryKey"] = [k.strip() for k in pk_constraint.expression.split(",")]
        return obj

    def _attribute_to_json(self, attr: Attribute) -> dict[str, Any]:
        primary_key = any(c.type == ConstraintType.PRIMARY_KEY for c in attr.constraints)
        obj: dict[str, Any] = {
            "name": attr.name,
            "type": self._datatype_to_string(attr.data_type),
            "required": attr.required,
            "primaryKey": primary_key,
        }
        if attr.description:
            obj["description"] = attr.description
        if attr.default_value is not None:
            obj["default"] = attr.default_value
        # Foreign key
        fk = next((c for c in attr.constraints if c.type == ConstraintType.FOREIGN_KEY), None)
        if fk and fk.ref_entity:
            fk_obj: dict[str, Any] = {"entity": fk.ref_entity.name}
            if fk.ref_attr_ids and len(fk.ref_attr_ids)>0:
                fk_obj["attribute"] = fk.ref_attr_ids[0]
            obj["foreignKey"] = fk_obj
        return obj

    def _relationship_to_json(self, rel: EntityRelationship) -> dict[str, Any]:
        obj: dict[str, Any] = {
            "cardinality": f"{self._cardinality_to_str(rel.cardinality_from)}:{self._cardinality_to_str(rel.cardinality_to)}",
        }
        if rel.from_entity:
            obj["from"] = rel.from_entity.name
        if rel.to_entity:
            obj["to"] = rel.to_entity.name
        if rel.name:
            obj["name"] = rel.name
        if rel.description:
            obj["description"] = rel.description
        if rel.foreign_key_attributes:
            obj["foreignKeyAttributes"] = rel.foreign_key_attributes
        return obj

    # ── XML representation ────────────────────────────────────────
    def _build_xml(self, doc: MSDMDocument) -> str:
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
            primary_key = any(c.type == ConstraintType.PRIMARY_KEY for c in attr.constraints)
            attr_elem = Element("Attribute", {
                "name": attr.name,
                "type": self._datatype_to_string(attr.data_type),
                "required": str(attr.required).lower(),
                "primaryKey": str(primary_key).lower(),
            })
            if attr.description:
                attr_elem.set("description", attr.description)
            if attr.default_value:
                attr_elem.set("default", attr.default_value)
            fk = next((c for c in attr.constraints if c.type == ConstraintType.FOREIGN_KEY), None)
            if fk and fk.ref_entity:
                fk_elem = SubElement(attr_elem, "ForeignKey", {
                    "entity": fk.ref_entity.name or "",
                })
                if fk.ref_attr_ids and len(fk.ref_attr_ids)>0:
                    fk_elem.set("attribute", fk.ref_attr_ids[0])
            ent_elem.append(attr_elem)
        parent.append(ent_elem)

    def _relationship_to_xml(self, rel: EntityRelationship, parent: Element) -> None:
        relation = {
            "cardinality": f"{self._cardinality_to_str(rel.cardinality_from)}:{self._cardinality_to_str(rel.cardinality_to)}",
        }
        rel_elem = Element("Relationship", relation)
        if rel.from_entity:    
            relation["from"] = rel.from_entity.name
        if rel.to_entity:    
            relation["to"] = rel.to_entity.name
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
        if base == ScalarType.REF and dt.ref_entity:
            return dt.ref_entity.name or "ref"
        if base == ScalarType.STRUCT:
            return "object"
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
        mapping = {
            Cardinality.ONE: "1",
            Cardinality.MANY: "*",
            Cardinality.ZERO_OR_ONE: "0..1",
            Cardinality.ONE_OR_MANY: "1..*",
        }
        return mapping.get(card, "1")
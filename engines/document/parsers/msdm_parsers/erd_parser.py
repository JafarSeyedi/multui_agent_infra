# engines/document/parsers/msdm_parsers/erd_parser.py
"""
Entity‑Relationship Diagram (ERD) Parser – converts .erd files (XML or JSON)
into an MSDMDocument.

Handles both common ERD representations:
- XML (<EntityRelationship> with <Entities> and <Relationships>)
- JSON (object with 'entities' and 'relationships' arrays)

Preserves all attributes, primary/foreign keys, cardinalities, and metadata
via dedicated MSDM fields and structured annotations for round‑trip fidelity.
"""
from __future__ import annotations

import json
from pathlib import Path
from xml.etree import ElementTree as ET

from ...models.media_types import MEDIA_TYPES
from ...models.msdm_models import Annotation
from ...models.msdm_models import Attribute
from ...models.msdm_models import Cardinality
from ...models.msdm_models import Constraint
from ...models.msdm_models import ConstraintType
from ...models.msdm_models import DataType
from ...models.msdm_models import Entity
from ...models.msdm_models import EntityKind
from ...models.msdm_models import MSDMDocument
from ...models.msdm_models import EntityRelationship
from ...models.msdm_models import ScalarType, Namespace
from ..base import ParseOptions
from .base_msdm_parser import BaseMSDMParser


class ERDParser(BaseMSDMParser):
    """Parser for Entity‑Relationship Diagram files (.erd, .xml, .json)."""
    name = "erd"
    supported_extensions = (".erd", ".xml", ".json")

    async def _parse_to_msdm(
        self, data: bytes, source_name: str, options: ParseOptions
    ) -> MSDMDocument:
        encoding = options.encoding or "utf-8"
        text = data.decode(encoding)
        doc = MSDMDocument(
            document_id=Path(source_name).stem,
            title=Path(source_name).stem,
            media_type=MEDIA_TYPES.get("erd", MEDIA_TYPES["json"])
        )
        doc.namespace = Namespace(uri=Path(source_name).stem)

        # Determine format by attempting JSON first, then XML
        parsed = False
        try:
            json_data = json.loads(text)
            if isinstance(json_data, dict) and ("entities" in json_data or "relationships" in json_data):
                self._parse_json(json_data, doc)
                parsed = True
        except Exception:
            pass

        if not parsed:
            try:
                root = ET.fromstring(text)
                if root.tag == 'EntityRelationship' or root.find('Entity') is not None:
                    self._parse_xml(root, doc)
                    parsed = True
            except Exception:
                raise ValueError("Could not parse ERD file: not valid JSON or XML")

        self.resolve_references(doc)
        return doc

    # ── JSON parsing ────────────────────────────────────────────
    def _parse_json(self, data: dict, doc: MSDMDocument) -> None:
        entities_list = data.get("entities", [])
        relationships_list = data.get("relationships", [])

        for entity_data in entities_list:
            entity = self._parse_json_entity(entity_data, doc)
            doc.entities.append(entity)

        for rel_data in relationships_list:
            rel = self._parse_json_relationship(rel_data, doc)
            doc.relationships.append(rel)

        # Store any extra top-level properties as document annotations
        for key in data:
            if key not in ("entities", "relationships"):
                doc.annotations.append(Annotation(key=key, value=json.dumps(data[key])))

    def _parse_json_entity(self, data: dict, doc: MSDMDocument) -> Entity:
        name = data["name"]
        desc = data.get("description")
        entity = Entity(
            name=name,
            kind=EntityKind.TABLE,
            description=desc,
        )

        # Attributes
        for attr_data in data.get("attributes", []):
            attr = self._parse_json_attribute(attr_data, entity, doc)
            entity.attributes.append(attr)

        # Additional properties stored as annotations
        for key in data:
            if key not in ("name", "description", "attributes", "primaryKey", "foreignKeys"):
                entity.annotations.append(Annotation(key=key, value=json.dumps(data[key])))

        return entity

    def _parse_json_attribute(self, data: dict, entity: Entity, doc: MSDMDocument) -> Attribute:
        name = data["name"]
        attr_type_str = data.get("type", "string").lower()
        required = data.get("required", False)
        desc = data.get("description")
        primary_key = data.get("primaryKey", False)
        default_val = data.get("default")

        dt = self._map_type_string(attr_type_str, doc)

        attr = Attribute(
            name=name,
            data_type=dt,
            required=required,
            description=desc,
            default_value=str(default_val) if default_val is not None else None,
        )
        if primary_key:
            attr.constraints.append(Constraint(type=ConstraintType.PRIMARY_KEY))
        # Foreign key reference
        fk_data = data.get("foreignKey")
        if fk_data:
            ref_entity_id = fk_data if isinstance(fk_data, str) else fk_data.get("entity")
            ref_attr = fk_data.get("attribute") if isinstance(fk_data, dict) else None
            attr.constraints.append(Constraint(
                type=ConstraintType.FOREIGN_KEY,
                ref_entity_id=ref_entity_id,
                ref_attr_ids=[ref_attr] if ref_attr else [],
            ))

        # Extra attributes stored as annotations
        for key in data:
            if key not in ("name", "type", "required", "description", "primaryKey",
                           "default", "foreignKey"):
                attr.annotations.append(Annotation(key=key, value=json.dumps(data[key])))

        return attr

    def _parse_json_relationship(self, data: dict, doc: MSDMDocument) -> EntityRelationship:
        name = data.get("name")
        from_ref_id = data["from"]
        to_ref_id = data["to"]
        card_str = data.get("cardinality", "1:1")

        card_from, card_to = self._parse_cardinality(card_str)

        return EntityRelationship(
            name=name,
            from_ref_id=from_ref_id,
            to_ref_id=to_ref_id,
            cardinality_from=card_from,
            cardinality_to=card_to,
            foreign_key_attributes=data.get("foreignKeyAttributes", []),
            description=data.get("description"),
        )

    # ── XML parsing ─────────────────────────────────────────────
    def _parse_xml(self, root: ET.Element, doc: MSDMDocument) -> None:
        # Entities
        entities_elem = root.find('Entities') or root.find('entities')
        if entities_elem is not None:
            for entity_elem in entities_elem.findall('Entity'):
                entity = self._parse_xml_entity(entity_elem, doc)
                doc.entities.append(entity)

        # Relationships
        rels_elem = root.find('Relationships') or root.find('relationships')
        if rels_elem is not None:
            for rel_elem in rels_elem.findall('Relationship'):
                rel = self._parse_xml_relationship(rel_elem, doc)
                doc.relationships.append(rel)

    def _parse_xml_entity(self, elem: ET.Element, doc: MSDMDocument) -> Entity:
        name = elem.get('name', '')
        desc = elem.get('description')
        entity = Entity(name=name, kind=EntityKind.TABLE, description=desc)

        for attr_elem in elem.findall('Attribute'):
            attr = self._parse_xml_attribute(attr_elem, doc)
            entity.attributes.append(attr)

        return entity

    def _parse_xml_attribute(self, elem: ET.Element, doc: MSDMDocument) -> Attribute:
        name = elem.get('name', '')
        type_str = elem.get('type', 'string').lower()
        required = elem.get('required', 'false').lower() == 'true'
        primary_key = elem.get('primaryKey', 'false').lower() == 'true'
        desc = elem.get('description')
        default_val = elem.get('default')

        dt = self._map_type_string(type_str, doc)

        attr = Attribute(
            name=name,
            data_type=dt,
            required=required,
            description=desc,
            default_value=default_val,
        )
        if primary_key:
            attr.constraints.append(Constraint(type=ConstraintType.PRIMARY_KEY))

        # Foreign key via child element
        fk_elem = elem.find('ForeignKey')
        if fk_elem is not None:
            ref_entity_id = fk_elem.get('entity', '')
            ref_attr = fk_elem.get('attribute')
            attr.constraints.append(Constraint(
                type=ConstraintType.FOREIGN_KEY,
                ref_entity_id=ref_entity_id,
                ref_attr_ids=[ref_attr] if ref_attr else [],
            ))

        return attr

    def _parse_xml_relationship(self, elem: ET.Element, doc: MSDMDocument) -> EntityRelationship:
        name = elem.get('name')
        from_ref_id = elem.get('from', '')
        to_ref_id = elem.get('to', '')
        card_str = elem.get('cardinality', '1:1')
        card_from, card_to = self._parse_cardinality(card_str)

        fk_attrs = []
        fk_elem = elem.find('ForeignKeyAttributes')
        if fk_elem is not None and fk_elem.text:
            fk_attrs = [a.strip() for a in fk_elem.text.split(',')]

        return EntityRelationship(
            name=name,
            from_ref_id=from_ref_id,
            to_ref_id=to_ref_id,
            cardinality_from=card_from,
            cardinality_to=card_to,
            foreign_key_attributes=fk_attrs,
            description=elem.get('description'),
        )

    # ── Helpers ─────────────────────────────────────────────────
    def _map_type_string(self, type_str: str, doc: MSDMDocument) -> DataType:
        mapping = {
            "string": ScalarType.STRING,
            "text": ScalarType.STRING,
            "varchar": ScalarType.STRING,
            "int": ScalarType.INT,
            "integer": ScalarType.INT,
            "long": ScalarType.LONG,
            "float": ScalarType.FLOAT,
            "double": ScalarType.DOUBLE,
            "decimal": ScalarType.DECIMAL,
            "boolean": ScalarType.BOOLEAN,
            "bool": ScalarType.BOOLEAN,
            "date": ScalarType.DATE,
            "time": ScalarType.TIME,
            "timestamp": ScalarType.TIMESTAMP,
            "datetime": ScalarType.TIMESTAMP,
            "uuid": ScalarType.UUID,
            "binary": ScalarType.BINARY,
            "blob": ScalarType.BINARY,
        }
        if type_str in mapping:
            return DataType(base=mapping[type_str])
        return DataType(base=ScalarType.REF, ref_entity_id=type_str)

    def _parse_cardinality(self, card_str: str) -> tuple[Cardinality, Cardinality]:
        card_str = card_str.replace(' ', '')
        if ':' in card_str:
            parts = card_str.split(':')
            return self._to_card(parts[0]), self._to_card(parts[1])
        if '-' in card_str:
            parts = card_str.split('-')
            if len(parts) == 2:
                return self._to_card(parts[0]), self._to_card(parts[1])
        return Cardinality.ONE, Cardinality.ONE

    def _to_card(self, token: str) -> Cardinality:
        token = token.lower()
        if token in ("1", "one"):
            return Cardinality.ONE
        if token in ("*", "many", "n"):
            return Cardinality.MANY
        if token in ("0..1", "zero-or-one"):
            return Cardinality.ZERO_OR_ONE
        if token in ("1..*", "one-or-many"):
            return Cardinality.ONE_OR_MANY
        return Cardinality.ONE
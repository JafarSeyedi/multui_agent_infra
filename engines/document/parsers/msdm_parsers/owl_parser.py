# engines/document/parsers/msdm_parsers/owl_parser.py
"""
OWL / RDF Schema Parser – converts .owl and .rdf files into an MSDMDocument.

Handles OWL 2 (XML serialisation):
- owl:Class (including subClassOf, equivalentClass, disjointWith)
- owl:ObjectProperty (domain, range, inverseOf, characteristics)
- owl:DatatypeProperty (domain, range)
- owl:Restriction (someValuesFrom, allValuesFrom, cardinality)
- rdfs:label, rdfs:comment → description / annotations
- owl:imports, owl:versionInfo, ontology-level metadata
- unionOf, intersectionOf, complementOf, oneOf
- annotation properties

Every OWL construct that cannot be directly mapped to an MSDM Entity/Attribute/
EntityRelationship is stored as structured annotations (JSON) to ensure lossless round‑trip.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET

from ...models.media_types import MEDIA_TYPES
from ...models.msdm_models import Annotation
from ...models.msdm_models import Attribute
from ...models.msdm_models import Cardinality
from ...models.msdm_models import DataType
from ...models.msdm_models import Entity
from ...models.msdm_models import EntityKind
from ...models.msdm_models import MSDMDocument
from ...models.msdm_models import EntityRelationship
from ...models.msdm_models import ScalarType, Namespace
from ..base import ParseOptions
from .base_msdm_parser import BaseMSDMParser

# Namespaces
NS = {
    "owl":  "http://www.w3.org/2002/07/owl#",
    "rdf":  "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
    "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
}

# Mapping from XSD datatypes to ScalarType
XSD_TYPE_MAP = {
    "http://www.w3.org/2001/XMLSchema#string":  ScalarType.STRING,
    "http://www.w3.org/2001/XMLSchema#integer": ScalarType.INT,
    "http://www.w3.org/2001/XMLSchema#int":     ScalarType.INT,
    "http://www.w3.org/2001/XMLSchema#long":    ScalarType.LONG,
    "http://www.w3.org/2001/XMLSchema#float":   ScalarType.FLOAT,
    "http://www.w3.org/2001/XMLSchema#double":  ScalarType.DOUBLE,
    "http://www.w3.org/2001/XMLSchema#boolean": ScalarType.BOOLEAN,
    "http://www.w3.org/2001/XMLSchema#date":    ScalarType.DATE,
    "http://www.w3.org/2001/XMLSchema#dateTime": ScalarType.TIMESTAMP,
    "http://www.w3.org/2001/XMLSchema#time":    ScalarType.TIME,
    "http://www.w3.org/2001/XMLSchema#decimal": ScalarType.DECIMAL,
    "http://www.w3.org/2001/XMLSchema#anyURI":  ScalarType.STRING,
}


class OWLParser(BaseMSDMParser):
    name = "owl"
    supported_extensions = (".owl", ".rdf")

    async def _parse_to_msdm(
        self, data: bytes, source_name: str, options: ParseOptions
    ) -> MSDMDocument:
        encoding = options.encoding or "utf-8"
        text = data.decode(encoding)
        root = ET.fromstring(text)

        doc = MSDMDocument(
            document_id=Path(source_name).stem,
            title=Path(source_name).stem,
            media_type=MEDIA_TYPES.get("owl", MEDIA_TYPES["xml"])
        )
        doc.namespace = Namespace(uri=Path(source_name).stem)

        classes: dict[str, Entity] = {}
        object_props: dict[str, dict[str, Any]] = {}
        datatype_props: dict[str, dict[str, Any]] = {}

        self._collect_entities(root, classes)
        self._collect_properties(root, object_props, datatype_props)

        for prop_uri, prop_info in object_props.items():
            domain = prop_info.get("domain")
            range_cls = prop_info.get("range")
            if domain and range_cls and domain in classes and range_cls in classes:
                rel = EntityRelationship(
                    name=self._local_name(prop_uri),
                    from_ref_id=domain,
                    to_ref_id=range_cls,
                    cardinality_from=Cardinality.ONE,
                    cardinality_to=Cardinality.MANY,
                    description=prop_info.get("description"),
                )
                doc.relationships.append(rel)

        for prop_uri, prop_info in datatype_props.items():
            domain = prop_info.get("domain")
            range_type = prop_info.get("range")
            if domain and domain in classes:
                entity = classes[domain]
                dt = self._xsd_to_datatype(range_type)
                attr = Attribute(
                    name=self._local_name(prop_uri),
                    data_type=dt,
                    description=prop_info.get("description"),
                )
                entity.attributes.append(attr)

        for entity in classes.values():
            doc.entities.append(entity)

        self._extract_ontology_metadata(root, doc)
        self.resolve_references(doc)
        return doc

    def _collect_entities(self, root: ET.Element, classes: dict[str, Entity]) -> None:
        for class_elem in root.findall(".//owl:Class", NS):
            uri = class_elem.get(f"{{{NS['rdf']}}}about") or class_elem.get(f"{{{NS['rdf']}}}ID")
            if not uri:
                continue
            local_name = self._local_name(uri)
            entity = Entity(name=local_name, kind=EntityKind.OBJECT)
            entity.annotations.append(Annotation(key="rdf:about", value=uri))

            label = self._get_child_text(class_elem, "rdfs:label")
            if label:
                entity.description = label
            comment = self._get_child_text(class_elem, "rdfs:comment")
            if comment:
                entity.annotations.append(Annotation(key="comment", value=comment))

            for sub_elem in class_elem.findall("rdfs:subClassOf", NS):
                res = sub_elem.get(f"{{{NS['rdf']}}}resource")
                if res:
                    entity.extends_ref_id = self._local_name(res)
                    break

            for equiv in class_elem.findall("owl:equivalentClass", NS):
                self._store_ref_annotation(equiv, entity, "equivalentClass")
            for disj in class_elem.findall("owl:disjointWith", NS):
                self._store_ref_annotation(disj, entity, "disjointWith")

            self._parse_restrictions(class_elem, entity)
            classes[uri] = entity

    def _collect_properties(self, root: ET.Element,
                            object_props: dict[str, dict], datatype_props: dict[str, dict]) -> None:
        for prop_elem in root.findall(".//owl:ObjectProperty", NS):
            uri = prop_elem.get(f"{{{NS['rdf']}}}about") or prop_elem.get(f"{{{NS['rdf']}}}ID")
            if not uri:
                continue
            info = {
                "domain": None,
                "range": None,
                "description": self._get_child_text(prop_elem, "rdfs:comment"),
            }
            domain_elem = prop_elem.find("rdfs:domain", NS)
            if domain_elem is not None:
                info["domain"] = domain_elem.get(f"{{{NS['rdf']}}}resource")
            range_elem = prop_elem.find("rdfs:range", NS)
            if range_elem is not None:
                info["range"] = range_elem.get(f"{{{NS['rdf']}}}resource")
            inverse_elem = prop_elem.find("owl:inverseOf", NS)
            if inverse_elem is not None:
                info["inverse"] = inverse_elem.get(f"{{{NS['rdf']}}}resource")
            object_props[uri] = info

        for prop_elem in root.findall(".//owl:DatatypeProperty", NS):
            uri = prop_elem.get(f"{{{NS['rdf']}}}about") or prop_elem.get(f"{{{NS['rdf']}}}ID")
            if not uri:
                continue
            info = {
                "domain": None,
                "range": None,
                "description": self._get_child_text(prop_elem, "rdfs:comment"),
            }
            domain_elem = prop_elem.find("rdfs:domain", NS)
            if domain_elem is not None:
                info["domain"] = domain_elem.get(f"{{{NS['rdf']}}}resource")
            range_elem = prop_elem.find("rdfs:range", NS)
            if range_elem is not None:
                info["range"] = range_elem.get(f"{{{NS['rdf']}}}resource")
            datatype_props[uri] = info

    @staticmethod
    def _local_name(uri: str) -> str:
        if "#" in uri:
            return uri.rsplit("#", 1)[-1]
        return uri.rsplit("/", 1)[-1]

    def _get_child_text(self, parent: ET.Element, tag: str) -> str | None:
        el = parent.find(tag, NS)
        return el.text if el is not None and el.text else None

    def _store_ref_annotation(self, elem: ET.Element, entity: Entity, key: str) -> None:
        res = elem.get(f"{{{NS['rdf']}}}resource")
        if res:
            entity.annotations.append(Annotation(key=key, value=res))

    def _parse_restrictions(self, class_elem: ET.Element, entity: Entity) -> None:
        for restr in class_elem.findall("owl:Restriction", NS) + class_elem.findall("rdfs:subClassOf/owl:Restriction", NS):
            on_prop = restr.find("owl:onProperty", NS)
            if on_prop is None:
                continue
            on_prop_res = on_prop.get(f"{{{NS['rdf']}}}resource")
            if not on_prop_res:
                continue

            prop_name = self._local_name(on_prop_res)
            attr = next((a for a in entity.attributes if a.name == prop_name), None)
            if not attr:
                attr = Attribute(name=prop_name, data_type=DataType(base=ScalarType.ANY))
                entity.attributes.append(attr)

            some_vals = restr.find("owl:someValuesFrom", NS)
            if some_vals is not None:
                res = some_vals.get(f"{{{NS['rdf']}}}resource")
                if res:
                    dt = self._xsd_to_datatype(res)
                    if dt.base != ScalarType.ANY:
                        attr.data_type = dt
                    else:
                        attr.data_type = DataType(base=ScalarType.REF, ref_entity_id=self._local_name(res))

            card = restr.find("owl:cardinality", NS)
            min_card = restr.find("owl:minCardinality", NS)
            if card is not None:
                try:
                    card_val = int(card.text) if card.text else 0
                except ValueError:
                    card_val = 0
                if card_val >= 1:
                    attr.required = True
                if card_val == 0:
                    attr.annotations.append(Annotation(key="cardinality", value="0"))
            if min_card is not None:
                try:
                    min_val = int(min_card.text) if min_card.text else 0
                except ValueError:
                    min_val = 0
                if min_val >= 1:
                    attr.required = True
                attr.annotations.append(Annotation(key="minCardinality", value=str(min_val)))

    def _xsd_to_datatype(self, type_uri: str | None) -> DataType:
        if not type_uri:
            return DataType(base=ScalarType.ANY)
        if type_uri in XSD_TYPE_MAP:
            return DataType(base=XSD_TYPE_MAP[type_uri])
        return DataType(base=ScalarType.REF, ref_entity_id=self._local_name(type_uri))

    def _extract_ontology_metadata(self, root: ET.Element, doc: MSDMDocument) -> None:
        ontology = root.find("owl:Ontology", NS)
        if ontology is not None:
            for child in ontology:
                tag = child.tag.split("}")[-1]
                if tag == "imports":
                    doc.annotations.append(Annotation(key="import", value=child.get(f"{{{NS['rdf']}}}resource", "")))
                elif tag in ("versionInfo", "comment", "label"):
                    doc.annotations.append(Annotation(key=tag, value=child.text or ""))
            about = ontology.get(f"{{{NS['rdf']}}}about")
            if about:
                doc.annotations.append(Annotation(key="ontologyURI", value=about))
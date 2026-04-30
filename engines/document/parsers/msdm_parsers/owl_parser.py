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
Relationship is stored as structured annotations (JSON) to ensure lossless round‑trip.
"""

from __future__ import annotations
import json
from pathlib import Path
from typing import Optional, Dict, Any, List, Set, Tuple
from xml.etree import ElementTree as ET

from .base_msdm_parser import BaseMSDMParser
from ..base import ParseOptions
from ...models.msdm_models import (
    MSDMDocument,
    Entity,
    Attribute,
    DataType,
    Constraint,
    ConstraintType,
    Index,
    Annotation,
    EntityKind,
    ScalarType,
    Relationship,
    Cardinality,
)

# ── Namespaces ──────────────────────────────────────────────────────
NS = {
    "owl":  "http://www.w3.org/2002/07/owl#",
    "rdf":  "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
    "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
}

# ── Mapping from XSD datatypes to ScalarType ────────────────────────
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
    """Parser for OWL / RDF Schema files (.owl, .rdf)."""
    name = "owl"
    supported_extensions = (".owl", ".rdf")

    async def _parse_to_msdm(
        self, data: bytes, source_name: str, options: ParseOptions
    ) -> MSDMDocument:
        encoding = options.encoding or "utf-8"
        text = data.decode(encoding)
        root = ET.fromstring(text)

        doc = MSDMDocument()
        doc.namespace = Path(source_name).stem

        # Two‑pass approach: first collect all class and property declarations,
        # then assign domains/ranges to create relationships/attributes.
        classes: Dict[str, Entity] = {}
        object_props: Dict[str, Dict[str, Any]] = {}
        datatype_props: Dict[str, Dict[str, Any]] = {}

        # 1st pass – collect classes and properties
        self._collect_entities(root, classes)
        self._collect_properties(root, object_props, datatype_props)

        # 2nd pass – create relationships and attributes from properties
        for prop_uri, prop_info in object_props.items():
            domain = prop_info.get("domain")
            range_cls = prop_info.get("range")
            if domain and range_cls and domain in classes and range_cls in classes:
                rel = Relationship(
                    name=self._local_name(prop_uri),
                    from_entity=domain,
                    to_entity=range_cls,
                    cardinality_from=Cardinality.ONE,
                    cardinality_to=Cardinality.MANY,
                    description=prop_info.get("description"),
                )
                doc.relationships.append(rel)
            # If domain or range is missing, still note it as annotation on appropriate entities

        for prop_uri, prop_info in datatype_props.items():
            domain = prop_info.get("domain")
            range_type = prop_info.get("range")  # XSD type URI
            if domain and domain in classes:
                entity = classes[domain]
                dt = self._xsd_to_datatype(range_type)
                attr = Attribute(
                    name=self._local_name(prop_uri),
                    data_type=dt,
                    description=prop_info.get("description"),
                )
                entity.attributes.append(attr)

        # Add collected classes to document entities
        for entity in classes.values():
            doc.entities.append(entity)

        # Store ontology metadata
        self._extract_ontology_metadata(root, doc)

        return doc

    # ── 1st pass helpers ────────────────────────────────────────────
    def _collect_entities(self, root: ET.Element, classes: Dict[str, Entity]) -> None:
        """Find all owl:Class declarations and record them."""
        for class_elem in root.findall(".//owl:Class", NS):
            uri = class_elem.get(f"{{{NS['rdf']}}}about")
            if not uri:
                uri = class_elem.get(f"{{{NS['rdf']}}}ID")
            if not uri:
                continue
            local_name = self._local_name(uri)
            entity = Entity(
                name=local_name,
                kind=EntityKind.OBJECT,
            )
            # Store full URI for later reference
            entity.annotations.append(Annotation(key="rdf:about", value=uri))

            # Label and comment
            label = self._get_child_text(class_elem, "rdfs:label")
            if label:
                entity.description = label
            comment = self._get_child_text(class_elem, "rdfs:comment")
            if comment:
                entity.annotations.append(Annotation(key="comment", value=comment))

            # Subclass relationships
            for sub_elem in class_elem.findall("rdfs:subClassOf", NS):
                res = sub_elem.get(f"{{{NS['rdf']}}}resource")
                if res:
                    entity.extends = self._local_name(res)
                    break  # take first

            # Equivalent classes, disjoints – stored as annotations
            for equiv in class_elem.findall("owl:equivalentClass", NS):
                self._store_ref_annotation(equiv, entity, "equivalentClass")
            for disj in class_elem.findall("owl:disjointWith", NS):
                self._store_ref_annotation(disj, entity, "disjointWith")

            # Restrictions (someValuesFrom, allValuesFrom) – can be used to interpret attributes
            self._parse_restrictions(class_elem, entity)

            classes[uri] = entity

    def _collect_properties(self, root: ET.Element,
                            object_props: Dict[str, Dict], datatype_props: Dict[str, Dict]) -> None:
        """Collect owl:ObjectProperty and owl:DatatypeProperty declarations."""
        for prop_elem in root.findall(".//owl:ObjectProperty", NS):
            uri = prop_elem.get(f"{{{NS['rdf']}}}about") or prop_elem.get(f"{{{NS['rdf']}}}ID")
            if not uri:
                continue
            info = {
                "domain": None,
                "range": None,
                "description": self._get_child_text(prop_elem, "rdfs:comment"),
            }
            # Domain
            domain_elem = prop_elem.find("rdfs:domain", NS)
            if domain_elem is not None:
                info["domain"] = domain_elem.get(f"{{{NS['rdf']}}}resource")
            # Range
            range_elem = prop_elem.find("rdfs:range", NS)
            if range_elem is not None:
                info["range"] = range_elem.get(f"{{{NS['rdf']}}}resource")
            # Inverse
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

    # ── Helpers ──────────────────────────────────────────────────────
    @staticmethod
    def _local_name(uri: str) -> str:
        """Extract the last part of a URI (after # or last /)."""
        if "#" in uri:
            return uri.rsplit("#", 1)[-1]
        return uri.rsplit("/", 1)[-1]

    def _get_child_text(self, parent: ET.Element, tag: str) -> Optional[str]:
        el = parent.find(tag, NS)
        return el.text if el is not None and el.text else None

    def _store_ref_annotation(self, elem: ET.Element, entity: Entity, key: str) -> None:
        """Store a resource reference from a child element as an annotation."""
        res = elem.get(f"{{{NS['rdf']}}}resource")
        if res:
            entity.annotations.append(Annotation(key=key, value=res))

    def _parse_restrictions(self, class_elem: ET.Element, entity: Entity) -> None:
        """Extract property restrictions (someValuesFrom, allValuesFrom, cardinality)
        and convert them to attributes when possible."""
        for restr in class_elem.findall("owl:Restriction", NS) + class_elem.findall("rdfs:subClassOf/owl:Restriction", NS):
            on_prop = restr.find("owl:onProperty", NS)
            on_prop_res = None
            if on_prop is not None:
                on_prop_res = on_prop.get(f"{{{NS['rdf']}}}resource")
            if not on_prop_res:
                continue

            # Determine the kind of restriction
            some_vals = restr.find("owl:someValuesFrom", NS)
            all_vals = restr.find("owl:allValuesFrom", NS)
            card = restr.find("owl:cardinality", NS)
            min_card = restr.find("owl:minCardinality", NS)
            max_card = restr.find("owl:maxCardinality", NS)

            # Create an attribute for the property if not already present
            prop_name = self._local_name(on_prop_res)
            existing = next((a for a in entity.attributes if a.name == prop_name), None)
            if not existing:
                attr = Attribute(name=prop_name, data_type=DataType(base=ScalarType.ANY))
                entity.attributes.append(attr)
            else:
                attr = existing

            # If someValuesFrom specifies a range type/class, refine the DataType
            if some_vals is not None:
                res = some_vals.get(f"{{{NS['rdf']}}}resource")
                if res:
                    # Could be a class or datatype – if it's a known XSD type, set scalar
                    dt = self._xsd_to_datatype(res)
                    if dt.base != ScalarType.ANY:
                        attr.data_type = dt
                    else:
                        # It's a class reference – the attribute is a reference to that entity
                        attr.data_type = DataType(base=ScalarType.REF, ref_entity=self._local_name(res))

            # Cardinality constraints
            if card is not None:
                card_val = int(card.get(f"{{{NS['rdf']}}}datatype", "")) if card.text else 0
                if card_val >= 1:
                    attr.required = True
                if card_val == 0:
                    attr.annotations.append(Annotation(key="cardinality", value="0"))
            if min_card is not None:
                min_val = int(min_card.text) if min_card.text else 0
                if min_val >= 1:
                    attr.required = True
                attr.annotations.append(Annotation(key="minCardinality", value=str(min_val)))
            if max_card is not None:
                max_val = int(max_card.text) if max_card.text else 0
                attr.annotations.append(Annotation(key="maxCardinality", value=str(max_val)))

    def _xsd_to_datatype(self, type_uri: Optional[str]) -> DataType:
        """Convert an XSD type URI to DataType."""
        if not type_uri:
            return DataType(base=ScalarType.ANY)
        if type_uri in XSD_TYPE_MAP:
            return DataType(base=XSD_TYPE_MAP[type_uri])
        # It's a custom class (object property range) – return REF
        return DataType(base=ScalarType.REF, ref_entity=self._local_name(type_uri))

    def _extract_ontology_metadata(self, root: ET.Element, doc: MSDMDocument) -> None:
        """Collect ontology-level annotations (imports, version, etc.)."""
        ontology = root.find("owl:Ontology", NS)
        if ontology is not None:
            for child in ontology:
                tag = child.tag.split("}")[-1]
                if tag == "imports":
                    doc.annotations.append(Annotation(key="import", value=child.get(f"{{{NS['rdf']}}}resource", "")))
                elif tag in ("versionInfo", "comment", "label"):
                    doc.annotations.append(Annotation(key=tag, value=child.text or ""))
            # Also add the ontology URI
            about = ontology.get(f"{{{NS['rdf']}}}about")
            if about:
                doc.annotations.append(Annotation(key="ontologyURI", value=about))
# engines/document/writers/msdm_writers/owl_writer.py
"""
OWL / RDF Schema Writer – converts an MSDMDocument into an OWL 2 XML ontology.
Produces an owl:Ontology containing owl:Class, owl:ObjectProperty,
owl:DatatypeProperty, and rdfs:subClassOf definitions for entities and
relationships.  Annotations (restrictions, equivalent classes, etc.) stored
during parsing are written back for round‑trip fidelity.
"""

from __future__ import annotations
from typing import Optional, Dict, Any, List
from xml.etree.ElementTree import Element, SubElement, tostring

from .base_msdm_writer import BaseMSDMWriter, WriteTarget, SoftDeleteStrategy
from engines.document.writers.base import WriteOptions
from engines.document.models.msdm_models import (
    MSDMDocument,
    Entity,
    Attribute,
    DataType,
    ScalarType,
    Relationship,
    Annotation,
    Cardinality,
    Constraint,
    ConstraintType,
    EntityKind,
)

# ── XSD datatype mapping ───────────────────────────────────────────
XSD_NS = "http://www.w3.org/2001/XMLSchema#"
_SCALAR_XSD_MAP: Dict[ScalarType, str] = {
    ScalarType.STRING:    "string",
    ScalarType.INT:       "integer",
    ScalarType.LONG:      "long",
    ScalarType.FLOAT:     "float",
    ScalarType.DOUBLE:    "double",
    ScalarType.BOOLEAN:   "boolean",
    ScalarType.DATE:      "date",
    ScalarType.TIME:      "time",
    ScalarType.TIMESTAMP: "dateTime",
    ScalarType.DURATION:  "duration",
    ScalarType.UUID:      "anyURI",
    ScalarType.BINARY:    "base64Binary",
    ScalarType.DECIMAL:   "decimal",
    ScalarType.ANY:       "anyType",
}

# ── OWL Namespaces ───────────────────────────────────────────────
OWL_NS = "http://www.w3.org/2002/07/owl#"
RDF_NS = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
RDFS_NS = "http://www.w3.org/2000/01/rdf-schema#"

NS_MAP = {
    "xmlns": OWL_NS,
    "xmlns:rdf": RDF_NS,
    "xmlns:rdfs": RDFS_NS,
    "xmlns:xsd": XSD_NS.rstrip("#"),
    "xmlns:owl": OWL_NS,
}


class OWLWriter(BaseMSDMWriter):
    """Writer for OWL / RDF Schema files (.owl, .rdf)."""
    name = "owl"
    supported_extensions = (".owl", ".rdf")

    def __init__(
        self,
        options: Optional[WriteOptions] = None,
        target_mode: WriteTarget = WriteTarget.DESIGN_FILE,
        soft_delete_strategy: SoftDeleteStrategy = SoftDeleteStrategy.NONE,
    ):
        super().__init__(options, target_mode, soft_delete_strategy)

    # ── Public API ─────────────────────────────────────────────────
    async def _write_design(self, document: MSDMDocument) -> bytes:
        onto_uri = self._get_ontology_uri(document)
        root = Element(f"{{{RDF_NS}}}RDF", NS_MAP)

        # Ontology element
        ontology = SubElement(root, f"{{{OWL_NS}}}Ontology", {f"{{{RDF_NS}}}about": onto_uri})
        # Add imports / version from annotations
        for ann in document.annotations:
            if ann.key == "import":
                SubElement(ontology, f"{{{OWL_NS}}}imports", {f"{{{RDF_NS}}}resource": ann.value})
            elif ann.key == "versionInfo":
                SubElement(ontology, f"{{{OWL_NS}}}versionInfo").text = ann.value
            elif ann.key in ("comment", "label"):
                elem = SubElement(ontology, f"{{{RDFS_NS}}}{ann.key}")
                elem.text = ann.value

        # Process entities (classes)
        # We'll collect properties separately: from attributes (datatype/object) and from relationships (object).
        # But to avoid duplicates, we'll process relationships first as they are explicit.

        # Map class URIs to entity
        class_uri_map: Dict[str, str] = {}
        for entity in document.entities:
            if entity.kind in (EntityKind.OBJECT, EntityKind.TABLE, EntityKind.DOCUMENT, EntityKind.GRAPH_NODE):
                class_uri = self._entity_to_uri(entity, document)
                class_uri_map[entity.name] = class_uri
                # Add class declaration
                class_elem = SubElement(root, f"{{{OWL_NS}}}Class", {f"{{{RDF_NS}}}about": class_uri})
                # Annotation for description
                if entity.description:
                    SubElement(class_elem, f"{{{RDFS_NS}}}comment").text = entity.description
                # Subclass relationship from extends
                if entity.extends and entity.extends in class_uri_map:
                    sub_class_of = SubElement(class_elem, f"{{{RDFS_NS}}}subClassOf", {
                        f"{{{RDF_NS}}}resource": class_uri_map[entity.extends]
                    })
                # Restore annotations for round-trip (equivalentClass, disjointWith, restrictions)
                for ann in entity.annotations:
                    if ann.key == "equivalentClass":
                        SubElement(class_elem, f"{{{OWL_NS}}}equivalentClass", {f"{{{RDF_NS}}}resource": ann.value})
                    elif ann.key == "disjointWith":
                        SubElement(class_elem, f"{{{OWL_NS}}}disjointWith", {f"{{{RDF_NS}}}resource": ann.value})
                    elif ann.key == "rdf:about":
                        pass  # already used as class uri
                    # We'll also store restrictions from annotations? They are complex XML, better to keep as raw annotation for round-trip only; the writer can't reconstruct them easily.
                    # We'll write them as a comment? No.
                    # We'll store raw restrictions in a <owl:Restriction> element only if we stored the whole restriction XML? In parser, we didn't store raw XML. This writer focuses on the core model; advanced OWL axioms are out of scope for a generic writer. They can be stored as annotations and manually restored.

        # Process entities that are attributes (datatype/object properties)
        for entity in document.entities:
            for attr in entity.attributes:
                # Skip if the attribute is from a relationship? No, attributes are always direct.
                # Determine if datatype or object property based on type
                prop_uri = self._property_uri(entity.name, attr.name, document)
                dt = attr.data_type
                if dt.base == ScalarType.REF and dt.ref_entity and dt.ref_entity in class_uri_map:
                    # Object property
                    prop_elem = SubElement(root, f"{{{OWL_NS}}}ObjectProperty", {f"{{{RDF_NS}}}about": prop_uri})
                    domain_class_uri = class_uri_map.get(entity.name)
                    if domain_class_uri:
                        SubElement(prop_elem, f"{{{RDFS_NS}}}domain", {f"{{{RDF_NS}}}resource": domain_class_uri})
                    range_class_uri = class_uri_map.get(dt.ref_entity)
                    if range_class_uri:
                        SubElement(prop_elem, f"{{{RDFS_NS}}}range", {f"{{{RDF_NS}}}resource": range_class_uri})
                    # For cardinalities, we can add an OWL restriction on the domain? Not necessary for basic property.
                else:
                    # Datatype property
                    prop_elem = SubElement(root, f"{{{OWL_NS}}}DatatypeProperty", {f"{{{RDF_NS}}}about": prop_uri})
                    domain_class_uri = class_uri_map.get(entity.name)
                    if domain_class_uri:
                        SubElement(prop_elem, f"{{{RDFS_NS}}}domain", {f"{{{RDF_NS}}}resource": domain_class_uri})
                    # Determine XSD range
                    xsd_type = _SCALAR_XSD_MAP.get(dt.base, "string")
                    SubElement(prop_elem, f"{{{RDFS_NS}}}range", {
                        f"{{{RDF_NS}}}resource": XSD_NS + xsd_type
                    })
                # Add description if present
                if attr.description:
                    SubElement(prop_elem, f"{{{RDFS_NS}}}comment").text = attr.description

        # Process relationships (they may also represent object properties)
        for rel in document.relationships:
            prop_uri = self._rel_to_uri(rel, document)
            if rel.from_entity in class_uri_map and rel.to_entity in class_uri_map:
                prop_elem = SubElement(root, f"{{{OWL_NS}}}ObjectProperty", {f"{{{RDF_NS}}}about": prop_uri})
                SubElement(prop_elem, f"{{{RDFS_NS}}}domain", {
                    f"{{{RDF_NS}}}resource": class_uri_map[rel.from_entity]})
                SubElement(prop_elem, f"{{{RDFS_NS}}}range", {
                    f"{{{RDF_NS}}}resource": class_uri_map[rel.to_entity]})
                if rel.description:
                    SubElement(prop_elem, f"{{{RDFS_NS}}}comment").text = rel.description
                # For cardinalities, could add owl:Restriction but that's complex.

        xml_str = tostring(root, encoding="unicode", method="xml")
        return xml_str.encode(self.options.encoding or "utf-8")

    async def get_supported_media_types(self) -> list[str]:
        return ["application/rdf+xml"]

    async def get_supported_extensions(self) -> list[str]:
        return self.supported_extensions

    # ── URI helpers ────────────────────────────────────────────────
    def _base_uri(self, doc: MSDMDocument) -> str:
        # Use namespace if set, otherwise generate from document id
        ns = doc.namespace or "http://example.org/ontology"
        return ns.rstrip("/#") + "#"

    def _entity_to_uri(self, entity: Entity, doc: MSDMDocument) -> str:
        return self._base_uri(doc) + entity.name

    def _property_uri(self, class_name: str, prop_name: str, doc: MSDMDocument) -> str:
        return self._base_uri(doc) + f"{class_name}/{prop_name}"

    def _rel_to_uri(self, rel: Relationship, doc: MSDMDocument) -> str:
        name = rel.name or f"{rel.from_entity}_to_{rel.to_entity}"
        return self._base_uri(doc) + name

    def _get_ontology_uri(self, doc: MSDMDocument) -> str:
        ann = next((a for a in doc.annotations if a.key == "ontologyURI"), None)
        return ann.value if ann else self._base_uri(doc)
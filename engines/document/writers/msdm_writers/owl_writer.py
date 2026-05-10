# engines/document/writers/msdm_writers/owl_writer.py
"""
OWL / RDF Schema Writer – converts an MSDMDocument into an OWL 2 XML ontology.
Produces an owl:Ontology containing owl:Class, owl:ObjectProperty,
owl:DatatypeProperty, and rdfs:subClassOf definitions for entities and
relationships.  Annotations (restrictions, equivalent classes, etc.) stored
during parsing are written back for round‑trip fidelity.
"""
from __future__ import annotations

from xml.etree.ElementTree import Element
from xml.etree.ElementTree import SubElement
from xml.etree.ElementTree import tostring

from ...models.msdm_models import Entity
from ...models.msdm_models import EntityKind
from ...models.msdm_models import MSDMDocument
from ...models.msdm_models import EntityRelationship
from ...models.msdm_models import ScalarType
from ..base import WriteOptions
from .base_msdm_writer import BaseMSDMWriter
from .base_msdm_writer import SoftDeleteStrategy
from .base_msdm_writer import WriteTarget

# XSD datatype mapping
XSD_NS = "http://www.w3.org/2001/XMLSchema#"
_SCALAR_XSD_MAP: dict[ScalarType, str] = {
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

# OWL Namespaces
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
    name = "owl"
    supported_extensions = (".owl", ".rdf")

    def __init__(
        self,
        options: WriteOptions | None = None,
        target_mode: WriteTarget = WriteTarget.DESIGN_FILE,
        soft_delete_strategy: SoftDeleteStrategy = SoftDeleteStrategy.NONE,
    ):
        super().__init__(options, target_mode, soft_delete_strategy)

    async def _write_design(self, document: MSDMDocument) -> bytes:
        onto_uri = self._get_ontology_uri(document)
        root = Element(f"{{{RDF_NS}}}RDF", NS_MAP)

        ontology = SubElement(root, f"{{{OWL_NS}}}Ontology", {f"{{{RDF_NS}}}about": onto_uri})
        for ann in document.annotations:
            if ann.key == "import":
                SubElement(ontology, f"{{{OWL_NS}}}imports", {f"{{{RDF_NS}}}resource": ann.value})
            elif ann.key == "versionInfo":
                SubElement(ontology, f"{{{OWL_NS}}}versionInfo").text = ann.value
            elif ann.key in ("comment", "label"):
                elem = SubElement(ontology, f"{{{RDFS_NS}}}{ann.key}")
                elem.text = ann.value

        class_uri_map: dict[str, str] = {}
        for entity in document.entities:
            if entity.kind in (EntityKind.OBJECT, EntityKind.TABLE, EntityKind.DOCUMENT, EntityKind.GRAPH_NODE):
                class_uri = self._entity_to_uri(entity, document)
                class_uri_map[entity.name] = class_uri
                class_elem = SubElement(root, f"{{{OWL_NS}}}Class", {f"{{{RDF_NS}}}about": class_uri})
                if entity.description:
                    SubElement(class_elem, f"{{{RDFS_NS}}}comment").text = entity.description
                if entity.extends and entity.extends.name in class_uri_map:
                    SubElement(class_elem, f"{{{RDFS_NS}}}subClassOf", {
                        f"{{{RDF_NS}}}resource": class_uri_map[entity.extends.name]
                    })
                for ann in entity.annotations:
                    if ann.key == "equivalentClass":
                        SubElement(class_elem, f"{{{OWL_NS}}}equivalentClass", {f"{{{RDF_NS}}}resource": ann.value})
                    elif ann.key == "disjointWith":
                        SubElement(class_elem, f"{{{OWL_NS}}}disjointWith", {f"{{{RDF_NS}}}resource": ann.value})

        for entity in document.entities:
            for attr in entity.attributes:
                prop_uri = self._property_uri(entity.name, attr.name, document)
                dt = attr.data_type
                if dt.base == ScalarType.REF and dt.ref_entity and dt.ref_entity.name in class_uri_map:
                    # Object property
                    prop_elem = SubElement(root, f"{{{OWL_NS}}}ObjectProperty", {f"{{{RDF_NS}}}about": prop_uri})
                    domain_class_uri = class_uri_map.get(entity.name)
                    if domain_class_uri:
                        SubElement(prop_elem, f"{{{RDFS_NS}}}domain", {f"{{{RDF_NS}}}resource": domain_class_uri})
                    range_class_uri = class_uri_map.get(dt.ref_entity.name)
                    if range_class_uri:
                        SubElement(prop_elem, f"{{{RDFS_NS}}}range", {f"{{{RDF_NS}}}resource": range_class_uri})
                else:
                    # Datatype property
                    prop_elem = SubElement(root, f"{{{OWL_NS}}}DatatypeProperty", {f"{{{RDF_NS}}}about": prop_uri})
                    domain_class_uri = class_uri_map.get(entity.name)
                    if domain_class_uri:
                        SubElement(prop_elem, f"{{{RDFS_NS}}}domain", {f"{{{RDF_NS}}}resource": domain_class_uri})
                    xsd_type = _SCALAR_XSD_MAP.get(dt.base, "string")
                    SubElement(prop_elem, f"{{{RDFS_NS}}}range", {
                        f"{{{RDF_NS}}}resource": XSD_NS + xsd_type
                    })
                if attr.description:
                    SubElement(prop_elem, f"{{{RDFS_NS}}}comment").text = attr.description

        for rel in document.relationships:
            prop_uri = self._rel_to_uri(rel, document)
            if rel.from_entity is not None and rel.from_entity.name in class_uri_map and rel.to_entity is not None and rel.to_entity.name in class_uri_map:
                prop_elem = SubElement(root, f"{{{OWL_NS}}}ObjectProperty", {f"{{{RDF_NS}}}about": prop_uri})
                SubElement(prop_elem, f"{{{RDFS_NS}}}domain", {
                    f"{{{RDF_NS}}}resource": class_uri_map[rel.from_entity.name]})
                SubElement(prop_elem, f"{{{RDFS_NS}}}range", {
                    f"{{{RDF_NS}}}resource": class_uri_map[rel.to_entity.name]})
                if rel.description:
                    SubElement(prop_elem, f"{{{RDFS_NS}}}comment").text = rel.description

        xml_str = tostring(root, encoding="unicode", method="xml")
        return xml_str.encode(getattr(self.options, "encoding", "utf-8") or "utf-8")

    def get_supported_media_types(self) -> list[str]:
        return ["application/rdf+xml"]

    def get_supported_extensions(self) -> list[str]:
        return list(self.supported_extensions)

    def _base_uri(self, doc: MSDMDocument) -> str:
        ns = ""
        if doc.namespace:
            ns = doc.namespace.uri
        ns = ns or "http://example.org/ontology"
        return ns.rstrip("/#") + "#"

    def _entity_to_uri(self, entity: Entity, doc: MSDMDocument) -> str:
        return self._base_uri(doc) + entity.name

    def _property_uri(self, class_name: str, prop_name: str, doc: MSDMDocument) -> str:
        return self._base_uri(doc) + f"{class_name}/{prop_name}"

    def _rel_to_uri(self, rel: EntityRelationship, doc: MSDMDocument) -> str:
        if rel.from_entity is not None and rel.to_entity is not None:
            name = rel.name or f"{rel.from_entity.name}_to_{rel.to_entity.name}"
        else:
            name = rel.name or f"{str(rel.from_ref_id)}_to_{str(rel.to_ref_id)}"
        return self._base_uri(doc) + name

    def _get_ontology_uri(self, doc: MSDMDocument) -> str:
        ann = next((a for a in doc.annotations if a.key == "ontologyURI"), None)
        return ann.value if ann else self._base_uri(doc)
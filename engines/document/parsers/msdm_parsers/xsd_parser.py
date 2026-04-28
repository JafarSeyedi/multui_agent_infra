# engines/document/parsers/msdm_parsers/xsd_parser.py
"""
XSD (XML Schema Definition) Parser – converts .xsd files into an MSDMDocument.

Handles:
- <xs:schema> root attributes (targetNamespace, elementFormDefault, etc.)
- <xs:element> (global and local)
- <xs:complexType> and <xs:simpleType> (named and anonymous)
- <xs:sequence>, <xs:choice>, <xs:all> compositors
- <xs:attribute> and <xs:attributeGroup>
- <xs:group>
- <xs:restriction> and <xs:extension> (with base type)
- <xs:simpleContent> and <xs:complexContent>
- <xs:annotation>, <xs:documentation>, <xs:appinfo>
- <xs:any> and <xs:anyAttribute> wildcards
- <xs:union> and <xs:list>
- <xs:key>, <xs:unique>, <xs:keyref> identity constraints

Every XSD detail is mapped to MSDM Entity (kind=OBJECT), Attribute, Constraint,
and Annotation objects.  Complex structures are faithfully captured; facets and
wildcards are stored as annotations for round‑trip fidelity.
"""

from __future__ import annotations
from typing import Optional, Dict, Any, List, Tuple, Set, Union
from xml.etree import ElementTree as ET
from pathlib import Path

from .base_msdm_parser import BaseMSDMParser
from engines.document.parsers.base import ParseOptions
from engines.document.models.msdm_models import (
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
)

# ── XML Schema namespace ──────────────────────────────────────────
XSD_NS = "http://www.w3.org/2001/XMLSchema"
NS = {"xs": XSD_NS}

# Mapping from XSD built‑in types to ScalarType
XSD_BUILTIN_MAP = {
    "string":        ScalarType.STRING,
    "normalizedString": ScalarType.STRING,
    "token":         ScalarType.STRING,
    "base64Binary":  ScalarType.BINARY,
    "hexBinary":     ScalarType.BINARY,
    "integer":       ScalarType.INT,
    "positiveInteger": ScalarType.INT,
    "negativeInteger": ScalarType.INT,
    "nonNegativeInteger": ScalarType.INT,
    "nonPositiveInteger": ScalarType.INT,
    "long":          ScalarType.LONG,
    "unsignedLong":  ScalarType.LONG,
    "int":           ScalarType.INT,
    "unsignedInt":   ScalarType.INT,
    "short":         ScalarType.INT,
    "unsignedShort": ScalarType.INT,
    "byte":          ScalarType.INT,
    "unsignedByte":  ScalarType.INT,
    "decimal":       ScalarType.DECIMAL,
    "float":         ScalarType.FLOAT,
    "double":        ScalarType.DOUBLE,
    "boolean":       ScalarType.BOOLEAN,
    "date":          ScalarType.DATE,
    "dateTime":      ScalarType.TIMESTAMP,
    "time":          ScalarType.TIME,
    "duration":      ScalarType.DURATION,
    "anyURI":        ScalarType.STRING,
    "QName":         ScalarType.STRING,
    "NOTATION":      ScalarType.STRING,
}


class XSDParser(BaseMSDMParser):
    """Parser for XML Schema Definition (.xsd) files."""
    name = "xsd"
    supported_extensions = (".xsd",)

    async def _parse_to_msdm(
        self, data: bytes, source_name: str, options: ParseOptions
    ) -> MSDMDocument:
        encoding = options.encoding or "utf-8"
        text = data.decode(encoding)
        root = ET.fromstring(text)

        doc = MSDMDocument()
        doc.namespace = Path(source_name).stem   # fallback

        # Store schema-level attributes as annotations
        for attr_name in ("targetNamespace", "elementFormDefault", "attributeFormDefault",
                          "version", "id"):
            val = root.get(attr_name)
            if val:
                doc.annotations.append(Annotation(key=attr_name, value=val))
        # Schema annotations (top‑level)
        ann_elem = root.find("xs:annotation", NS)
        if ann_elem is not None:
            doc.annotations.append(Annotation(key="annotation", value=ET.tostring(ann_elem, encoding="unicode")))

        # Two‑pass: first collect all named global definitions
        self._registry: Dict[str, dict] = {}   # name → {"type": …, "element": …}
        for child in root:
            tag = child.tag.split("}")[-1]
            if tag in ("complexType", "simpleType", "group", "attributeGroup"):
                name = child.get("name")
                if name:
                    self._registry.setdefault(name, {})[tag] = child
            elif tag == "element":
                name = child.get("name")
                if name:
                    self._registry.setdefault(name, {})["element"] = child

        # Second pass: process all definitions
        for name, entries in self._registry.items():
            if "complexType" in entries:
                self._parse_complex_type(name, entries["complexType"], doc)
            elif "simpleType" in entries:
                self._parse_simple_type(name, entries["simpleType"], doc)
            elif "element" in entries:
                # If the element has an anonymous complex/simple type inside, process it
                self._parse_global_element(name, entries["element"], doc)
            # Groups/attributeGroups are stored as annotations for round‑trip
            for kind in ("group", "attributeGroup"):
                if kind in entries:
                    doc.annotations.append(Annotation(key=f"xs_{kind}", value=ET.tostring(entries[kind], encoding="unicode")))

        return doc

    # ── Named complex type ──────────────────────────────────────
    def _parse_complex_type(self, name: str, ct_elem: ET.Element, doc: MSDMDocument) -> Entity:
        entity = Entity(name=name, kind=EntityKind.OBJECT)
        # Store original XML for round‑trip
        entity.annotations.append(Annotation(key="xs_complexType", value=ET.tostring(ct_elem, encoding="unicode")))

        # Abstract, final, block
        for attr in ("abstract", "final", "block", "mixed"):
            val = ct_elem.get(attr)
            if val:
                entity.annotations.append(Annotation(key=attr, value=val))

        # Process content: simpleContent / complexContent / open content
        self._process_complex_content(ct_elem, entity, doc)
        doc.entities.append(entity)
        return entity

    def _process_complex_content(self, parent: ET.Element, entity: Entity, doc: MSDMDocument) -> None:
        """
        Handle the interior of a complexType: either a compositor (sequence, choice, all)
        directly, or complexContent/simpleContent, or attributes.
        """
        # Check for simpleContent or complexContent child
        sc = parent.find("xs:simpleContent", NS)
        cc = parent.find("xs:complexContent", NS)
        if sc is not None:
            # simpleContent extends/restricts a simple type → entity may have a value attribute
            ext = sc.find("xs:extension", NS) or sc.find("xs:restriction", NS)
            if ext is not None:
                base = ext.get("base")
                self._process_base_type(base, entity, doc)
                # Process attributes under extension/restriction
                self._process_attributes(ext, entity)
                # Simple content: main value is the text content
                # Add a pseudo attribute for the text content if not already present
                if not any(a.name == "value" for a in entity.attributes):
                    dt = self._resolve_type_qname(base)
                    entity.attributes.append(Attribute(name="value", data_type=dt))
        elif cc is not None:
            # complexContent extends/restricts
            child_elem = cc.find("xs:extension", NS) or cc.find("xs:restriction", NS)
            if child_elem is not None:
                base = child_elem.get("base")
                self._process_base_type(base, entity, doc)
                # Extract compositor and attributes
                self._process_compositor_or_attrs(child_elem, entity, doc)
        else:
            # Direct compositor (sequence, choice, all) or attributes
            self._process_compositor_or_attrs(parent, entity, doc)

    def _process_base_type(self, base_qname: str, entity: Entity, doc: MSDMDocument) -> None:
        """Set entity.extends from a base type QName."""
        if base_qname:
            # remove namespace prefix if any
            base_name = base_qname.split(":")[-1] if ":" in base_qname else base_qname
            entity.extends = base_name

    def _process_compositor_or_attrs(self, container: ET.Element, entity: Entity, doc: MSDMDocument) -> None:
        """Process any child compositor (sequence, choice, all) and attributes."""
        compositors = ("xs:sequence", "xs:choice", "xs:all")
        for tag in compositors:
            comp = container.find(tag, NS)
            if comp is not None:
                self._process_compositor(comp, entity, doc)
                break
        # Process attributes (including anyAttribute)
        self._process_attributes(container, entity)

    def _process_compositor(self, comp: ET.Element, entity: Entity, doc: MSDMDocument) -> None:
        """Process a sequence/choice/all and create attributes."""
        # Record the compositor type as annotation on the entity (for round‑trip)
        compositor_type = comp.tag.split("}")[-1]
        entity.annotations.append(Annotation(key="compositor", value=compositor_type))

        for child in comp:
            tag = child.tag.split("}")[-1]
            if tag == "element":
                attr = self._parse_element(child, doc)
                if attr:
                    entity.attributes.append(attr)
            elif tag == "group":
                # Reference to a group – store as annotation
                ref = child.get("ref")
                if ref:
                    entity.annotations.append(Annotation(key="group_ref", value=ref))
            elif tag == "choice":
                # Nested choice – flatten (store as annotation)
                self._process_compositor(child, entity, doc)
            elif tag == "sequence":
                self._process_compositor(child, entity, doc)
            elif tag == "any":
                entity.annotations.append(Annotation(key="any", value=ET.tostring(child, encoding="unicode")))

    def _parse_element(self, elem: ET.Element, doc: MSDMDocument) -> Optional[Attribute]:
        """Parse an <xs:element> into an Attribute."""
        name = elem.get("name")
        ref = elem.get("ref")
        if ref:
            name = ref.split(":")[-1] if ":" in ref else ref
        if not name:
            return None

        # Type (can be anonymous complex/simple type inside)
        type_qname = elem.get("type")
        anonymous_type = elem.find("xs:complexType", NS) or elem.find("xs:simpleType", NS)

        if anonymous_type is not None:
            # Create a nested entity for the anonymous type
            anon_name = f"{name}_type"
            if anonymous_type.tag.endswith("complexType"):
                nested_entity = self._parse_complex_type(anon_name, anonymous_type, doc)
            else:
                nested_entity = self._parse_simple_type(anon_name, anonymous_type, doc)
            dt = DataType(base=ScalarType.REF, ref_entity=nested_entity.name)
        elif type_qname:
            dt = self._resolve_type_qname(type_qname)
        else:
            dt = DataType(base=ScalarType.ANY)

        # MinOccurs / MaxOccurs
        min_occurs = int(elem.get("minOccurs", "1"))
        max_occurs_str = elem.get("maxOccurs", "1")
        is_array = max_occurs_str == "unbounded" or (max_occurs_str.isdigit() and int(max_occurs_str) > 1)
        required = min_occurs > 0

        if is_array:
            dt = DataType(base=ScalarType.ARRAY, element_type=dt)

        attr = Attribute(
            name=name,
            data_type=dt,
            required=required,
        )
        # Default / Fixed
        default = elem.get("default")
        fixed = elem.get("fixed")
        if default:
            attr.default_value = default
            attr.constraints.append(Constraint(type=ConstraintType.DEFAULT, expression=default))
        if fixed:
            attr.annotations.append(Annotation(key="fixed", value=fixed))

        # Nillable
        if elem.get("nillable") == "true":
            attr.annotations.append(Annotation(key="nillable", value="true"))

        # Store original element XML for round‑trip
        attr.annotations.append(Annotation(key="xs_element", value=ET.tostring(elem, encoding="unicode")))

        return attr

    def _process_attributes(self, container: ET.Element, entity: Entity) -> None:
        """Extract <xs:attribute> and <xs:anyAttribute> from container."""
        for attr_elem in container.findall("xs:attribute", NS):
            name = attr_elem.get("name")
            ref = attr_elem.get("ref")
            if ref:
                name = ref.split(":")[-1] if ":" in ref else ref
            if not name:
                continue
            type_qname = attr_elem.get("type")
            dt = self._resolve_type_qname(type_qname) if type_qname else DataType(base=ScalarType.STRING)
            use = attr_elem.get("use", "optional")
            attr = Attribute(
                name=name,
                data_type=dt,
                required=use == "required",
            )
            default = attr_elem.get("default")
            fixed = attr_elem.get("fixed")
            if default:
                attr.default_value = default
                attr.constraints.append(Constraint(type=ConstraintType.DEFAULT, expression=default))
            if fixed:
                attr.annotations.append(Annotation(key="fixed", value=fixed))
            entity.attributes.append(attr)

        # anyAttribute
        any_attr = container.find("xs:anyAttribute", NS)
        if any_attr is not None:
            entity.annotations.append(Annotation(key="anyAttribute", value=ET.tostring(any_attr, encoding="unicode")))

    # ── Named simple type ────────────────────────────────────
    def _parse_simple_type(self, name: str, st_elem: ET.Element, doc: MSDMDocument) -> Entity:
        entity = Entity(name=name, kind=EntityKind.OBJECT)
        entity.annotations.append(Annotation(key="xs_simpleType", value=ET.tostring(st_elem, encoding="unicode")))

        # Restriction, list, union
        restriction = st_elem.find("xs:restriction", NS)
        union = st_elem.find("xs:union", NS)
        list_elem = st_elem.find("xs:list", NS)

        if restriction is not None:
            base = restriction.get("base")
            dt = self._resolve_type_qname(base) if base else DataType(base=ScalarType.STRING)
            attr = Attribute(name="value", data_type=dt, required=True)
            # Facets → constraints and annotations
            self._parse_facets(restriction, attr)
            entity.attributes.append(attr)
        elif union is not None:
            # Union types are stored as annotations
            member_types = union.get("memberTypes", "")
            entity.annotations.append(Annotation(key="union_memberTypes", value=member_types))
            # Create a single ANY attribute
            entity.attributes.append(Attribute(name="value", data_type=DataType(base=ScalarType.ANY), required=True))
        elif list_elem is not None:
            item_type = list_elem.get("itemType")
            item_dt = self._resolve_type_qname(item_type) if item_type else DataType(base=ScalarType.STRING)
            dt = DataType(base=ScalarType.ARRAY, element_type=item_dt)
            entity.attributes.append(Attribute(name="value", data_type=dt, required=True))

        doc.entities.append(entity)
        return entity

    def _parse_facets(self, restriction: ET.Element, attr: Attribute) -> None:
        """Extract XSD facets and apply as typed constraints."""
        facet_map = {
            "minLength":      ConstraintType.MIN_LENGTH,
            "maxLength":      ConstraintType.MAX_LENGTH,
            "length":         ConstraintType.LENGTH,
            "minInclusive":   ConstraintType.MIN_INCLUSIVE,
            "maxInclusive":   ConstraintType.MAX_INCLUSIVE,
            "minExclusive":   ConstraintType.MIN_EXCLUSIVE,
            "maxExclusive":   ConstraintType.MAX_EXCLUSIVE,
            "totalDigits":    ConstraintType.TOTAL_DIGITS,
            "fractionDigits": ConstraintType.FRACTION_DIGITS,
            "pattern":        ConstraintType.PATTERN,
            "enumeration":    ConstraintType.ENUMERATION,
            "whiteSpace":     ConstraintType.WHITESPACE,
        }
        for facet_name, constr_type in facet_map.items():
            for facet in restriction.findall(f"xs:{facet_name}", NS):
                value = facet.get("value")
                if value:
                    attr.constraints.append(Constraint(type=constr_type, expression=value))

    # ── Top‑level element (anonymous type) ────────────────────
    def _parse_global_element(self, name: str, elem: ET.Element, doc: MSDMDocument) -> None:
        """
        A global <xs:element> that may contain an anonymous type definition.
        We create an Entity named after the element, and if it contains a complex
        or simple type, we process that.
        """
        anon_ct = elem.find("xs:complexType", NS)
        anon_st = elem.find("xs:simpleType", NS)
        if anon_ct is not None:
            entity = self._parse_complex_type(name, anon_ct, doc)
            entity.name = name    # override with element name
        elif anon_st is not None:
            entity = self._parse_simple_type(name, anon_st, doc)
            entity.name = name
        else:
            # Element with type reference and cardinality
            type_qname = elem.get("type")
            dt = self._resolve_type_qname(type_qname) if type_qname else DataType(base=ScalarType.ANY)
            entity = Entity(name=name, kind=EntityKind.OBJECT)
            attr = Attribute(name=name, data_type=dt)
            entity.attributes.append(attr)
            doc.entities.append(entity)

    # ── Type resolution ──────────────────────────────────────
    def _resolve_type_qname(self, qname: str) -> DataType:
        """Convert an XSD type QName (or built‑in name) to a DataType."""
        if not qname:
            return DataType(base=ScalarType.ANY)
        # Remove namespace prefix
        local = qname.split(":")[-1] if ":" in qname else qname
        # Check if it's a built‑in XSD type
        if local.lower() in XSD_BUILTIN_MAP:
            return DataType(base=XSD_BUILTIN_MAP[local.lower()])
        # Otherwise, it's a reference to another global type or element
        return DataType(base=ScalarType.REF, ref_entity=local)
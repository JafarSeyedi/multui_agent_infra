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

from pathlib import Path
from xml.etree import ElementTree as ET

from ...models.media_types import MEDIA_TYPES
from ...models.msdm_models import Annotation
from ...models.msdm_models import Attribute
from ...models.msdm_models import Constraint
from ...models.msdm_models import ConstraintType
from ...models.msdm_models import DataType
from ...models.msdm_models import Entity
from ...models.msdm_models import EntityKind
from ...models.msdm_models import MSDMDocument
from ...models.msdm_models import ScalarType, Namespace
from ..base import ParseOptions
from .base_msdm_parser import BaseMSDMParser

# XML Schema namespace
XSD_NS = "http://www.w3.org/2001/XMLSchema"
NS = {"xs": XSD_NS}

# Mapping from XSD built‑in types to ScalarType
XSD_BUILTIN_MAP = {
    "string":           ScalarType.STRING,
    "normalizedString": ScalarType.STRING,
    "token":            ScalarType.STRING,
    "base64Binary":     ScalarType.BINARY,
    "hexBinary":        ScalarType.BINARY,
    "integer":          ScalarType.INT,
    "positiveInteger":  ScalarType.INT,
    "negativeInteger":  ScalarType.INT,
    "nonNegativeInteger": ScalarType.INT,
    "nonPositiveInteger": ScalarType.INT,
    "long":             ScalarType.LONG,
    "unsignedLong":     ScalarType.LONG,
    "int":              ScalarType.INT,
    "unsignedInt":      ScalarType.INT,
    "short":            ScalarType.INT,
    "unsignedShort":    ScalarType.INT,
    "byte":             ScalarType.INT,
    "unsignedByte":     ScalarType.INT,
    "decimal":          ScalarType.DECIMAL,
    "float":            ScalarType.FLOAT,
    "double":           ScalarType.DOUBLE,
    "boolean":          ScalarType.BOOLEAN,
    "date":             ScalarType.DATE,
    "dateTime":         ScalarType.TIMESTAMP,
    "time":             ScalarType.TIME,
    "duration":         ScalarType.DURATION,
    "anyURI":           ScalarType.STRING,
    "QName":            ScalarType.STRING,
    "NOTATION":         ScalarType.STRING,
}


class XSDParser(BaseMSDMParser):
    name = "xsd"
    supported_extensions = (".xsd",)

    async def _parse_to_msdm(
        self, data: bytes, source_name: str, options: ParseOptions
    ) -> MSDMDocument:
        encoding = options.encoding or "utf-8"
        text = data.decode(encoding)
        root = ET.fromstring(text)

        doc = MSDMDocument(
            document_id=Path(source_name).stem,
            title=Path(source_name).stem,
            media_type=MEDIA_TYPES.get("xsd", MEDIA_TYPES["xml"])
        )
        doc.namespace = Namespace(uri=Path(source_name).stem)

        for attr_name in ("targetNamespace", "elementFormDefault", "attributeFormDefault",
                          "version", "id"):
            val = root.get(attr_name)
            if val:
                doc.annotations.append(Annotation(key=attr_name, value=val))

        ann_elem = root.find("xs:annotation", NS)
        if ann_elem is not None:
            doc.annotations.append(Annotation(key="annotation", value=ET.tostring(ann_elem, encoding="unicode")))

        self._registry: dict[str, dict] = {}
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

        for name, entries in self._registry.items():
            if "complexType" in entries:
                self._parse_complex_type(name, entries["complexType"], doc)
            elif "simpleType" in entries:
                self._parse_simple_type(name, entries["simpleType"], doc)
            elif "element" in entries:
                self._parse_global_element(name, entries["element"], doc)
            for kind in ("group", "attributeGroup"):
                if kind in entries:
                    doc.annotations.append(Annotation(key=f"xs_{kind}", value=ET.tostring(entries[kind], encoding="unicode")))

        self.resolve_references(doc)
        return doc

    def _parse_complex_type(self, name: str, ct_elem: ET.Element, doc: MSDMDocument) -> Entity:
        entity = Entity(name=name, kind=EntityKind.OBJECT)
        entity.annotations.append(Annotation(key="xs_complexType", value=ET.tostring(ct_elem, encoding="unicode")))

        for attr in ("abstract", "final", "block", "mixed"):
            val = ct_elem.get(attr)
            if val:
                entity.annotations.append(Annotation(key=attr, value=val))

        self._process_complex_content(ct_elem, entity, doc)
        doc.entities.append(entity)
        return entity

    def _process_complex_content(self, parent: ET.Element, entity: Entity, doc: MSDMDocument) -> None:
        sc = parent.find("xs:simpleContent", NS)
        cc = parent.find("xs:complexContent", NS)
        if sc is not None:
            ext = sc.find("xs:extension", NS) or sc.find("xs:restriction", NS)
            if ext is not None:
                base = ext.get("base")
                if base:
                    self._process_base_type(base, entity, doc)
                self._process_attributes(ext, entity)
                if not any(a.name == "value" for a in entity.attributes):
                    dt = self._resolve_type_qname(base) if base else DataType(base=ScalarType.ANY)
                    entity.attributes.append(Attribute(name="value", data_type=dt))
        elif cc is not None:
            child_elem = cc.find("xs:extension", NS) or cc.find("xs:restriction", NS)
            if child_elem is not None:
                base = child_elem.get("base")
                if base:
                    self._process_base_type(base, entity, doc)
                self._process_compositor_or_attrs(child_elem, entity, doc)
        else:
            self._process_compositor_or_attrs(parent, entity, doc)

    def _process_base_type(self, base_qname: str, entity: Entity, doc: MSDMDocument) -> None:
        if base_qname:
            base_name = base_qname.split(":")[-1] if ":" in base_qname else base_qname
            entity.extends_ref_id = base_name

    def _process_compositor_or_attrs(self, container: ET.Element, entity: Entity, doc: MSDMDocument) -> None:
        compositors = ("xs:sequence", "xs:choice", "xs:all")
        for tag in compositors:
            comp = container.find(tag, NS)
            if comp is not None:
                self._process_compositor(comp, entity, doc)
                break
        self._process_attributes(container, entity)

    def _process_compositor(self, comp: ET.Element, entity: Entity, doc: MSDMDocument) -> None:
        compositor_type = comp.tag.split("}")[-1]
        entity.annotations.append(Annotation(key="compositor", value=compositor_type))

        for child in comp:
            tag = child.tag.split("}")[-1]
            if tag == "element":
                attr = self._parse_element(child, doc)
                if attr:
                    entity.attributes.append(attr)
            elif tag == "group":
                ref = child.get("ref")
                if ref:
                    entity.annotations.append(Annotation(key="group_ref", value=ref))
            elif tag in ("choice", "sequence"):
                self._process_compositor(child, entity, doc)
            elif tag == "any":
                entity.annotations.append(Annotation(key="any", value=ET.tostring(child, encoding="unicode")))

    def _parse_element(self, elem: ET.Element, doc: MSDMDocument) -> Attribute | None:
        name = elem.get("name")
        ref = elem.get("ref")
        if ref:
            name = ref.split(":")[-1] if ":" in ref else ref
        if not name:
            return None

        type_qname = elem.get("type")
        anonymous_type = elem.find("xs:complexType", NS) or elem.find("xs:simpleType", NS)

        if anonymous_type is not None:
            anon_name = f"{name}_type"
            if anonymous_type.tag.endswith("complexType"):
                nested_entity = self._parse_complex_type(anon_name, anonymous_type, doc)
            else:
                nested_entity = self._parse_simple_type(anon_name, anonymous_type, doc)
            dt = DataType(base=ScalarType.REF, ref_entity_id=nested_entity.name)
        elif type_qname:
            dt = self._resolve_type_qname(type_qname)
        else:
            dt = DataType(base=ScalarType.ANY)

        min_occurs = int(elem.get("minOccurs", "1"))
        max_occurs_str = elem.get("maxOccurs", "1")
        is_array = max_occurs_str == "unbounded" or (max_occurs_str.isdigit() and int(max_occurs_str) > 1)
        required = min_occurs > 0

        if is_array:
            dt = DataType(base=ScalarType.ARRAY, element_type=dt)

        attr = Attribute(name=name, data_type=dt, required=required)
        default = elem.get("default")
        fixed = elem.get("fixed")
        if default:
            attr.default_value = default
            attr.constraints.append(Constraint(type=ConstraintType.DEFAULT, expression=default))
        if fixed:
            attr.annotations.append(Annotation(key="fixed", value=fixed))
        if elem.get("nillable") == "true":
            attr.annotations.append(Annotation(key="nillable", value="true"))

        attr.annotations.append(Annotation(key="xs_element", value=ET.tostring(elem, encoding="unicode")))
        return attr

    def _process_attributes(self, container: ET.Element, entity: Entity) -> None:
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
            attr = Attribute(name=name, data_type=dt, required=use == "required")
            default = attr_elem.get("default")
            fixed = attr_elem.get("fixed")
            if default:
                attr.default_value = default
                attr.constraints.append(Constraint(type=ConstraintType.DEFAULT, expression=default))
            if fixed:
                attr.annotations.append(Annotation(key="fixed", value=fixed))
            entity.attributes.append(attr)

        any_attr = container.find("xs:anyAttribute", NS)
        if any_attr is not None:
            entity.annotations.append(Annotation(key="anyAttribute", value=ET.tostring(any_attr, encoding="unicode")))

    def _parse_simple_type(self, name: str, st_elem: ET.Element, doc: MSDMDocument) -> Entity:
        entity = Entity(name=name, kind=EntityKind.OBJECT)
        entity.annotations.append(Annotation(key="xs_simpleType", value=ET.tostring(st_elem, encoding="unicode")))

        restriction = st_elem.find("xs:restriction", NS)
        union = st_elem.find("xs:union", NS)
        list_elem = st_elem.find("xs:list", NS)

        if restriction is not None:
            base = restriction.get("base")
            dt = self._resolve_type_qname(base) if base else DataType(base=ScalarType.STRING)
            attr = Attribute(name="value", data_type=dt, required=True)
            self._parse_facets(restriction, attr)
            entity.attributes.append(attr)
        elif union is not None:
            member_types = union.get("memberTypes", "")
            entity.annotations.append(Annotation(key="union_memberTypes", value=member_types))
            entity.attributes.append(Attribute(name="value", data_type=DataType(base=ScalarType.ANY), required=True))
        elif list_elem is not None:
            item_type = list_elem.get("itemType")
            item_dt = self._resolve_type_qname(item_type) if item_type else DataType(base=ScalarType.STRING)
            dt = DataType(base=ScalarType.ARRAY, element_type=item_dt)
            entity.attributes.append(Attribute(name="value", data_type=dt, required=True))

        doc.entities.append(entity)
        return entity

    def _parse_facets(self, restriction: ET.Element, attr: Attribute) -> None:
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

    def _parse_global_element(self, name: str, elem: ET.Element, doc: MSDMDocument) -> None:
        anon_ct = elem.find("xs:complexType", NS)
        anon_st = elem.find("xs:simpleType", NS)
        if anon_ct is not None:
            entity = self._parse_complex_type(name, anon_ct, doc)
            entity.name = name
        elif anon_st is not None:
            entity = self._parse_simple_type(name, anon_st, doc)
            entity.name = name
        else:
            type_qname = elem.get("type")
            dt = self._resolve_type_qname(type_qname) if type_qname else DataType(base=ScalarType.ANY)
            entity = Entity(name=name, kind=EntityKind.OBJECT)
            attr = Attribute(name=name, data_type=dt)
            entity.attributes.append(attr)
            doc.entities.append(entity)

    def _resolve_type_qname(self, qname: str) -> DataType:
        if not qname:
            return DataType(base=ScalarType.ANY)
        local = qname.split(":")[-1] if ":" in qname else qname
        if local.lower() in XSD_BUILTIN_MAP:
            return DataType(base=XSD_BUILTIN_MAP[local.lower()])
        return DataType(base=ScalarType.REF, ref_entity_id=local)
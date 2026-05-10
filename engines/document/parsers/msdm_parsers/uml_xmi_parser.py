# engines/document/parsers/msdm_parsers/uml_xmi_parser.py
"""
UML XMI Parser – converts .xmi / .uml files into an MSDMDocument.

================================================================================
COMPLETE MAPPING DECISIONS (final, approved)
================================================================================

1. UML Class / Interface / DataType / PrimitiveType
   → MSDM Entity (kind=OBJECT). Interface flag stored in is_interface.

2. UML Enumeration
   → NOT CREATED AS SEPARATE ENTITY.
   → Enum literals are collected and later attached as a CHECK constraint
     on any attribute whose type references that enumeration.
   → The attribute's data type is set to ScalarType.STRING.

3. UML ownedAttribute (property)
   → MSDM Attribute.
   → Multiplicity bounds (lowerValue/upperValue) mapped to Cardinality enum
     and to the 'required' flag.
   → Default value mapped to Constraint(type=DEFAULT).
   → Visibility, isStatic, isDerived mapped to corresponding Attribute fields.
   → Type reference stored in DataType.ref_entity_id (resolved in second pass).

4. UML ownedOperation (method/operation)
   → COMPLETELY IGNORED. No Attribute created. No output.

5. UML Association
   → MSDM EntityRelationship.
   → Ends (ownedEnd) provide type references (stored in from_ref_id / to_ref_id),
     multiplicities (mapped to Cardinality), and role names.
   → Role names stored as allowed annotations (from_role, to_role).

6. UML Generalization
   → MSDM Entity.extends_ref_id (temporary string), resolved later.

7. UML Stereotype (applied to Class, Attribute, Association)
   → Stored as allowed annotation (key="stereotype_ref", value=ref).

8. XMI ID (xmi:id)
   → Stored as allowed annotation (key="xmi_id", value=id) on Entity and EntityRelationship.

9. No other annotations are allowed or stored.

10. Reference resolution:
    → Uses the base class method resolve_references() which resolves
      extends_ref_id, from_ref_id, to_ref_id, ref_entity_id, etc.

11. Cardinality mapping (UML bounds → Cardinality enum):
    - "1"               → ONE
    - "0..1"            → ZERO_OR_ONE
    - "1..*"            → ONE_OR_MANY
    - "*", "0..*", "n"  → MANY
    - Other numeric ranges → MANY or ONE heuristically.

================================================================================
All original parsing capabilities except operations and separate enum entities.
================================================================================
"""
from __future__ import annotations

from pathlib import Path
from xml.etree import ElementTree as ET
from typing import Any

from ...models.media_types import MEDIA_TYPES
from ...models.msdm_models import (
    Annotation, Attribute, Cardinality, Constraint, ConstraintType, DataType,
    Entity, EntityKind, MSDMDocument, Namespace, EntityRelationship, ScalarType, VisibilityKind
)
from ..base import ParseOptions
from .base_msdm_parser import BaseMSDMParser

NS_UML = "http://www.omg.org/spec/UML/20131001"
NS_XMI = "http://www.omg.org/spec/XMI/20131001"
NS_XSI = "http://www.w3.org/2001/XMLSchema-instance"
NS_ALL = {"uml": NS_UML, "xmi": NS_XMI, "xsi": NS_XSI}


class UMLXmiParser(BaseMSDMParser):
    name = "uml_xmi"
    supported_extensions = (".xmi", ".uml")

    async def _parse_to_msdm(
        self, data: bytes, source_name: str, options: ParseOptions
    ) -> MSDMDocument:
        encoding = options.encoding or "utf-8"
        text = data.decode(encoding)
        root = ET.fromstring(text)

        doc = MSDMDocument(
            document_id=Path(source_name).stem,
            title=Path(source_name).stem,
            media_type=MEDIA_TYPES.get("uml_xmi", MEDIA_TYPES["xml"])
        )
        doc.namespace = Namespace(uri=Path(source_name).stem)

        ns = root.tag.split("}")[0][1:] if root.tag.startswith("{") else ""
        if ns:
            NS_ALL["uml"] = ns
        self._ns = ns

        # Temporary storage
        self._entity_map: dict[str, Entity] = {}
        self._class_names: dict[str, str] = {}
        self._class_elements: list[ET.Element] = []
        self._association_elements: list[ET.Element] = []
        self._generalizations: list[ET.Element] = []
        self._enum_map: dict[str, list[str]] = {}  # xmi_id -> list of literal names

        self._collect_elements(root, "")

        # First pass: parse classes (skip enumerations)
        for elem in self._class_elements:
            self._parse_class(elem, doc)

        # Parse generalizations (store refs)
        for gen_elem in self._generalizations:
            self._parse_generalization(gen_elem, doc)

        # Parse associations
        for assoc_elem in self._association_elements:
            self._parse_association(assoc_elem, doc)

        # Second pass: resolve all references using base method
        self.resolve_references(doc)

        return doc

    def _collect_elements(self, parent: ET.Element, qualified_name_prefix: str) -> None:
        for child in parent:
            tag = child.tag.split("}")[-1]
            if tag == "packagedElement":
                xmi_type = child.get(f"{{{NS_XMI}}}type", "")
                if not xmi_type:
                    local = child.tag.split("}")[-1] if "}" in child.tag else child.tag
                    if local in ("Class", "Interface", "DataType", "PrimitiveType", "Enumeration", "Association", "Generalization"):
                        xmi_type = "uml:" + local
                # Class-like elements (including DataType, PrimitiveType) go to class list
                if xmi_type in ("uml:Class", "uml:Interface", "uml:DataType", "uml:PrimitiveType"):
                    self._class_elements.append(child)
                elif xmi_type == "uml:Enumeration":
                    self._collect_enum_literals(child)
                elif xmi_type == "uml:Association":
                    self._association_elements.append(child)
                elif xmi_type == "uml:Generalization":
                    self._generalizations.append(child)
                elif xmi_type == "uml:Package":
                    name = child.get("name", "")
                    new_prefix = f"{qualified_name_prefix}{name}::" if qualified_name_prefix else f"{name}::"
                    self._collect_elements(child, new_prefix)

    def _collect_enum_literals(self, enum_elem: ET.Element) -> None:
        xmi_id = enum_elem.get(f"{{{NS_XMI}}}id", enum_elem.get("id", ""))
        if not xmi_id:
            return
        literals = []
        for lit in enum_elem.findall("uml:ownedLiteral", NS_ALL):
            lit_name = lit.get("name", "")
            if lit_name:
                literals.append(lit_name)
        if literals:
            self._enum_map[xmi_id] = literals

    def _parse_class(self, elem: ET.Element, doc: MSDMDocument) -> Entity | None:
        xmi_id = elem.get(f"{{{NS_XMI}}}id", elem.get("id", ""))
        name = elem.get("name", "anonymous")
        xmi_type = elem.get(f"{{{NS_XMI}}}type", "")
        if not xmi_type:
            local = elem.tag.split("}")[-1]
            xmi_type = "uml:" + local

        # Skip enumeration (already handled separately)
        if xmi_type == "uml:Enumeration":
            return None

        is_interface = xmi_type == "uml:Interface"

        entity = Entity(name=name, kind=EntityKind.OBJECT)
        if xmi_id:
            entity.annotations.append(Annotation(key="xmi_id", value=xmi_id))
        entity.is_interface = is_interface
        entity.is_abstract = elem.get("isAbstract", "false").lower() == "true"
        self._extract_stereotypes(elem, entity)

        # Parse owned attributes
        for attr_elem in elem.findall("uml:ownedAttribute", NS_ALL):
            if self._is_association_end(attr_elem):
                continue
            attr = self._parse_attribute(attr_elem)
            if attr:
                entity.attributes.append(attr)

        # ownedOperation elements are completely ignored

        doc.entities.append(entity)
        self._entity_map[xmi_id] = entity
        self._class_names[name] = xmi_id
        return entity

    def _is_association_end(self, attr_elem: ET.Element) -> bool:
        return attr_elem.get("association") is not None

    def _parse_attribute(self, attr_elem: ET.Element) -> Attribute | None:
        name = attr_elem.get("name", "")
        if not name:
            return None

        visibility = attr_elem.get("visibility")
        is_static = attr_elem.get("isStatic", "false").lower() == "true"
        is_derived = attr_elem.get("isDerived", "false").lower() == "true"
        type_ref = attr_elem.get("type")

        dt = self._resolve_type(attr_elem)

        attr = Attribute(name=name, data_type=dt)
        attr.is_static = is_static
        attr.is_derived = is_derived
        if visibility:
            vis_map = {"+": VisibilityKind.PUBLIC, "-": VisibilityKind.PRIVATE,
                       "#": VisibilityKind.PROTECTED, "~": VisibilityKind.PACKAGE}
            attr.visibility = vis_map.get(visibility)

        # Multiplicity
        lower = self._get_bound(attr_elem, "lowerValue")
        upper = self._get_bound(attr_elem, "upperValue")
        if upper == "1":
            attr.required = True
        elif upper == "*" or (upper and upper.isdigit() and int(upper) > 1):
            attr.required = False
        if lower and lower != "0":
            attr.required = True

        # Default value
        default_elem = attr_elem.find("uml:defaultValue", NS_ALL)
        if default_elem is not None:
            val = default_elem.get("value", default_elem.text)
            if val:
                attr.default_value = val
                attr.constraints.append(Constraint(type=ConstraintType.DEFAULT, expression=val))

        # Enumeration handling: if type_ref points to an enumeration we collected,
        # replace data type with STRING and add CHECK constraint.
        if type_ref and type_ref in self._enum_map:
            literals = self._enum_map[type_ref]
            if literals:
                quoted = ", ".join(repr(v) for v in literals)
                check_expr = f"IN ({quoted})"
                attr.constraints.append(Constraint(type=ConstraintType.CHECK, expression=check_expr))
                attr.data_type = DataType(base=ScalarType.STRING)

        self._extract_stereotypes(attr_elem, attr)
        return attr

    def _resolve_type(self, elem: ET.Element) -> DataType:
        type_ref = elem.get("type")
        if type_ref:
            return DataType(base=ScalarType.REF, ref_entity_id=type_ref)
        return DataType(base=ScalarType.ANY)

    def _get_bound(self, elem: ET.Element, tag: str) -> str | None:
        bound_elem = elem.find(f"uml:{tag}", NS_ALL)
        if bound_elem is not None:
            val = bound_elem.get("value")
            if val is not None:
                return val
            type_ref = bound_elem.get(f"{{{NS_XMI}}}type")
            if type_ref and "LiteralString" in type_ref:
                return bound_elem.get("value")
        return None

    def _extract_stereotypes(self, elem: ET.Element, target: Any) -> None:
        for child in elem:
            tag = child.tag.split("}")[-1]
            if tag == "stereotype":
                ref = child.get(f"{{{NS_XMI}}}idref") or child.get("href", "")
                if ref:
                    target.annotations.append(Annotation(key="stereotype_ref", value=ref))
            # Extensions ignored

    def _parse_generalization(self, gen_elem: ET.Element, doc: MSDMDocument) -> None:
        specific_ref = gen_elem.get("specific")
        general_ref = gen_elem.get("general")
        if specific_ref and general_ref and specific_ref in self._entity_map:
            self._entity_map[specific_ref].extends_ref_id = general_ref

    def _parse_association(self, assoc_elem: ET.Element, doc: MSDMDocument) -> None:
        name = assoc_elem.get("name")
        member_end_refs = assoc_elem.get("memberEnd", "")
        owned_ends = assoc_elem.findall("uml:ownedEnd", NS_ALL)

        end_ids = member_end_refs.split() if member_end_refs else []
        if len(end_ids) < 2 and len(owned_ends) >= 2:
            end1 = owned_ends[0]
            end2 = owned_ends[1]
            self._create_relationship_from_ends(end1, end2, name, assoc_elem, doc)
        elif len(end_ids) >= 2:
            end_elems = []
            for rid in end_ids:
                found = None
                for child in assoc_elem:
                    if child.get(f"{{{NS_XMI}}}id") == rid or child.get("id") == rid:
                        found = child
                        break
                if found:
                    end_elems.append(found)
            if len(end_elems) >= 2:
                self._create_relationship_from_ends(end_elems[0], end_elems[1], name, assoc_elem, doc)

    def _create_relationship_from_ends(self, end1: ET.Element, end2: ET.Element,
                                      assoc_name: str | None, assoc_elem: ET.Element,
                                      doc: MSDMDocument) -> None:
        def get_class_ref(end: ET.Element) -> str | None:
            return end.get("type")

        from_id = get_class_ref(end1)
        to_id = get_class_ref(end2)
        if not from_id or not to_id:
            return

        mult_from = self._get_bound(end1, "upperValue") or "1"
        mult_to = self._get_bound(end2, "upperValue") or "1"
        card_from = self._to_card(mult_from)
        card_to = self._to_card(mult_to)

        role_from = end1.get("name")
        role_to = end2.get("name")

        rel = EntityRelationship(
            name=assoc_name,
            from_entity=None,
            to_entity=None,
            cardinality_from=card_from,
            cardinality_to=card_to,
            description=assoc_elem.get("documentation", ""),
        )
        rel.from_ref_id = from_id
        rel.to_ref_id = to_id
        if role_from:
            rel.annotations.append(Annotation(key="from_role", value=role_from))
        if role_to:
            rel.annotations.append(Annotation(key="to_role", value=role_to))

        self._extract_stereotypes(assoc_elem, rel)
        doc.relationships.append(rel)

    def _to_card(self, mult: str) -> Cardinality:
        mult = mult.strip()
        if mult == "1":
            return Cardinality.ONE
        if mult in ("*", "n", "0..*"):
            return Cardinality.MANY
        if mult == "0..1":
            return Cardinality.ZERO_OR_ONE
        if mult == "1..*":
            return Cardinality.ONE_OR_MANY
        if ".." in mult:
            parts = mult.split("..")
            lower = parts[0].strip()
            upper = parts[1].strip()
            if lower == "0" and upper == "1":
                return Cardinality.ZERO_OR_ONE
            if lower == "1" and upper == "1":
                return Cardinality.ONE
            if lower == "1" and (upper == "*" or upper == "n"):
                return Cardinality.ONE_OR_MANY
            if lower == "0" and (upper == "*" or upper == "n"):
                return Cardinality.MANY
        if mult.isdigit():
            return Cardinality.ONE if mult == "1" else Cardinality.MANY
        return Cardinality.ONE
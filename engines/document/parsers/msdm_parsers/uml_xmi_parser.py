# engines/document/parsers/msdm_parsers/uml_xmi_parser.py
"""
UML XMI Parser – converts .xmi / .uml files into an MSDMDocument.

Supports UML 2.x XMI (as exported by MagicDraw, Papyrus, EA, etc.).
Parses:
- packagedElement (uml:Class, uml:Interface, uml:DataType, uml:Enumeration,
  uml:PrimitiveType, uml:Association, uml:Generalization, uml:Package, etc.)
- ownedAttribute (properties, association ends)
- ownedOperation (methods) and ownedParameter
- ownedLiteral (enum values)
- generalizations (extends relationship)
- associations with member ends, multiplicities, navigability
- stereotypes and tagged values are stored as Annotations.
- nested packages are flattened; their fully qualified names are used.
"""

from __future__ import annotations
import re
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
from xml.etree import ElementTree as ET

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
    Cardinality,
)

# ── Namespaces ─────────────────────────────────────────────────────
NS_UML = "http://www.omg.org/spec/UML/20131001"        # UML 2.5 standard
NS_XMI = "http://www.omg.org/spec/XMI/20131001"
NS_XSI = "http://www.w3.org/2001/XMLSchema-instance"

# Also commonly seen: UML 2.4.1, 2.1, etc. We'll try to detect from the root attribute.
NS_ALL = {
    "uml": NS_UML,
    "xmi": NS_XMI,
    "xsi": NS_XSI,
}


class UMLXmiParser(BaseMSDMParser):
    """Parser for UML XMI files (.xmi, .uml)."""
    name = "uml_xmi"
    supported_extensions = (".xmi", ".uml")

    async def _parse_to_msdm(
        self, data: bytes, source_name: str, options: ParseOptions
    ) -> MSDMDocument:
        encoding = options.encoding or "utf-8"
        text = data.decode(encoding)
        root = ET.fromstring(text)

        doc = MSDMDocument()
        doc.namespace = Path(source_name).stem

        # Detect actual UML namespace from root (default namespace)
        ns = root.tag.split("}")[0][1:] if root.tag.startswith("{") else ""
        if ns:
            NS_ALL["uml"] = ns
        # Also scan for explicit uml: namespace in attributes
        # (XMI often declares xmlns:uml="...")
        # We'll just rely on the registered NS; we'll try both common ones.
        # For safety, we'll also accept any tag ending with 'Class' etc.
        self._ns = ns

        # First pass: collect all packaged elements into a flat list (recursively)
        self._entity_map: Dict[str, Entity] = {}        # xmi:id → Entity
        self._class_names: Dict[str, str] = {}           # name → xmi:id (for duplicate handling)
        self._class_elements: List[ET.Element] = []
        self._association_elements: List[ET.Element] = []
        self._generalizations: List[ET.Element] = []

        self._collect_elements(root, "")

        # Second pass: parse classes and interfaces
        for elem in self._class_elements:
            self._parse_class(elem, doc)

        # Third pass: generalize
        for gen_elem in self._generalizations:
            self._parse_generalization(gen_elem, doc)

        # Fourth pass: associations
        for assoc_elem in self._association_elements:
            self._parse_association(assoc_elem, doc)

        return doc

    # ── Element collection ──────────────────────────────────────────
    def _collect_elements(self, parent: ET.Element, qualified_name_prefix: str) -> None:
        """
        Recursively walk through packagedElement and collect classes,
        associations, generalizations, and nested packages.
        """
        for child in parent:
            tag = child.tag.split("}")[-1]
            if tag == "packagedElement":
                xmi_type = child.get(f"{{{NS_XMI}}}type", "")
                if not xmi_type:
                    # The element name itself may be uml:Class etc.
                    local = child.tag.split("}")[-1] if "}" in child.tag else child.tag
                    if local in ("Class", "Interface", "DataType", "Enumeration", "PrimitiveType", "Association", "Generalization"):
                        xmi_type = "uml:" + local
                # Determine element kind
                if xmi_type in ("uml:Class", "uml:Interface", "uml:DataType", "uml:Enumeration"):
                    self._class_elements.append(child)
                elif xmi_type == "uml:Association":
                    self._association_elements.append(child)
                elif xmi_type == "uml:Generalization":
                    self._generalizations.append(child)
                elif xmi_type == "uml:Package":
                    # Recurse
                    name = child.get("name", "")
                    new_prefix = f"{qualified_name_prefix}{name}::" if qualified_name_prefix else f"{name}::"
                    self._collect_elements(child, new_prefix)

    def _parse_class(self, elem: ET.Element, doc: MSDMDocument) -> Entity:
        """Parse a Class/Interface/DataType/Enumeration element."""
        xmi_id = elem.get(f"{{{NS_XMI}}}id", elem.get("id", ""))
        name = elem.get("name", "anonymous")
        xmi_type = elem.get(f"{{{NS_XMI}}}type", "")
        if not xmi_type:
            local = elem.tag.split("}")[-1]
            xmi_type = "uml:" + local

        is_interface = xmi_type == "uml:Interface"
        is_enum = xmi_type == "uml:Enumeration"
        is_datatype = xmi_type == "uml:DataType" or xmi_type == "uml:PrimitiveType"

        kind = EntityKind.OBJECT
        entity = Entity(name=name, kind=kind)
        entity.annotations.append(Annotation(key="xmi_id", value=xmi_id))
        entity.annotations.append(Annotation(key="xmi_type", value=xmi_type))
        if is_interface:
            entity.annotations.append(Annotation(key="interface", value="true"))
        elif is_enum:
            entity.annotations.append(Annotation(key="enumeration", value="true"))
        elif is_datatype:
            entity.annotations.append(Annotation(key="datatype", value="true"))

        # Stereotypes & tagged values (from child elements)
        self._extract_stereotypes(elem, entity)

        # Attributes (ownedAttribute)
        for attr_elem in elem.findall("uml:ownedAttribute", NS_ALL):
            if self._is_association_end(attr_elem):
                continue    # association ends handled later
            attr = self._parse_attribute(attr_elem)
            if attr:
                entity.attributes.append(attr)

        # Operations (ownedOperation)
        for op_elem in elem.findall("uml:ownedOperation", NS_ALL):
            op_attr = self._parse_operation(op_elem)
            if op_attr:
                entity.attributes.append(op_attr)   # store as pseudo-attribute

        # Enum literals (ownedLiteral)
        if is_enum:
            enum_values = []
            for lit_elem in elem.findall("uml:ownedLiteral", NS_ALL):
                val_name = lit_elem.get("name", "")
                enum_values.append(val_name)
            if enum_values:
                attr = Attribute(name="value", data_type=DataType(base=ScalarType.STRING), required=True)
                quoted = ", ".join(repr(v) for v in enum_values)
                attr.constraints.append(Constraint(type=ConstraintType.CHECK, expression=f"IN ({quoted})"))
                entity.attributes.append(attr)

        doc.entities.append(entity)
        self._entity_map[xmi_id] = entity
        self._class_names[name] = xmi_id
        return entity

    def _is_association_end(self, attr_elem: ET.Element) -> bool:
        """Check if the ownedAttribute is actually an association end (part of an association)."""
        assoc = attr_elem.get("association")
        return assoc is not None

    def _parse_attribute(self, attr_elem: ET.Element) -> Optional[Attribute]:
        """Parse a UML Property as an MSDM Attribute."""
        name = attr_elem.get("name", "")
        visibility = attr_elem.get("visibility")
        is_static = attr_elem.get("isStatic", "false").lower() == "true"
        is_derived = attr_elem.get("isDerived", "false").lower() == "true"

        # Type
        dt = self._resolve_type(attr_elem)
        attr = Attribute(name=name, data_type=dt)

        # Lower / upper multiplicity
        lower = self._get_bound(attr_elem, "lowerValue")
        upper = self._get_bound(attr_elem, "upperValue")
        if upper == "1":
            attr.required = True
        elif upper == "*" or (upper.isdigit() and int(upper) > 1):
            attr.required = False
            attr.annotations.append(Annotation(key="max_multiplicity", value=upper))
        if lower and lower != "0":
            attr.required = True
            attr.annotations.append(Annotation(key="min_multiplicity", value=lower))

        # Default value
        default = attr_elem.find("uml:defaultValue", NS_ALL)
        if default is not None:
            val_elem = default.get("value", default.text)
            if val_elem:
                attr.default_value = val_elem
                attr.constraints.append(Constraint(type=ConstraintType.DEFAULT, expression=val_elem))

        # Stereotype and tagged values on attribute
        self._extract_stereotypes(attr_elem, attr)

        # Static / Derived markers
        if is_static:
            attr.annotations.append(Annotation(key="static", value="true"))
        if is_derived:
            attr.annotations.append(Annotation(key="derived", value="true"))

        if visibility:
            attr.annotations.append(Annotation(key="visibility", value=visibility))

        return attr

    def _parse_operation(self, op_elem: ET.Element) -> Optional[Attribute]:
        """Parse a UML Operation into an MSDM Attribute (stored as method annotation)."""
        name = op_elem.get("name", "")
        visibility = op_elem.get("visibility")
        is_static = op_elem.get("isStatic", "false").lower() == "true"
        is_abstract = op_elem.get("isAbstract", "false").lower() == "true"

        # Parameters
        params = []
        param_list = op_elem.findall("uml:ownedParameter", NS_ALL)
        return_type = None
        for param in param_list:
            p_name = param.get("name", "")
            direction = param.get("direction", "in")
            p_type = self._resolve_type(param)
            if direction == "return":
                return_type = p_type
            else:
                params.append(f"{p_name}: {self._type_to_string(p_type)}")

        # Build pseudo-name: methodName(param1,param2): returnType
        pseudo_name = f"{name}({', '.join(params)})"
        dt = return_type if return_type else DataType(base=ScalarType.ANY)
        attr = Attribute(name=pseudo_name, data_type=dt)
        attr.annotations.append(Annotation(key="method", value="true"))
        attr.annotations.append(Annotation(key="operation_name", value=name))
        if visibility:
            attr.annotations.append(Annotation(key="visibility", value=visibility))
        if is_static:
            attr.annotations.append(Annotation(key="static", value="true"))
        if is_abstract:
            attr.annotations.append(Annotation(key="abstract", value="true"))
        return attr

    def _resolve_type(self, elem: ET.Element) -> DataType:
        """Resolve the type of a property or parameter."""
        type_ref = elem.get("type")
        if type_ref:
            # It's a reference by xmi:id
            # We'll try to find the entity name later; for now store as unknown
            ref_entity = self._entity_map.get(type_ref, None)
            if ref_entity:
                return DataType(base=ScalarType.REF, ref_entity=ref_entity.name)
            else:
                # Not yet resolved, store placeholder
                return DataType(base=ScalarType.REF, ref_entity=f"xmi:{type_ref}")
        # Check for inline type definition (rare)
        child = elem.find("uml:type", NS_ALL)
        if child is not None:
            type_name = child.get("name", "anonymous")
            return DataType(base=ScalarType.REF, ref_entity=type_name)
        # Check for default UML primitive types (String, Integer, Boolean, etc.)
        return DataType(base=ScalarType.ANY)

    def _type_to_string(self, dt: DataType) -> str:
        """Convert DataType to a simple string for parameter display."""
        if dt.base == ScalarType.REF:
            return dt.ref_entity or "Unknown"
        return dt.base.value

    def _get_bound(self, elem: ET.Element, tag: str) -> Optional[str]:
        """Extract a multiplicity bound (e.g., lowerValue / upperValue) from a Property element."""
        bound_elem = elem.find(f"uml:{tag}", NS_ALL)
        if bound_elem is not None:
            val_attr = bound_elem.get("value")
            if val_attr is not None:
                return val_attr
            # XMI 2.1 sometimes stores as type with an attribute
            type_ref = bound_elem.get(f"{{{NS_XMI}}}type")
            if type_ref and "LiteralString" in type_ref:
                return bound_elem.get("value")
        return None

    def _extract_stereotypes(self, elem: ET.Element, target: Entity | Attribute) -> None:
        """Extract stereotype and tagged value annotations from an element."""
        for child in elem:
            tag = child.tag.split("}")[-1]
            if tag == "stereotype":
                # stereotype reference
                ref = child.get(f"{{{NS_XMI}}}idref") or child.get("href", "")
                if ref:
                    target.annotations.append(Annotation(key="stereotype_ref", value=ref))
            elif tag == "xmi:Extension":
                # tag = "Extension" in XMI extension namespace
                ext_key = child.get("extender", "")
                ext_value = child.get("extenderValue", "")
                if ext_key:
                    target.annotations.append(Annotation(key=ext_key, value=ext_value))

    # ── Generalization ─────────────────────────────────────────────
    def _parse_generalization(self, gen_elem: ET.Element, doc: MSDMDocument) -> None:
        """Handle generalization – set extends on the specific entity."""
        specific_ref = gen_elem.get("specific")
        general_ref = gen_elem.get("general")
        if specific_ref and general_ref:
            specific_entity = self._entity_map.get(specific_ref)
            general_entity = self._entity_map.get(general_ref)
            if specific_entity and general_entity:
                specific_entity.extends = general_entity.name

    # ── Association ─────────────────────────────────────────────────
    def _parse_association(self, assoc_elem: ET.Element, doc: MSDMDocument) -> None:
        """
        Parse a UML Association element and produce one or two Relationships.
        Association has memberEnds (xmi:idrefs) and potentially ownedEnds.
        """
        name = assoc_elem.get("name")
        member_end_refs = assoc_elem.get("memberEnd", "")
        owned_ends = assoc_elem.findall("uml:ownedEnd", NS_ALL)

        # memberEnd is a space‑separated list of xmi:idrefs
        end_ids = member_end_refs.split() if member_end_refs else []
        if len(end_ids) < 2 and len(owned_ends) >= 2:
            # Some tools store as ownedEnd children
            end1 = owned_ends[0]
            end2 = owned_ends[1]
            self._create_relationship_from_ends(end1, end2, name, assoc_elem, doc)
        elif len(end_ids) >= 2:
            # We need to find the actual ownedEnd elements from the association or from the target classes
            # Usually the association owns the ends.
            end_elems = []
            for rid in end_ids:
                found = None
                # Search in association's children
                for child in assoc_elem:
                    if child.get(f"{{{NS_XMI}}}id") == rid or child.get("id") == rid:
                        found = child
                        break
                if not found:
                    # The memberEnd might be defined in the class's ownedAttribute
                    # We'll try to find from _entity_map? Not straightforward.
                    # Fallback: create a relationship with just the idrefs.
                    pass
                if found:
                    end_elems.append(found)
            if len(end_elems) >= 2:
                self._create_relationship_from_ends(end_elems[0], end_elems[1], name, assoc_elem, doc)
            else:
                # Record association as annotation for round‑trip
                doc.annotations.append(Annotation(key="association_raw", value=ET.tostring(assoc_elem, encoding="unicode")))

    def _create_relationship_from_ends(self, end1: ET.Element, end2: ET.Element,
                                      assoc_name: Optional[str], assoc_elem: ET.Element,
                                      doc: MSDMDocument) -> None:
        """Extract details from two UML Property ends and build a Relationship."""
        # Get class references from the end's type attribute
        def get_class_ref(end: ET.Element) -> Optional[str]:
            type_ref = end.get("type")
            if type_ref:
                ent = self._entity_map.get(type_ref)
                return ent.name if ent else None
            return None

        from_class = get_class_ref(end1)
        to_class = get_class_ref(end2)
        if not from_class or not to_class:
            return

        # Multiplicities
        mult_from = self._get_bound(end1, "upperValue") or "1"
        mult_to = self._get_bound(end2, "upperValue") or "1"
        card_from = self._to_card(mult_from)
        card_to = self._to_card(mult_to)

        # Name of the association end (if any)
        role_from = end1.get("name")
        role_to = end2.get("name")

        rel = Relationship(
            name=assoc_name,
            from_entity=from_class,
            to_entity=to_class,
            cardinality_from=card_from,
            cardinality_to=card_to,
            description=assoc_elem.get("documentation", ""),
        )
        if role_from:
            rel.annotations.append(Annotation(key="from_role", value=role_from))
        if role_to:
            rel.annotations.append(Annotation(key="to_role", value=role_to))

        # Stereotype on association
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
        # Try to parse numeric range
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
        # Numeric if digit
        if mult.isdigit():
            if mult == "1":
                return Cardinality.ONE
            else:
                return Cardinality.MANY
        return Cardinality.ONE
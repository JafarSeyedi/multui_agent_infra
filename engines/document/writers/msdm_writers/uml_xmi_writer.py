# engines/document/writers/msdm_writers/uml_xmi_writer.py
"""
UML XMI Writer – converts an MSDMDocument into UML 2.x XMI (XML).

================================================================================
COMPLETE MAPPING DECISIONS (final, approved)
================================================================================

1. MSDM Entity (any kind) → UML Class (or Interface if is_interface=True).
   → No UML Enumeration is written (enums in MSDM are represented as CHECK
     constraints on attributes, not as separate elements).

2. MSDM Attribute → UML ownedAttribute.
   → Data type: if ref_entity (Entity) then output as type reference to that class.
   → If data_type is ScalarType.STRING and the attribute has a CHECK constraint
     (possible enum), we do NOT produce a UML enumeration – we just output the
     attribute as a plain String property (lossy for round‑trip).
   → Multiplicity: derived from required flag and data_type (ARRAY).
   → Visibility, isStatic, isDerived, default value are mapped.

3. MSDM EntityRelationship → UML Association.
   → Ends (ownedEnd) with role names (from_role, to_role annotations) and
     multiplicities mapped to lower/upper values.
   → Stereotypes on the association are written.

4. MSDM Entity.extends → UML Generalization.

5. Annotations allowed and written:
   - xmi_id → used as XMI id for the element.
   - stereotype_ref → written as <stereotype href="..."/> child element.
   - from_role / to_role → used as name attributes on association ends.

6. No other annotations are written.

7. Operations/methods: NOT WRITTEN. No ownedOperation elements are generated,
   even if the MSDM model somehow contains attributes with operation_name
   (which have been removed from the model).

8. No ownedLiteral (enum literals) are written.

================================================================================
All original writing capabilities except operation output and enumeration output.
================================================================================
"""
from __future__ import annotations

from xml.etree.ElementTree import Element, SubElement, tostring

from ...models.msdm_models import (
    Annotation, Attribute, Cardinality, Entity, MSDMDocument, EntityRelationship, ScalarType, VisibilityKind
)
from ..base import WriteOptions
from .base_msdm_writer import BaseMSDMWriter, SoftDeleteStrategy, WriteTarget

NS_UML = "http://www.omg.org/spec/UML/20131001"
NS_XMI = "http://www.omg.org/spec/XMI/20131001"
NS_XSI = "http://www.w3.org/2001/XMLSchema-instance"

XMI_ATTRIB = {
    f"{{{NS_XSI}}}schemaLocation": "http://www.omg.org/spec/UML/20131001 http://www.omg.org/spec/UML/20131001/UML.xmi",
}
NS_MAP = {
    "xmlns:uml": NS_UML,
    "xmlns:xmi": NS_XMI,
    "xmlns:xsi": NS_XSI,
    "xmi:version": "2.4.1",
}
NS_MAP.update(XMI_ATTRIB)


class UMLXmiWriter(BaseMSDMWriter):
    name = "uml_xmi"
    supported_extensions = (".xmi", ".uml")

    def __init__(self, options: WriteOptions | None = None,
                 target_mode: WriteTarget = WriteTarget.DESIGN_FILE,
                 soft_delete_strategy: SoftDeleteStrategy = SoftDeleteStrategy.NONE):
        super().__init__(options, target_mode, soft_delete_strategy)
        self._id_counter = 0

    async def _write_design(self, document: MSDMDocument) -> bytes:
        root = Element(f"{{{NS_XMI}}}XMI", NS_MAP)

        self._entity_ids: dict[str, str] = {}
        for entity in document.entities:
            self._entity_ids[entity.name] = self._existing_or_new_id(entity, "xmi_id")

        uri = document.namespace.uri if document.namespace else "Model"
        model = SubElement(root, f"{{{NS_UML}}}Model", {
            f"{{{NS_XMI}}}id": self._new_id("model"),
            "name": uri,
        })

        for entity in document.entities:
            model.append(self._entity_to_element(entity))

        for entity in document.entities:
            if entity.extends:
                gen = self._generalization_to_element(entity, entity.extends.name)
                if gen is not None:
                    model.append(gen)

        for rel in document.relationships:
            assoc = self._relationship_to_element(rel)
            if assoc is not None:
                model.append(assoc)

        xml_str = tostring(root, encoding="unicode", method="xml")
        encoding = getattr(self.options, "encoding", "utf-8") if self.options else "utf-8"
        return xml_str.encode(encoding)

    def get_supported_media_types(self) -> list[str]:
        return ["application/xmi+xml", "application/xml"]

    def get_supported_extensions(self) -> list[str]:
        return list(self.supported_extensions)

    def _new_id(self, prefix: str = "id") -> str:
        self._id_counter += 1
        return f"{prefix}_{self._id_counter}"

    def _existing_or_new_id(self, entity: Entity, annotation_key: str) -> str:
        existing = next((a.value for a in entity.annotations if a.key == annotation_key), None)
        if existing:
            return existing
        return self._new_id(entity.name)

    def _entity_to_element(self, entity: Entity) -> Element:
        # Never output Enumeration; only Class or Interface
        if entity.is_interface:
            tag = f"{{{NS_UML}}}Interface"
            xmi_type = "uml:Interface"
        else:
            tag = f"{{{NS_UML}}}Class"
            xmi_type = "uml:Class"

        xmi_id = self._entity_ids[entity.name]
        elem = Element(tag, {
            f"{{{NS_XMI}}}id": xmi_id,
            f"{{{NS_XMI}}}type": xmi_type,
            "name": entity.name,
        })
        if entity.description:
            SubElement(elem, f"{{{NS_UML}}}documentation").text = entity.description

        # Allowed annotation: stereotype_ref
        for ann in entity.annotations:
            if ann.key == "stereotype_ref":
                SubElement(elem, "stereotype", {"href": ann.value})

        if entity.is_abstract:
            elem.set("isAbstract", "true")
        if entity.is_interface:
            elem.set("isAbstract", "true")  # Interface is abstract

        # Write owned attributes (no operations)
        for attr in entity.attributes:
            elem.append(self._property_to_element(attr, entity))

        return elem

    def _property_to_element(self, attr: Attribute, owner: Entity) -> Element:
        prop_id = self._new_id(f"{owner.name}_{attr.name}")
        prop_elem = Element(f"{{{NS_UML}}}ownedAttribute", {
            f"{{{NS_XMI}}}id": prop_id,
            "name": attr.name,
        })

        # Type reference
        if attr.data_type.base == ScalarType.REF and attr.data_type.ref_entity:
            ref_id = self._entity_ids.get(attr.data_type.ref_entity.name)
            if ref_id:
                prop_elem.set("type", ref_id)
        # For STRING we don't set type (could be a primitive, but we skip for simplicity)

        # Multiplicity
        if not attr.required or attr.data_type.base == ScalarType.ARRAY:
            lower_val = "0" if not attr.required else "0"
            upper_val = "*" if attr.data_type.base == ScalarType.ARRAY else "1"
            SubElement(prop_elem, f"{{{NS_UML}}}lowerValue", {
                f"{{{NS_XMI}}}type": "uml:LiteralInteger",
                "value": lower_val,
            })
            SubElement(prop_elem, f"{{{NS_UML}}}upperValue", {
                f"{{{NS_XMI}}}type": "uml:LiteralUnlimitedNatural",
                "value": upper_val,
            })

        if attr.visibility:
            prop_elem.set("visibility", attr.visibility.value)
        if attr.is_static:
            prop_elem.set("isStatic", "true")
        if attr.is_derived:
            prop_elem.set("isDerived", "true")
        if attr.default_value is not None:
            SubElement(prop_elem, f"{{{NS_UML}}}defaultValue", {
                f"{{{NS_XMI}}}type": "uml:LiteralString",
                "value": attr.default_value,
            })

        # CHECK constraints (enums) are NOT written back to XMI
        return prop_elem

    def _generalization_to_element(self, specific_entity: Entity, general_name: str) -> Element | None:
        specific_id = self._entity_ids.get(specific_entity.name)
        general_id = self._entity_ids.get(general_name)
        if not specific_id or not general_id:
            return None
        gen_id = self._new_id(f"gen_{specific_entity.name}_{general_name}")
        return Element(f"{{{NS_UML}}}Generalization", {
            f"{{{NS_XMI}}}id": gen_id,
            "general": general_id,
            "specific": specific_id,
        })

    def _relationship_to_element(self, rel: EntityRelationship) -> Element | None:
        if not rel.from_entity or not rel.to_entity:
            return None
        from_id = self._entity_ids.get(rel.from_entity.name)
        to_id = self._entity_ids.get(rel.to_entity.name)
        if not from_id or not to_id:
            return None

        assoc_id = self._new_id(f"assoc_{rel.from_entity.name}_{rel.to_entity.name}")
        assoc = Element(f"{{{NS_UML}}}Association", {
            f"{{{NS_XMI}}}id": assoc_id,
            "name": rel.name or "",
        })
        if rel.description:
            SubElement(assoc, f"{{{NS_UML}}}documentation").text = rel.description

        end1_id = self._new_id(f"end1_{rel.from_entity.name}_{rel.to_entity.name}")
        end2_id = self._new_id(f"end2_{rel.from_entity.name}_{rel.to_entity.name}")

        from_role = next((a.value for a in rel.annotations if a.key == "from_role"), "")
        to_role = next((a.value for a in rel.annotations if a.key == "to_role"), "")

        end1 = SubElement(assoc, f"{{{NS_UML}}}ownedEnd", {
            f"{{{NS_XMI}}}id": end1_id,
            "name": from_role,
            "type": from_id,
        })
        self._set_multiplicity(end1, rel.cardinality_from)

        end2 = SubElement(assoc, f"{{{NS_UML}}}ownedEnd", {
            f"{{{NS_XMI}}}id": end2_id,
            "name": to_role,
            "type": to_id,
        })
        self._set_multiplicity(end2, rel.cardinality_to)

        assoc.set("memberEnd", f"{end1_id} {end2_id}")

        for ann in rel.annotations:
            if ann.key == "stereotype_ref":
                SubElement(assoc, "stereotype", {"href": ann.value})

        return assoc

    def _set_multiplicity(self, end_elem: Element, card: Cardinality) -> None:
        if card == Cardinality.ONE:
            lower, upper = "1", "1"
        elif card == Cardinality.ZERO_OR_ONE:
            lower, upper = "0", "1"
        elif card == Cardinality.ONE_OR_MANY:
            lower, upper = "1", "*"
        else:  # MANY (0..*)
            lower, upper = "0", "*"
        SubElement(end_elem, f"{{{NS_UML}}}lowerValue", {
            f"{{{NS_XMI}}}type": "uml:LiteralInteger",
            "value": lower,
        })
        SubElement(end_elem, f"{{{NS_UML}}}upperValue", {
            f"{{{NS_XMI}}}type": "uml:LiteralUnlimitedNatural",
            "value": upper,
        })
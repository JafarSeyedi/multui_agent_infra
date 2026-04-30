# engines/document/writers/msdm_writers/uml_xmi_writer.py
"""
UML XMI Writer – converts an MSDMDocument into UML 2.x XMI (XML).
Reconstructs classes, interfaces, enumerations, properties, operations,
generalizations, and associations.  Annotations stored by the parser
(stereotype, xmi:id, etc.) are honoured for round‑trip fidelity.
"""

from __future__ import annotations
from typing import Optional, Dict, Any, List, Tuple
from xml.etree.ElementTree import Element, SubElement, tostring

from .base_msdm_writer import BaseMSDMWriter, WriteTarget, SoftDeleteStrategy
from ..base import WriteOptions
from ...models.msdm_models import (
    MSDMDocument,
    Entity,
    Attribute,
    DataType,
    ScalarType,
    Constraint,
    ConstraintType,
    Relationship,
    Cardinality,
    Annotation,
    EntityKind,
)

# ── Namespaces ─────────────────────────────────────────────────────
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
    """Writer for UML XMI files (.xmi, .uml)."""
    name = "uml_xmi"
    supported_extensions = (".xmi", ".uml")

    def __init__(
        self,
        options: Optional[WriteOptions] = None,
        target_mode: WriteTarget = WriteTarget.DESIGN_FILE,
        soft_delete_strategy: SoftDeleteStrategy = SoftDeleteStrategy.NONE,
    ):
        super().__init__(options, target_mode, soft_delete_strategy)
        self._id_counter = 0

    # ── Public API ─────────────────────────────────────────────────
    async def _write_design(self, document: MSDMDocument) -> bytes:
        root = Element(f"{{{NS_XMI}}}XMI", NS_MAP)

        # Map entity name -> xmi:id for type references
        self._entity_ids: Dict[str, str] = {}
        self._attribute_ids: Dict[str, str] = {}   # for memberEnd references

        # Collect all entities: first pass assign ids
        for entity in document.entities:
            self._entity_ids[entity.name] = self._existing_or_new_id(entity, "xmi_id")

        # Build uml:Model to contain packaged elements
        model = SubElement(root, f"{{{NS_UML}}}Model", {
            f"{{{NS_XMI}}}id": self._new_id("model"),
            "name": document.namespace or "Model",
        })

        # Write all entities (classes, interfaces, enums)
        for entity in document.entities:
            elem = self._entity_to_element(entity)
            model.append(elem)

        # Write generalizations (based on extends)
        for entity in document.entities:
            if entity.extends and entity.extends in self._entity_ids:
                gen = self._generalization_to_element(entity, entity.extends)
                model.append(gen)

        # Write associations from Relationships
        for rel in document.relationships:
            assoc = self._relationship_to_element(rel)
            if assoc is not None:
                model.append(assoc)

        # Write any raw annotations that represent complete XMI elements (round‑trip)
        # The parser didn't store whole elements, but we'll still check document annotations
        for ann in document.annotations:
            if ann.key == "raw_xmi_element":
                # Directly append the literal XML (requires parsing)
                pass

        xml_str = tostring(root, encoding="unicode", method="xml")
        return xml_str.encode(self.options.encoding or "utf-8")

    async def get_supported_media_types(self) -> list[str]:
        return ["application/xmi+xml", "application/xml"]

    async def get_supported_extensions(self) -> list[str]:
        return self.supported_extensions

    # ── ID generation ──────────────────────────────────────────────
    def _new_id(self, prefix: str = "id") -> str:
        self._id_counter += 1
        return f"{prefix}_{self._id_counter}"

    def _existing_or_new_id(self, entity: Entity, annotation_key: str) -> str:
        """Returns the stored xmi:id or generates a new one."""
        existing = next((a.value for a in entity.annotations if a.key == annotation_key), None)
        if existing:
            return existing
        return self._new_id(entity.name)

    # ── Entity → XML element ───────────────────────────────────────
    def _entity_to_element(self, entity: Entity) -> Element:
        xmi_type = self._get_annotation(entity, "xmi_type") or "uml:Class"
        # Translate common types
        if "Interface" in xmi_type:
            tag = f"{{{NS_UML}}}Interface"
        elif "Enumeration" in xmi_type:
            tag = f"{{{NS_UML}}}Enumeration"
        elif "DataType" in xmi_type or "PrimitiveType" in xmi_type:
            tag = f"{{{NS_UML}}}DataType"
        else:
            tag = f"{{{NS_UML}}}Class"

        xmi_id = self._entity_ids[entity.name]
        elem = Element(tag, {
            f"{{{NS_XMI}}}id": xmi_id,
            f"{{{NS_XMI}}}type": xmi_type,
            "name": entity.name,
        })

        if entity.description:
            SubElement(elem, f"{{{NS_UML}}}documentation").text = entity.description

        # Stereotype and extensions from annotations
        for ann in entity.annotations:
            if ann.key == "stereotype_ref":
                # <stereotype href="..."/>
                SubElement(elem, "stereotype", {"href": ann.value})
            elif ann.key not in ("xmi_type", "xmi_id", "abstract", "interface", "enumeration"):
                # For other key‑value pairs, write as <xmi:Extension>
                ext = SubElement(elem, f"{{{NS_XMI}}}Extension", {
                    "extender": ann.key,
                    "extenderValue": ann.value,
                })

        # Abstract attribute
        if self._get_annotation(entity, "abstract") == "true":
            elem.set("isAbstract", "true")
        if self._get_annotation(entity, "interface") == "true":
            elem.set("isAbstract", "true")  # UML Interface is abstract by nature

        # Attributes (properties)
        for attr in entity.attributes:
            if self._is_method(attr):
                op_elem = self._operation_to_element(attr, entity)
                elem.append(op_elem)
            else:
                prop_elem = self._property_to_element(attr, entity)
                elem.append(prop_elem)

        # Enum literals (for enumeration)
        if "Enumeration" in xmi_type:
            for ann in entity.annotations:
                if ann.key == "enum_member":
                    literal = SubElement(elem, f"{{{NS_UML}}}ownedLiteral", {
                        "name": ann.value.split("=")[0].strip(),
                    })
                # no value needed for UML

        return elem

    # ── Property (ownedAttribute) ───────────────────────────────────
    def _property_to_element(self, attr: Attribute, owner: Entity) -> Element:
        prop_id = self._new_id(f"{owner.name}_{attr.name}")
        prop_elem = Element(f"{{{NS_UML}}}ownedAttribute", {
            f"{{{NS_XMI}}}id": prop_id,
            "name": attr.name,
        })

        # Type reference
        if attr.data_type.base == ScalarType.REF and attr.data_type.ref_entity:
            refer_id = self._entity_ids.get(attr.data_type.ref_entity)
            if refer_id:
                prop_elem.set("type", refer_id)

        # Multiplicity
        if not attr.required or attr.data_type.base == ScalarType.ARRAY:
            lower = SubElement(prop_elem, f"{{{NS_UML}}}lowerValue", {
                f"{{{NS_XMI}}}type": "uml:LiteralInteger",
                "value": "0" if not attr.required else "0",
            })
            upper_val = "-1" if attr.data_type.base == ScalarType.ARRAY else "1"
            upper = SubElement(prop_elem, f"{{{NS_UML}}}upperValue", {
                f"{{{NS_XMI}}}type": "uml:LiteralUnlimitedNatural",
                "value": "*" if upper_val == "-1" else upper_val,
            })

        # Visibility from annotation
        vis = self._get_annotation(attr, "visibility")
        if vis:
            prop_elem.set("visibility", vis)

        # Static / derived
        if self._get_annotation(attr, "static") == "true":
            prop_elem.set("isStatic", "true")
        if self._get_annotation(attr, "derived") == "true":
            prop_elem.set("isDerived", "true")

        # Default value (optional)
        if attr.default_value is not None:
            default_elem = SubElement(prop_elem, f"{{{NS_UML}}}defaultValue", {
                f"{{{NS_XMI}}}type": "uml:LiteralString",
                "value": attr.default_value,
            })

        return prop_elem

    # ── Operation (ownedOperation) ─────────────────────────────────
    def _operation_to_element(self, attr: Attribute, owner: Entity) -> Element:
        op_name = self._get_annotation(attr, "operation_name") or attr.name
        op_elem = Element(f"{{{NS_UML}}}ownedOperation", {
            "name": op_name,
        })
        # Visibility
        vis = self._get_annotation(attr, "visibility")
        if vis:
            op_elem.set("visibility", vis)
        if self._get_annotation(attr, "static") == "true":
            op_elem.set("isStatic", "true")
        if self._get_annotation(attr, "abstract") == "true":
            op_elem.set("isAbstract", "true")

        # Parameters: we don't have them stored; skip.

        # Return type
        if attr.data_type.base != ScalarType.ANY:
            ret_type = SubElement(op_elem, f"{{{NS_UML}}}ownedParameter", {
                "name": "return",
                "direction": "return",
            })
            # Set type if reference
            if attr.data_type.base == ScalarType.REF and attr.data_type.ref_entity:
                ref_id = self._entity_ids.get(attr.data_type.ref_entity)
                if ref_id:
                    ret_type.set("type", ref_id)

        return op_elem

    # ── Generalization ──────────────────────────────────────────────
    def _generalization_to_element(self, specific_entity: Entity, general_name: str) -> Element:
        specific_id = self._entity_ids[specific_entity.name]
        general_id = self._entity_ids.get(general_name)
        if not general_id:
            return None
        gen_id = self._new_id(f"gen_{specific_entity.name}_{general_name}")
        gen = Element(f"{{{NS_UML}}}Generalization", {
            f"{{{NS_XMI}}}id": gen_id,
            "general": general_id,
            "specific": specific_id,
        })
        return gen

    # ── Association (from Relationship) ─────────────────────────────
    def _relationship_to_element(self, rel: Relationship) -> Optional[Element]:
        from_id = self._entity_ids.get(rel.from_entity)
        to_id = self._entity_ids.get(rel.to_entity)
        if not from_id or not to_id:
            return None

        assoc_id = self._new_id(f"assoc_{rel.from_entity}_{rel.to_entity}")
        assoc = Element(f"{{{NS_UML}}}Association", {
            f"{{{NS_XMI}}}id": assoc_id,
            "name": rel.name or "",
        })
        if rel.description:
            SubElement(assoc, f"{{{NS_UML}}}documentation").text = rel.description

        # Member ends (ownedEnd)
        # We create two ownedEnd elements and set the memberEnd attribute on the association.
        # For simplicity, we'll create both ends owned by the association, each referencing the class.
        end1_id = self._new_id(f"end1_{rel.from_entity}_{rel.to_entity}")
        end2_id = self._new_id(f"end2_{rel.from_entity}_{rel.to_entity}")

        # End 1 (from_entity side)
        end1 = SubElement(assoc, f"{{{NS_UML}}}ownedEnd", {
            f"{{{NS_XMI}}}id": end1_id,
            "name": self._get_annotation(rel, "from_role") or "",
            "type": from_id,
        })
        self._set_multiplicity(end1, rel.cardinality_from)

        # End 2 (to_entity side)
        end2 = SubElement(assoc, f"{{{NS_UML}}}ownedEnd", {
            f"{{{NS_XMI}}}id": end2_id,
            "name": self._get_annotation(rel, "to_role") or "",
            "type": to_id,
        })
        self._set_multiplicity(end2, rel.cardinality_to)

        # memberEnd attribute (space‑separated)
        assoc.set("memberEnd", f"{end1_id} {end2_id}")

        return assoc

    def _set_multiplicity(self, end_elem: Element, card: Cardinality) -> None:
        """Set lowerValue / upperValue child elements on an association end."""
        lower_val = "0"
        upper_val = "*"
        if card == Cardinality.ONE:
            lower_val = upper_val = "1"
        elif card == Cardinality.ZERO_OR_ONE:
            lower_val = "0"
            upper_val = "1"
        elif card == Cardinality.ONE_OR_MANY:
            lower_val = "1"
            upper_val = "*"
        elif card == Cardinality.MANY:
            lower_val = "0"
            upper_val = "*"

        SubElement(end_elem, f"{{{NS_UML}}}lowerValue", {
            f"{{{NS_XMI}}}type": "uml:LiteralInteger",
            "value": lower_val,
        })
        SubElement(end_elem, f"{{{NS_UML}}}upperValue", {
            f"{{{NS_XMI}}}type": "uml:LiteralUnlimitedNatural",
            "value": upper_val,
        })

    # ── Annotation helpers ─────────────────────────────────────────
    def _get_annotation(self, obj, key: str) -> Optional[str]:
        if isinstance(obj, (Entity, Attribute, Relationship)):
            return next((a.value for a in obj.annotations if a.key == key), None)
        return None

    def _is_method(self, attr: Attribute) -> bool:
        return any(a.key == "method" and a.value == "true" for a in attr.annotations)
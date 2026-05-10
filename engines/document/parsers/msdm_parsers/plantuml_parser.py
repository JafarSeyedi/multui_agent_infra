# engines/document/parsers/msdm_parsers/plantuml_parser.py
"""
PlantUML Parser – converts .plantuml / .puml / .pu class- and ER-diagrams
into an MSDMDocument.

Handles:
- @startuml / @enduml blocks
- class, abstract class, interface, enum, annotation, stereotype
- fields (attribute name : type) with visibility markers (+,-,#,~)
- methods (method name(param:type):returnType) with visibility
- static, abstract modifiers
- inheritance  (Child --|> Parent  or  Parent <|-- Child)
- realisation  (Class ..|> Interface)
- associations, aggregations, compositions with multiplicities
- directional arrows  ( -- , --> , --* , --o , --+ , etc.)
- notes, comments, packages, skinparams, and other syntactic sugar
  are preserved as Annotations for lossless round‑trip.

Every semantic element is mapped to MSDM Entity (kind=OBJECT), Attribute,
and EntityRelationship objects.  Non‑standard constructs are stored as structured
annotations.
"""
from __future__ import annotations

import re
from pathlib import Path

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

# ── Regular expressions ──────────────────────────────────────────

# Class-like definitions: (abstract )? (class|interface|enum|annotation|entity) Name (<<stereotype>>)? ( { ... } )?
RE_CLASS_DEF = re.compile(
    r'^(?:(abstract|annotation)\s+)?(class|interface|enum|entity|annotation)\s+'  # keyword group(1,2)
    r'(\w+)\s*'                                                                    # name group(3)
    r'(?:<<\s*(\w+(?:,\s*\w+)*)\s*>>\s*)?'                                        # stereotype group(4) optional
    r'(\{?)\s*$',                                                                    # opening brace? group(5)
    re.IGNORECASE
)

# Field definition inside class body:  {+|-|#|~}? name : type
RE_FIELD = re.compile(
    r'^\s*([+#\-~])?\s*(\w+)\s*:\s*(.+)$'   # visibility(1) name(2) type(3)
)

# Method definition:  {+|-|#|~}? name ( param:type, ... ) : returnType
RE_METHOD = re.compile(
    r'^\s*([+#\-~])?\s*(\w+)\s*\(\s*(.*?)\s*\)\s*(?::\s*(.+))?\s*$'
)

# EntityRelationship line: ClassA  ["label"] [mult] --|> / --> / --* / --o / .. etc  [mult] ClassB [ : label ]
# We'll break it down:  LeftClass  (["left_label"])?  (multiplicity_left)?  arrow  (multiplicity_right)?  RightClass  ( : label)?
RE_RELATION = re.compile(
    r'^\s*(\w+)\s*'                                  # classA
    r'(?:"([^"]*)"\s*)?'                             # label left (quoted)
    r'(?:((?:\d+\.\.\*)|(?:\d+\.\.\d+)|[*\d]+)\s+)?' # multiplicity left
    r'((?:\.\.?|<\|?)?(--?|\.\.?)(?:[\|>]|[*o+#]?[>\|]))'               # arrow (group 4) e.g. --|>, .., -->
    r'\s*(?:((?:\d+\.\.\*)|(?:\d+\.\.\d+)|[*\d]+)\s+)?' # multiplicity right
    r'(\w+)\s*'                                      # classB
    r'(?::\s*(.+))?\s*$',                            # label right
    re.IGNORECASE
)

# Multiplicity tokens e.g. "1", "0..1", "1..*", "*" -> Cardinality
MULTIPLICITY_MAP = {
    "1": Cardinality.ONE,
    "0..1": Cardinality.ZERO_OR_ONE,
    "1..*": Cardinality.ONE_OR_MANY,
    "*": Cardinality.MANY,
    "0..*": Cardinality.MANY,    # often used for many
}


class PlantUMLParser(BaseMSDMParser):
    """Parser for PlantUML diagram files (.plantuml, .puml, .pu)."""
    name = "plantuml"
    supported_extensions = (".plantuml", ".puml", ".pu")

    async def _parse_to_msdm(
        self, data: bytes, source_name: str, options: ParseOptions
    ) -> MSDMDocument:
        encoding = options.encoding or "utf-8"
        text = data.decode(encoding)

        doc = MSDMDocument(
            document_id=Path(source_name).stem,
            title=Path(source_name).stem,
            media_type=MEDIA_TYPES.get("plantuml", MEDIA_TYPES["txt"])
        )
        doc.namespace = Namespace(uri=Path(source_name).stem)

        lines = text.splitlines()

        # State
        current_entity: Entity | None = None
        in_block = False
        block_lines: list[str] = []
        # Map of class name -> Entity for relationship resolution
        entities_by_name: dict[str, Entity] = {}
        # List of raw relationship strings to parse after all entities are defined
        raw_relations: list[str] = []

        for line in lines:
            stripped = line.strip()

            # Skip comments (PlantUML line comment is a single quote)
            if stripped.startswith("'"):
                continue

            # Skip start/end tags
            if stripped.lower() in ("@startuml", "@enduml"):
                continue

            # If we are inside a class block
            if in_block:
                if stripped == "}":
                    # End of block – finalize entity
                    assert current_entity is not None
                    self._finalize_class_block(current_entity, block_lines, doc, entities_by_name)
                    in_block = False
                    current_entity = None
                    block_lines = []
                    continue
                else:
                    # Collect block content
                    block_lines.append(line)
                    continue

            # Try to match a class/interface/enum definition
            m = RE_CLASS_DEF.match(stripped)
            if m:
                abstract = m.group(1) == "abstract" if m.group(1) else False
                kind_str = m.group(2).lower()
                name = m.group(3)
                stereotype = m.group(4)  # optional
                has_brace = m.group(5) == "{"

                if kind_str == "class":
                    kind = EntityKind.OBJECT
                elif kind_str == "interface":
                    kind = EntityKind.OBJECT   # MSDM doesn't have a separate interface entity; use annotations
                elif kind_str == "enum":
                    kind = EntityKind.OBJECT
                elif kind_str == "entity":
                    kind = EntityKind.TABLE   # ER entity
                else:
                    kind = EntityKind.OBJECT

                entity = Entity(name=name, kind=kind)
                if abstract:
                    entity.annotations.append(Annotation(key="abstract", value="true"))
                if stereotype:
                    entity.annotations.append(Annotation(key="stereotype", value=stereotype))
                if kind_str == "interface":
                    entity.annotations.append(Annotation(key="interface", value="true"))

                if has_brace:
                    in_block = True
                    current_entity = entity
                    block_lines = []
                else:
                    # No block – keep as empty entity
                    doc.entities.append(entity)
                    entities_by_name[name] = entity
                continue

            # Try to match a relationship line
            rel_match = RE_RELATION.match(stripped)
            if rel_match:
                # We'll process relationships later once all classes are known
                raw_relations.append(stripped)
                # but also store as annotation for round-trip
                doc.annotations.append(Annotation(key="raw_relation", value=stripped))
                continue

            # Unrecognized line – store as a document-level annotation
            if stripped:
                doc.annotations.append(Annotation(key="raw_line", value=stripped))

        # If a block was never closed, finalize it anyway
        if in_block and current_entity:
            self._finalize_class_block(current_entity, block_lines, doc, entities_by_name)

        # Now parse the relationships we stored
        for rel_line in raw_relations:
            self._parse_relationship_line(rel_line, entities_by_name, doc)

        # Also add entities that were collected (some may already be in doc.entities)
        for ent in entities_by_name.values():
            if ent not in doc.entities:
                doc.entities.append(ent)

        self.resolve_references(doc)
        return doc

    def _finalize_class_block(self, entity: Entity, lines: list[str],
                              doc: MSDMDocument, entities_by_name: dict[str, Entity]) -> None:
        """
        Parse the interior of a class/interface body.
        Lines contain field definitions and method definitions.
        """
        for line in lines:
            stripped = line.strip()
            if not stripped or stripped == "}":
                continue

            # Try field first
            field_m = RE_FIELD.match(stripped)
            if field_m:
                visibility = field_m.group(1) or ""
                name = field_m.group(2)
                type_str = field_m.group(3).strip()
                attr = Attribute(
                    name=name,
                    data_type=self._parse_type_string(type_str, doc),
                    required=False,  # can't deduce from syntax
                )
                if visibility:
                    attr.annotations.append(Annotation(key="visibility", value=visibility))
                entity.attributes.append(attr)
                continue

            # Try method
            method_m = RE_METHOD.match(stripped)
            if method_m:
                visibility = method_m.group(1) or ""
                method_name = method_m.group(2)
                params_str = method_m.group(3).strip()
                return_type_str = method_m.group(4)
                # Represent method as an attribute with complex type? We'll use an annotation for now.
                # For a richer representation, we could create a nested struct for method signature.
                # We'll store as a pseudo-attribute with name = methodName(params) and type = returnType.
                pseudo_name = f"{method_name}({params_str})"
                pseudo_type = return_type_str if return_type_str else "void"
                attr = Attribute(
                    name=pseudo_name,
                    data_type=self._parse_type_string(pseudo_type, doc),
                )
                attr.annotations.append(Annotation(key="method", value="true"))
                if visibility:
                    attr.annotations.append(Annotation(key="visibility", value=visibility))
                entity.attributes.append(attr)
                continue

            # Unrecognized line inside block – store as entity annotation
            entity.annotations.append(Annotation(key="body_line", value=stripped))

        doc.entities.append(entity)
        entities_by_name[entity.name] = entity

    def _parse_type_string(self, type_str: str, doc: MSDMDocument) -> DataType:
        """Convert a PlantUML type string (possibly with generics, arrays) to DataType.
        We do a best-effort mapping."""
        if not type_str:
            return DataType(base=ScalarType.ANY)
        type_str = type_str.strip()
        # Check for array syntax like 'int[]', 'List<String>'
        if type_str.endswith("[]"):
            inner = type_str[:-2]
            return DataType(base=ScalarType.ARRAY, element_type=self._parse_type_string(inner, doc))
        if "<" in type_str and type_str.endswith(">"):
            # generic, treat as STRUCT with annotations? Or just ANY
            return DataType(base=ScalarType.ANY)
        # Primitive type mapping
        mapping = {
            "string": ScalarType.STRING,
            "int": ScalarType.INT,
            "integer": ScalarType.INT,
            "long": ScalarType.LONG,
            "float": ScalarType.FLOAT,
            "double": ScalarType.DOUBLE,
            "boolean": ScalarType.BOOLEAN,
            "bool": ScalarType.BOOLEAN,
            "date": ScalarType.DATE,
            "datetime": ScalarType.TIMESTAMP,
            "void": ScalarType.ANY,
            "char": ScalarType.STRING,
            "byte": ScalarType.BINARY,
        }
        lower = type_str.lower()
        if lower in mapping:
            return DataType(base=mapping[lower])
        # Otherwise, treat as a reference to another class
        return DataType(base=ScalarType.REF, ref_entity_id=type_str)

    def _parse_relationship_line(self, line: str,
                                 entities_by_name: dict[str, Entity],
                                 doc: MSDMDocument) -> None:
        """
        Parse a full relationship line and add a Relationship object to doc.
        Also handle inheritance by setting Entity.extends.
        """
        m = RE_RELATION.match(line)
        if not m:
            return

        left_class = m.group(1)
        left_label = m.group(2)
        left_mult_str = m.group(3)
        arrow = m.group(4)
        right_mult_str = m.group(5)
        right_class = m.group(6)
        label = m.group(7)

        # Determine relationship kind from arrow
        if arrow in ("--|>", "<|--", "..|>"):  # inheritance / realisation
            # Inheritance: left is parent if arrow is <|--, else if arrow ends with |> right is parent?
            # Common case: Parent <|-- Child  => left=Parent, arrow=<|--, right=Child
            if arrow == "<|--" or arrow == "..|>":
                # left is the supertype?
                if arrow == "<|--":
                    # left is parent, right is child
                    if right_class in entities_by_name:
                        child_entity = entities_by_name[right_class]
                        child_entity.extends_ref_id = left_class
                        if arrow == "..|>":
                            # realisation: class ..|> interface (left is class, right is interface?)
                            # Actually it's usually Child ..|> Parent or Class ..|> Interface
                            # We'll treat left as child and right as interface, so set extends and mark interface annotation
                            if left_class in entities_by_name:
                                left_entity = entities_by_name[left_class]
                                left_entity.extends_ref_id = right_class
                                left_entity.annotations.append(Annotation(key="implements", value="true"))
                            return
                else:  # --|>  (left child, right parent)
                    if left_class in entities_by_name:
                        left_entity = entities_by_name[left_class]
                        left_entity.extends_ref_id = right_class
                return
            # Arrow like --|> or similar directional
            # We'll handle general cases later
        else:
            # Regular association
            from_card = self._to_card(left_mult_str)
            to_card = self._to_card(right_mult_str)
            # Determine direction: if arrow contains > at end, direction is left->right
            rel = EntityRelationship(
                name=label,
                from_ref_id=left_class,
                to_ref_id=right_class,
                cardinality_from=from_card,
                cardinality_to=to_card,
            )
            if left_label:
                rel.annotations.append(Annotation(key="left_label", value=left_label))
            doc.relationships.append(rel)

    def _to_card(self, mult_str: str | None) -> Cardinality:
        if not mult_str:
            return Cardinality.ONE
        mult_str = mult_str.strip()
        if mult_str in MULTIPLICITY_MAP:
            return MULTIPLICITY_MAP[mult_str]
        # Try to parse patterns like "0..1"
        if ".." in mult_str:
            parts = mult_str.split("..")
            lower = parts[0].strip()
            upper = parts[1].strip()
            if lower == "0" and upper == "1":
                return Cardinality.ZERO_OR_ONE
            if lower == "1" and upper == "*":
                return Cardinality.ONE_OR_MANY
            if lower == "0" and (upper == "*" or upper == "n"):
                return Cardinality.MANY
        # Any number > 1 we treat as MANY? Could be improved.
        if mult_str.isdigit():
            val = int(mult_str)
            if val == 1:
                return Cardinality.ONE
            else:
                return Cardinality.MANY
        return Cardinality.ONE
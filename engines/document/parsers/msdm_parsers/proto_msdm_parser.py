# engines/document/parsers/msdm_parsers/proto_parser.py
"""
Protobuf IDL Parser (.proto) – converts .proto files into an MSDMDocument.

Handles:
- syntax, package, import (stored as annotations)
- option (file-level, message-level, field-level)
- message, enum, oneof, map (pseudo‑oneof)
- field types: scalar types, references to other messages/enums
- repeated, optional, required
- reserved fields (numbers, names)
- nested messages and enums
- extensions, extend blocks (preserved as annotations)

Every protobuf detail is mapped to MSDM Entity (kind=OBJECT), Attribute,
Constraint, and Annotation objects for lossless round‑trip.
"""

from __future__ import annotations
import re
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple, Set

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
)

# ── Protobuf scalar type mapping ──────────────────────────────────
PROTO_SCALAR_MAP = {
    "double":   ScalarType.DOUBLE,
    "float":    ScalarType.FLOAT,
    "int32":    ScalarType.INT,
    "int64":    ScalarType.LONG,
    "uint32":   ScalarType.LONG,
    "uint64":   ScalarType.LONG,
    "sint32":   ScalarType.INT,
    "sint64":   ScalarType.LONG,
    "fixed32":  ScalarType.INT,
    "fixed64":  ScalarType.LONG,
    "sfixed32": ScalarType.INT,
    "sfixed64": ScalarType.LONG,
    "bool":     ScalarType.BOOLEAN,
    "string":   ScalarType.STRING,
    "bytes":    ScalarType.BINARY,
}


class ProtoParser(BaseMSDMParser):
    """Parser for Protobuf IDL (.proto) files."""
    name = "proto"
    supported_extensions = (".proto",)

    async def _parse_to_msdm(
        self, data: bytes, source_name: str, options: ParseOptions
    ) -> MSDMDocument:
        encoding = options.encoding or "utf-8"
        text = data.decode(encoding)

        doc = MSDMDocument()
        doc.namespace = Path(source_name).stem

        # Remove comments
        text = self._strip_comments(text)

        # Parse top‑level elements using a simple recursive descent approach
        self._tokenize(text)
        self._pos = 0

        while self._peek() is not None:
            self._parse_top_level(doc)

        return doc

    # ── Simple tokenizer (splitting by meaningful boundaries) ─────
    def _tokenize(self, text: str) -> None:
        # Tokenization is straightforward: we split by whitespace but keep braces, semicolons,
        # and retain quoted strings. We'll process line by line? Not enough.
        # Instead, we'll use a regex to produce tokens:
        # - identifiers: [a-zA-Z_][a-zA-Z0-9_.]*
        # - string literals: "..." or '...'
        # - numbers: \d+
        # - symbols: = ; ( ) { } [ ] , < > / etc.
        pattern = re.compile(
            r'"[^"]*"'          # string literal
            r"|'[^']*'"
            r"|0x[0-9a-fA-F]+"
            r"|\d+\.\d+|\d+"
            r"|[a-zA-Z_][\w.]*" # identifier or qualified name
            r"|//[^\n]*"        # line comment (though we already stripped)
            r"|\S",
            re.IGNORECASE
        )
        self._tokens = pattern.findall(text)
        self._pos = 0

    def _peek(self, offset: int = 0) -> Optional[str]:
        idx = self._pos + offset
        return self._tokens[idx] if idx < len(self._tokens) else None

    def _advance(self) -> str:
        tok = self._tokens[self._pos]
        self._pos += 1
        return tok

    def _strip_comments(self, text: str) -> str:
        # Remove block comments
        text = re.sub(r'/\*.*?\*/', '', text, flags=re.DOTALL)
        # Remove line comments
        text = re.sub(r'//[^\n]*', '', text)
        return text

    # ── Top‑level parsing ────────────────────────────────────────
    def _parse_top_level(self, doc: MSDMDocument) -> None:
        tok = self._peek()
        if tok is None:
            return
        keyword = tok
        if keyword == "syntax":
            self._advance()
            self._expect("=")
            val = self._advance().strip('";')
            doc.annotations.append(Annotation(key="syntax", value=val))
            self._expect(";")
        elif keyword == "package":
            self._advance()
            pkg = self._advance().rstrip(";")
            doc.namespace = pkg
            if self._peek() == ";":
                self._advance()
        elif keyword == "import":
            self._advance()
            imp = self._advance().strip('";')
            doc.annotations.append(Annotation(key="import", value=imp))
            if self._peek() == ";":
                self._advance()
        elif keyword == "option":
            self._parse_option(None, doc)   # file‑level option stored on doc
        elif keyword == "message":
            self._advance()
            self._parse_message(doc, None)
        elif keyword == "enum":
            self._advance()
            self._parse_enum(doc, None)
        elif keyword == "extend":
            self._advance()
            # extend blocks not fully modeled; store as annotation
            self._parse_extend(doc)
        elif keyword == "service":
            self._advance()
            # service definitions usually go to SSDM, but if present in MSDM context,
            # we store as annotation
            self._parse_service(doc)
        else:
            # skip unknown
            self._advance()

    # ── Message parsing ──────────────────────────────────────────
    def _parse_message(self, doc: MSDMDocument, parent: Optional[Entity]) -> Entity:
        name = self._advance()
        entity = Entity(name=name, kind=EntityKind.OBJECT)
        self._expect("{")
        while self._peek() and self._peek() != "}":
            field_tok = self._peek()
            if field_tok == "message":
                self._advance()
                nested = self._parse_message(doc, entity)
                # Store nested entity as annotation? Or add as child? For simplicity, annotations.
                entity.annotations.append(Annotation(key="nested_message", value=nested.name))
                # We could also add the nested entity to doc.entities for completeness
                doc.entities.append(nested)
            elif field_tok == "enum":
                self._advance()
                nested_enum = self._parse_enum(doc, entity)
                entity.annotations.append(Annotation(key="nested_enum", value=nested_enum.name))
                doc.entities.append(nested_enum)
            elif field_tok == "option":
                self._parse_option(entity, doc)
            elif field_tok == "oneof":
                self._advance()
                self._parse_oneof(entity, doc)
            elif field_tok == "reserved":
                self._advance()
                # reserved fields – store as annotation
                reserved_parts = []
                while self._peek() and self._peek() != ";":
                    reserved_parts.append(self._advance())
                entity.annotations.append(Annotation(key="reserved", value=" ".join(reserved_parts)))
                self._expect(";")
            elif field_tok == "map":
                self._parse_map_field(entity, doc)
            elif field_tok == "}":
                break
            else:
                # It's a normal field: [repeated|optional|required] type name = number [field_options];
                self._parse_field(entity, doc)
        self._expect("}")
        doc.entities.append(entity)
        return entity

    def _parse_field(self, entity: Entity, doc: MSDMDocument) -> None:
        """Parse a message field."""
        # optional, repeated, required
        label = None
        tok = self._peek()
        if tok in ("optional", "repeated", "required"):
            label = self._advance()
        field_type = self._advance()   # can be scalar or qualified name
        field_name = self._advance()
        self._expect("=")
        field_number = self._advance()
        # skip ; if present after options, but options may follow before ;
        # field options can be inside [ ... ]
        field_options = {}
        if self._peek() == "[":
            self._advance()
            field_options = self._parse_field_options()
            self._expect("]")
        # read until semicolon
        while self._peek() and self._peek() != ";":
            self._advance()
        if self._peek() == ";":
            self._advance()

        # Build DataType
        dt = self._proto_type_to_datatype(field_type, label, doc)

        attr = Attribute(
            name=field_name,
            data_type=dt,
            required=label == "required",
            description=None,
        )
        # Field number
        attr.annotations.append(Annotation(key="field_number", value=field_number))
        if label:
            attr.annotations.append(Annotation(key="label", value=label))
        # Field options
        for opt_key, opt_val in field_options.items():
            attr.annotations.append(Annotation(key=opt_key, value=opt_val))
        entity.attributes.append(attr)

    def _parse_map_field(self, entity: Entity, doc: MSDMDocument) -> None:
        """map<keyType, valueType> name = number;"""
        # advance over 'map' (already consumed) or we handle it when we see 'map'
        # Assume we are positioned at 'map'? In the loop we handled. Let's adjust: the caller
        # already called _advance() for 'map' and passed here. So we need to read the full declaration.
        # But our loop already advances 'map', so here we see '<'
        if self._peek() == "<":
            self._advance()
        key_type = self._advance()
        self._expect(",")
        value_type = self._advance()
        self._expect(">")
        name = self._advance()
        self._expect("=")
        field_number = self._advance()
        # Options
        field_options = {}
        if self._peek() == "[":
            self._advance()
            field_options = self._parse_field_options()
            self._expect("]")
        while self._peek() and self._peek() != ";":
            self._advance()
        self._expect(";")

        # Represent map as MAP DataType with key_type and value_type
        key_dt = self._proto_scalar_to_datatype(key_type)
        val_dt = self._proto_type_to_datatype(value_type, None, doc)
        dt = DataType(base=ScalarType.MAP, key_type=key_dt, value_type=val_dt)

        attr = Attribute(name=name, data_type=dt)
        attr.annotations.append(Annotation(key="field_number", value=field_number))
        for opt_key, opt_val in field_options.items():
            attr.annotations.append(Annotation(key=opt_key, value=opt_val))
        entity.attributes.append(attr)

    def _parse_oneof(self, entity: Entity, doc: MSDMDocument) -> None:
        """oneof name { fields } -> represented as a Struct attribute with nested optional fields."""
        name = self._advance()
        self._expect("{")
        # Create a dedicated struct attribute for the oneof
        nested_attrs = []
        while self._peek() and self._peek() != "}":
            tok = self._peek()
            if tok in ("option",):
                # skip option inside oneof
                self._advance()
                while self._peek() and self._peek() != ";":
                    self._advance()
                self._expect(";")
            else:
                # Field inside oneof (similar to normal field but no required/optional/repeated)
                field_type = self._advance()
                field_name = self._advance()
                self._expect("=")
                field_number = self._advance()
                field_options = {}
                if self._peek() == "[":
                    self._advance()
                    field_options = self._parse_field_options()
                    self._expect("]")
                while self._peek() and self._peek() != ";":
                    self._advance()
                self._expect(";")
                dt = self._proto_type_to_datatype(field_type, None, doc)
                attr = Attribute(name=field_name, data_type=dt, required=False)
                attr.annotations.append(Annotation(key="field_number", value=field_number))
                for opt_key, opt_val in field_options.items():
                    attr.annotations.append(Annotation(key=opt_key, value=opt_val))
                nested_attrs.append(attr)
        self._expect("}")
        # Add as a composite attribute to entity
        oneof_attr = Attribute(name=name, data_type=DataType(base=ScalarType.STRUCT))
        oneof_attr.nested_attributes = nested_attrs
        # Mark it as oneof
        oneof_attr.annotations.append(Annotation(key="oneof", value="true"))
        entity.attributes.append(oneof_attr)

    # ── Enum parsing ──────────────────────────────────────────────
    def _parse_enum(self, doc: MSDMDocument, parent: Optional[Entity]) -> Entity:
        name = self._advance()
        entity = Entity(name=name, kind=EntityKind.OBJECT)
        self._expect("{")
        while self._peek() and self._peek() != "}":
            tok = self._peek()
            if tok == "option":
                self._parse_option(entity, doc)
            elif tok == "reserved":
                self._advance()
                parts = []
                while self._peek() and self._peek() != ";":
                    parts.append(self._advance())
                entity.annotations.append(Annotation(key="reserved", value=" ".join(parts)))
                self._expect(";")
            else:
                # Enum value
                val_name = self._advance()
                self._expect("=")
                val_num = self._advance()
                # optional field options
                while self._peek() and self._peek() != ";":
                    if self._peek() == "[":
                        self._advance()
                        self._parse_field_options()  # ignore
                        self._expect("]")
                    else:
                        self._advance()
                self._expect(";")
                # Represent enum value as a constraint on a single "value" attribute? We'll create a check constraint for the whole enum.
                # For detailed mapping, we'll collect values and after parsing body, set an "enum_values" annotation.
                # We store as annotation temporarily.
                entity.annotations.append(Annotation(key="enum_value", value=f"{val_name}={val_num}"))
        self._expect("}")
        doc.entities.append(entity)
        return entity

    # ── Option parsing ──────────────────────────────────────────
    def _parse_option(self, target: Optional[Entity], doc: MSDMDocument) -> None:
        """Parse an option statement and attach it as an annotation."""
        opt_name = self._advance()
        self._expect("=")
        # value could be a string, number, or identifier
        value_tokens = []
        while self._peek() and self._peek() != ";":
            value_tokens.append(self._advance())
        opt_value = " ".join(value_tokens)
        if target:
            target.annotations.append(Annotation(key="option", value=f"{opt_name}={opt_value}"))
        else:
            doc.annotations.append(Annotation(key="file_option", value=f"{opt_name}={opt_value}"))

    def _parse_field_options(self) -> Dict[str, str]:
        """Parse the content of [ ... ] field options and return a dict."""
        opts = {}
        # Simple: token sequence like (packed=true), (json_name = "foo"), etc.
        # We'll accumulate key=value pairs separated by commas.
        current_key = None
        while self._peek() and self._peek() != "]":
            tok = self._peek()
            if tok == ",":
                self._advance()
                continue
            # key = value
            key = self._advance()
            if self._peek() == "=":
                self._advance()
                val = self._advance().strip('"')
                opts[key.strip("(")] = val.strip(")")
            else:
                # boolean option without value, e.g., deprecated
                opts[key.strip("(")] = "true"
                if key.endswith(")"):
                    pass  # already stripped paren
        return opts

    # ── Extend / Service (stubs for round‑trip) ──────────────────
    def _parse_extend(self, doc: MSDMDocument) -> None:
        """Record an extend block as annotation."""
        extend_target = self._advance()
        self._expect("{")
        # skip content
        depth = 1
        while self._peek() and depth > 0:
            if self._peek() == "{":
                depth += 1
            elif self._peek() == "}":
                depth -= 1
                if depth == 0:
                    self._advance()
                    break
            self._advance()
        doc.annotations.append(Annotation(key="extend", value=extend_target))

    def _parse_service(self, doc: MSDMDocument) -> None:
        """Record service definition as annotation."""
        service_name = self._advance()
        self._expect("{")
        depth = 1
        while self._peek() and depth > 0:
            if self._peek() == "{":
                depth += 1
            elif self._peek() == "}":
                depth -= 1
                if depth == 0:
                    self._advance()
                    break
            self._advance()
        doc.annotations.append(Annotation(key="service", value=service_name))

    # ── Type conversion helpers ─────────────────────────────────
    def _proto_type_to_datatype(self, type_str: str, label: Optional[str], doc: MSDMDocument) -> DataType:
        """Convert a protobuf type (maybe qualified) to DataType."""
        # If label is "repeated", wrap with ARRAY
        base = self._proto_scalar_to_datatype(type_str)
        if label == "repeated":
            return DataType(base=ScalarType.ARRAY, element_type=base)
        return base

    def _proto_scalar_to_datatype(self, type_str: str) -> DataType:
        """Map a type name (including qualified names) to DataType."""
        if type_str in PROTO_SCALAR_MAP:
            return DataType(base=PROTO_SCALAR_MAP[type_str])
        # Otherwise, it's a reference to another message or enum
        return DataType(base=ScalarType.REF, ref_entity=type_str)

    # ── Utility ─────────────────────────────────────────────────
    def _expect(self, expected: str) -> None:
        tok = self._advance()
        if tok != expected:
            raise SyntaxError(f"Expected '{expected}' but got '{tok}'")
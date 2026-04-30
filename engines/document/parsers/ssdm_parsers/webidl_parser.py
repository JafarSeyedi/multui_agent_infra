# engines/document/parsers/ssdm_parsers/webidl_parser.py
"""
Web IDL Parser – converts a .webidl file into an SSDM_DOCUMENT.

Mapping rules (Web IDL → SSDM):
- interface → set of operations (one per method) + optional MSDM entity for attributes
- dictionary → MSDM entity
- enum → MSDM entity with a CHECK constraint
- typedef → alias stored as MSDM entity? Skipped for simplicity.
- Each interface method → Operation (name, parameters, return type as first response)
- Method parameters (primitives, arrays, dictionaries) → Parameter objects
- Return type → Response with content_entity referencing the MSDM type
"""

from __future__ import annotations
import re
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple

from .base_ssdm_parser import BaseSSDMParser
from ..base import ParseOptions
from ...models.ssdm_models import (
    SSDM_DOCUMENT,
    Operation,
    Parameter,
    ParameterLocation,
    RequestBody,
    Response,
    SecurityScheme,
    Server,
)
from ...models.msdm_models import (
    MSDMDocument,
    Entity,
    Attribute,
    DataType,
    ScalarType,
    Constraint,
    ConstraintType,
)
from ...models.base import BaseDocument


# ── Tokenizer ──────────────────────────────────────────────────────
TOKEN_SPEC = [
    ("COMMENT",       r"//[^\n]*|/\*[\s\S]*?\*/"),
    ("STRING",        r'"[^"\\]*(?:\\.[^"\\]*)*"'),
    ("NUMBER",        r"-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?"),
    ("KEYWORD",       r"[a-zA-Z_][\w]*"),
    ("PUNCTUATION",   r"[{}();,=<>\[\]\.]"),
    ("WHITESPACE",    r"\s+"),
    ("UNEXPECTED",    r"."),
]
TOKEN_RE = re.compile("|".join(f"(?P<{name}>{pattern})" for name, pattern in TOKEN_SPEC))


class Token:
    def __init__(self, kind: str, value: str, pos: int):
        self.kind = kind
        self.value = value
        self.pos = pos


def tokenize(text: str) -> List[Token]:
    tokens = []
    for m in TOKEN_RE.finditer(text):
        kind = m.lastgroup
        value = m.group()
        if kind in ("WHITESPACE", "COMMENT"):
            continue
        tokens.append(Token(kind, value, m.start()))
    return tokens


# ── Parser ─────────────────────────────────────────────────────────
class WebIDLParser(BaseSSDMParser):
    """Parser for Web IDL files (.webidl)."""

    name = "webidl"
    supported_extensions = (".webidl",)

    async def _parse_to_document(
        self, data: bytes, source_name: str, options: ParseOptions
    ) -> SSDM_DOCUMENT:
        encoding = options.encoding or "utf-8"
        text = data.decode(encoding)
        tokens = tokenize(text)
        self._tokens = tokens
        self._pos = 0

        doc = SSDM_DOCUMENT(
            title=Path(source_name).stem,
            version="1.0.0",
        )
        msdm = MSDMDocument()

        # Parse definitions
        while self._pos < len(self._tokens):
            self._parse_definition(doc, msdm)

        if msdm.entities:
            doc.type_definitions = msdm
        return doc

    # ── Token helpers ──────────────────────────────────────────
    def _peek(self) -> Optional[Token]:
        return self._tokens[self._pos] if self._pos < len(self._tokens) else None

    def _advance(self) -> Token:
        tok = self._tokens[self._pos]
        self._pos += 1
        return tok

    def _expect(self, kind: str, value: Optional[str] = None) -> Token:
        tok = self._advance()
        if tok.kind != kind or (value is not None and tok.value != value):
            raise SyntaxError(f"Expected {kind}('{value}') but got {tok}")
        return tok

    def _match(self, *kinds: str) -> Optional[Token]:
        tok = self._peek()
        if tok and tok.kind in kinds:
            return self._advance()
        return None

    # ── Definition dispatcher ──────────────────────────────────
    def _parse_definition(self, doc: SSDM_DOCUMENT, msdm: MSDMDocument) -> None:
        tok = self._peek()
        if not tok:
            return
        if tok.value == "interface":
            self._advance()
            self._parse_interface(doc, msdm)
        elif tok.value == "dictionary":
            self._advance()
            self._parse_dictionary(msdm)
        elif tok.value == "enum":
            self._advance()
            self._parse_enum(msdm)
        elif tok.value == "typedef":
            self._advance()
            self._parse_typedef(msdm)
        elif tok.value == "callback" or tok.value == "callback interface":
            self._advance()
            self._skip_definition()  # skip callbacks for now
        elif tok.value == "partial" or tok.value == "interface mixin":
            self._advance()
            self._skip_definition()
        else:
            # Unknown – skip to next semicolon or brace
            self._skip_unknown()

    def _skip_definition(self) -> None:
        # Skip until we see a top-level semicolon not inside braces
        depth = 0
        while self._pos < len(self._tokens):
            tok = self._advance()
            if tok.value == "{":
                depth += 1
            elif tok.value == "}":
                depth -= 1
            elif tok.value == ";" and depth == 0:
                break

    def _skip_unknown(self) -> None:
        # Skip one token or a semicolon
        if self._peek() and self._peek().value == ";":
            self._advance()
        else:
            self._advance()

    # ── Interface ──────────────────────────────────────────────
    def _parse_interface(self, doc: SSDM_DOCUMENT, msdm: MSDMDocument) -> None:
        name = self._expect("KEYWORD").value
        # Inheritance
        if self._peek() and self._peek().value == ":":
            self._advance()
            self._expect("KEYWORD")  # skip base
        self._expect("PUNCTUATION", "{")

        # Members
        attributes: List[Attribute] = []
        while self._peek() and self._peek().value != "}":
            member = self._parse_interface_member()
            if isinstance(member, Operation):
                doc.operations.append(member)
            elif isinstance(member, Attribute):
                attributes.append(member)
        self._expect("PUNCTUATION", "}")

        # Create MSDM entity for the interface (attributes)
        if attributes:
            entity = Entity(name=name)
            entity.attributes = attributes
            msdm.entities.append(entity)

        # May need to add a server? Not in Web IDL.

    def _parse_interface_member(self) -> Optional[Operation | Attribute]:
        tok = self._peek()
        if not tok:
            return None
        # Handle 'readonly', 'static', 'stringifier', 'inherit', etc.
        qualifiers = []
        while tok.value in ("readonly", "static", "stringifier", "inherit", "attribute",
                            "iterable", "maplike", "setlike", "async"):
            qualifiers.append(self._advance().value)
            tok = self._peek()
            if not tok:
                return None
        if tok.value == "attribute":
            # regular attribute
            self._advance()
            attr_type = self._parse_type()
            attr_name = self._expect("KEYWORD").value
            self._expect("PUNCTUATION", ";")
            dt = self._idl_type_to_datatype(attr_type)
            return Attribute(name=attr_name, data_type=dt, required=True)
        else:
            # Assume a method
            return self._parse_operation(qualifiers)

    def _parse_operation(self, qualifiers: List[str]) -> Operation:
        name = self._expect("KEYWORD").value
        self._expect("PUNCTUATION", "(")
        params = []
        if self._peek() and self._peek().value != ")":
            params = self._parse_arguments()
        self._expect("PUNCTUATION", ")")
        # Return type (optional)
        return_type = None
        if self._peek() and self._peek().value in (":", "=>"):
            self._advance()
            return_type = self._parse_type()
            if self._peek() and self._peek().value == "?":
                self._advance()  # nullable
        self._expect("PUNCTUATION", ";")

        op = Operation(name=name, http_method=None)  # No HTTP method in Web IDL
        op.parameters = params
        if return_type:
            dt = self._idl_type_to_datatype(return_type)
            entity = self._datatype_to_entity(dt, name + "Return")
            if entity:
                op.responses.append(Response(status_code="200", content_entity=entity))
        return op

    def _parse_arguments(self) -> List[Parameter]:
        params = []
        # Comma‑separated arguments
        while True:
            param_name = self._expect("KEYWORD").value
            self._expect("PUNCTUATION", ":")
            param_type = self._parse_type()
            required = True
            if self._peek() and self._peek().value == "=":
                self._advance()
                # skip default value
                if self._peek() and self._peek().kind in ("STRING", "NUMBER", "KEYWORD"):
                    self._advance()
                required = False
            dt = self._idl_type_to_datatype(param_type)
            params.append(Parameter(
                name=param_name,
                location=ParameterLocation.BODY,   # Web IDL arguments are like body parameters
                required=required,
                type_string=self._type_to_string(param_type),
            ))
            if self._peek() and self._peek().value == ",":
                self._advance()
            else:
                break
        return params

    # ── Dictionary ─────────────────────────────────────────────
    def _parse_dictionary(self, msdm: MSDMDocument) -> None:
        name = self._expect("KEYWORD").value
        # Inheritance
        if self._peek() and self._peek().value == ":":
            self._advance()
            self._expect("KEYWORD")
        self._expect("PUNCTUATION", "{")
        entity = Entity(name=name)
        while self._peek() and self._peek().value != "}":
            self._parse_dictionary_member(entity)
        self._expect("PUNCTUATION", "}")
        msdm.entities.append(entity)

    def _parse_dictionary_member(self, entity: Entity) -> None:
        # member type, name, default
        tok = self._peek()
        if tok and tok.value in ("required",):
            self._advance()
        attr_type = self._parse_type()
        attr_name = self._expect("KEYWORD").value
        default = None
        if self._peek() and self._peek().value == "=":
            self._advance()
            if self._peek() and self._peek().kind in ("STRING", "NUMBER", "KEYWORD"):
                default = self._advance().value
        self._expect("PUNCTUATION", ";")
        dt = self._idl_type_to_datatype(attr_type)
        entity.attributes.append(Attribute(name=attr_name, data_type=dt, required=False))

    # ── Enum ───────────────────────────────────────────────────
    def _parse_enum(self, msdm: MSDMDocument) -> None:
        name = self._expect("KEYWORD").value
        self._expect("PUNCTUATION", "{")
        values = []
        while self._peek() and self._peek().value != "}":
            val = self._expect("KEYWORD").value
            values.append(val)
            if self._peek() and self._peek().value == ",":
                self._advance()
        self._expect("PUNCTUATION", "}")
        entity = Entity(name=name)
        attr = Attribute(name="value", data_type=DataType(base=ScalarType.STRING), required=True)
        quoted = ", ".join(f'"{v}"' for v in values)
        attr.constraints.append(Constraint(type=ConstraintType.CHECK, expression=f"IN ({quoted})"))
        entity.attributes.append(attr)
        msdm.entities.append(entity)

    # ── Typedef (skip for now) ─────────────────────────────────
    def _parse_typedef(self, msdm: MSDMDocument) -> None:
        self._parse_type()
        self._expect("KEYWORD")
        self._expect("PUNCTUATION", ";")

    # ── Type parser ────────────────────────────────────────────
    def _parse_type(self) -> str:
        """Return the type name as a string (may include generics, sequences, etc.)"""
        tok = self._peek()
        if not tok:
            return "any"
        # Check for built‑in names
        if tok.value in ("any", "boolean", "byte", "octet", "short", "unsigned short",
                         "long", "unsigned long", "long long", "unsigned long long",
                         "float", "unrestricted float", "double", "unrestricted double",
                         "DOMString", "ByteString", "USVString", "object", "symbol",
                         "ArrayBuffer", "DataView", "Int8Array", "Int16Array", "Int32Array",
                         "Uint8Array", "Uint16Array", "Uint32Array", "Uint8ClampedArray",
                         "Float32Array", "Float64Array", "BigInt64Array", "BigUint64Array",
                         "undefined", "void"):
            return self._advance().value
        if tok.value == "sequence":
            self._advance()
            self._expect("PUNCTUATION", "<")
            inner = self._parse_type()
            self._expect("PUNCTUATION", ">")
            return f"sequence<{inner}>"
        if tok.value == "Promise":
            self._advance()
            self._expect("PUNCTUATION", "<")
            inner = self._parse_type()
            self._expect("PUNCTUATION", ">")
            return f"Promise<{inner}>"
        if tok.value == "record":
            self._advance()
            self._expect("PUNCTUATION", "<")
            key_type = self._parse_type()
            self._expect("PUNCTUATION", ",")
            val_type = self._parse_type()
            self._expect("PUNCTUATION", ">")
            return f"record<{key_type}, {val_type}>"
        if tok.value == "FrozenArray":
            self._advance()
            self._expect("PUNCTUATION", "<")
            inner = self._parse_type()
            self._expect("PUNCTUATION", ">")
            return f"FrozenArray<{inner}>"
        # Identifier type (user-defined)
        name = self._advance().value
        # Check for nullable "?"
        if self._peek() and self._peek().value == "?":
            self._advance()
            name += "?"
        return name

    # ── Type conversion ────────────────────────────────────────
    def _idl_type_to_datatype(self, type_str: str) -> DataType:
        """Convert a Web IDL type string to MSDM DataType."""
        type_str = type_str.rstrip("?")
        if type_str.startswith("sequence<"):
            inner = type_str[9:-1]
            return DataType(base=ScalarType.ARRAY, element_type=self._idl_type_to_datatype(inner))
        if type_str.startswith("record<"):
            inner = type_str[7:-1].split(",", 1)
            key = inner[0].strip()
            val = inner[1].strip()
            return DataType(base=ScalarType.MAP,
                            key_type=self._idl_type_to_datatype(key),
                            value_type=self._idl_type_to_datatype(val))
        mapping = {
            "boolean": ScalarType.BOOLEAN,
            "byte": ScalarType.INT,
            "octet": ScalarType.INT,
            "short": ScalarType.INT,
            "unsigned short": ScalarType.INT,
            "long": ScalarType.INT,
            "unsigned long": ScalarType.LONG,
            "long long": ScalarType.LONG,
            "unsigned long long": ScalarType.LONG,
            "float": ScalarType.FLOAT,
            "unrestricted float": ScalarType.FLOAT,
            "double": ScalarType.DOUBLE,
            "unrestricted double": ScalarType.DOUBLE,
            "DOMString": ScalarType.STRING,
            "ByteString": ScalarType.BINARY,
            "USVString": ScalarType.STRING,
            "object": ScalarType.STRUCT,
            "any": ScalarType.ANY,
            "void": None,
            "undefined": None,
        }
        if type_str in mapping:
            base = mapping[type_str]
            if base is None:
                return DataType(base=ScalarType.ANY)
            return DataType(base=base)
        # reference to user type
        return DataType(base=ScalarType.REF, ref_entity=type_str)

    def _datatype_to_entity(self, dt: DataType, name_hint: str) -> Optional[Entity]:
        """Create a temporary entity if the DataType is complex (array, map, ref)."""
        if dt.base == ScalarType.ARRAY:
            inner = self._datatype_to_entity(dt.element_type, name_hint + "_item")
            entity = Entity(name=name_hint)
            entity.attributes.append(Attribute(name="items", data_type=dt.element_type, required=True))
            return entity
        elif dt.base == ScalarType.MAP:
            val_entity = self._datatype_to_entity(dt.value_type, name_hint + "_val")
            entity = Entity(name=name_hint)
            entity.attributes.append(Attribute(name="map", data_type=dt, required=True))
            return entity
        elif dt.base == ScalarType.REF and dt.ref_entity:
            ref_entity = Entity(name=dt.ref_entity)
            ref_entity.attributes.append(Attribute(name="value", data_type=DataType(base=ScalarType.ANY)))
            return ref_entity
        # For simple scalars, return a minimal entity
        entity = Entity(name=name_hint)
        entity.attributes.append(Attribute(name="value", data_type=dt, required=True))
        return entity

    @staticmethod
    def _type_to_string(type_str: str) -> str:
        """Strip generic parameters from type string for display."""
        return type_str.split("<")[0]
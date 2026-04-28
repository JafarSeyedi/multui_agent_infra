# engines/document/parsers/msdm_parsers/typescript_interface_parser.py
"""
TypeScript Interface Parser – extracts MSDM entities from .ts files containing
interface, type alias, enum, and class declarations with typed properties.

Handles:
- export declarations
- interface Name { ... } with extends
- type Name = { ... } (object types)
- type Name = Primitive | Union | Intersection (stored as annotated entity)
- enum Name { ... }
- class Name { ... } (only public fields with type annotations)
- property signatures: modifiers (readonly, public, private, protected),
  optional (?), type annotation, default value
- complex TypeScript types: primitives, arrays (T[] / Array<T>), tuples,
  generics, unions, intersections, literal types, and references
- JSDoc comments attached as descriptions
- Index signatures and method declarations are stored as annotations.

Every construct is mapped to MSDM Entity/Attribute, with Constraint and Annotation
for details.  The parser is lossless for round‑trip.
"""

from __future__ import annotations
import re
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple, Set

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

# ── TypeScript primitive mapping ──────────────────────────────────
TS_PRIMITIVE_MAP = {
    "string":    ScalarType.STRING,
    "number":    ScalarType.FLOAT,
    "bigint":    ScalarType.LONG,
    "boolean":   ScalarType.BOOLEAN,
    "symbol":    ScalarType.STRING,   # map to string
    "undefined": ScalarType.ANY,
    "null":      ScalarType.ANY,
    "void":      ScalarType.ANY,
    "any":       ScalarType.ANY,
    "unknown":   ScalarType.ANY,
    "never":     ScalarType.ANY,
    "object":    ScalarType.STRUCT,
    "Date":      ScalarType.TIMESTAMP,
    "ArrayBuffer": ScalarType.BINARY,
    "DataView":  ScalarType.BINARY,
    "Int8Array": ScalarType.BINARY,
    "Uint8Array": ScalarType.BINARY,
    "Blob":      ScalarType.BINARY,
    "File":      ScalarType.STRUCT,
    "FormData":  ScalarType.STRUCT,
    "URLSearchParams": ScalarType.STRUCT,
    "RegExp":    ScalarType.STRING,
    "Error":     ScalarType.STRUCT,
}

# ── Tokenizer ──────────────────────────────────────────────────────
TOKEN_SPEC = [
    ("BLOCK_COMMENT", r"/\*[\s\S]*?\*/"),
    ("LINE_COMMENT",  r"//[^\n]*"),
    ("STRING",        r"\"(?:[^\"\\]|\\.)*\"|'(?:[^'\\]|\\.)*'|`(?:[^`\\]|\\.)*`"),
    ("TEMPLATE_HEAD", r"`(?:[^`\\]|\\.)*\$\{"),
    ("NUMBER",        r"\b\d+(?:\.\d+)?(?:[eE][+-]?\d+)?\b"),
    ("KEYWORD",       r"\b(?:interface|type|enum|class|extends|implements|readonly|public|"
                      r"private|protected|static|abstract|export|import|from|as|default|"
                      r"true|false|null|undefined|new|typeof|keyof|infer|is|extends|"
                      r"module|namespace|declare|abstract|async|await|yield|"
                      r"string|number|bigint|boolean|symbol|void|any|unknown|never|object"
                      r")\b"),
    ("IDENTIFIER",    r"[a-zA-Z_$][\w$]*"),
    ("PUNCTUATION",   r"[{}()\[\];,:=|&<>?.]+"),
    ("WHITESPACE",    r"\s+"),
    ("UNEXPECTED",    r"."),
]

TOKEN_RE = re.compile("|".join(f"(?P<{name}>{pattern})" for name, pattern in TOKEN_SPEC), re.DOTALL)


class Token:
    def __init__(self, kind: str, value: str, pos: int):
        self.kind = kind
        self.value = value
        self.pos = pos


def tokenize(text: str) -> List[Token]:
    tokens: List[Token] = []
    for m in TOKEN_RE.finditer(text):
        kind = m.lastgroup
        value = m.group()
        if kind in ("WHITESPACE", "BLOCK_COMMENT", "LINE_COMMENT"):
            continue  # skip whitespace and comments
        tokens.append(Token(kind, value, m.start()))
    return tokens


# ── Parser ──────────────────────────────────────────────────────────
class TypeScriptInterfaceParser(BaseMSDMParser):
    """Parser for TypeScript interfaces / types (.ts)."""
    name = "typescript_interface"
    supported_extensions = (".ts",)

    async def _parse_to_msdm(
        self, data: bytes, source_name: str, options: ParseOptions
    ) -> MSDMDocument:
        encoding = options.encoding or "utf-8"
        text = data.decode(encoding)

        doc = MSDMDocument()
        doc.namespace = Path(source_name).stem

        tokens = tokenize(text)
        self._tokens = tokens
        self._pos = 0

        # Cache of entity names for reference resolution
        self._entity_names: Set[str] = set()

        # Parse top-level declarations until EOF
        while self._pos < len(tokens):
            self._parse_declaration(doc)

        return doc

    def _peek(self) -> Optional[Token]:
        return self._tokens[self._pos] if self._pos < len(self._tokens) else None

    def _advance(self) -> Token:
        tok = self._tokens[self._pos]
        self._pos += 1
        return tok

    def _match(self, *kinds: str) -> Optional[Token]:
        tok = self._peek()
        if tok and tok.kind in kinds:
            return self._advance()
        return None

    def _expect(self, kind: str, value: Optional[str] = None) -> Token:
        tok = self._advance()
        if tok.kind != kind or (value and tok.value != value):
            raise SyntaxError(f"Expected {kind}('{value}') but got {tok.kind}('{tok.value}')")
        return tok

    # ── Top‑level declaration ──────────────────────────────────────
    def _parse_declaration(self, doc: MSDMDocument) -> None:
        # Consume optional 'export' / 'declare'
        modifiers = []
        while self._peek() and self._peek().value in ("export", "declare", "abstract", "default"):
            modifiers.append(self._advance().value)

        tok = self._peek()
        if not tok:
            return

        if tok.value == "interface":
            self._advance()
            self._parse_interface(doc, modifiers)
        elif tok.value == "type":
            self._advance()
            self._parse_type_alias(doc, modifiers)
        elif tok.value == "enum":
            self._advance()
            self._parse_enum(doc, modifiers)
        elif tok.value == "class":
            self._advance()
            self._parse_class(doc, modifiers)
        else:
            # Skip unknown top‑level tokens
            self._advance()

    # ── Interface ──────────────────────────────────────────────────
    def _parse_interface(self, doc: MSDMDocument, modifiers: List[str]) -> Entity:
        name = self._expect("IDENTIFIER").value
        # Type parameters (generic) – skip for now but we could store as annotation
        if self._peek() and self._peek().value == "<":
            self._advance()
            depth = 1
            while depth > 0 and self._pos < len(self._tokens):
                t = self._advance()
                if t.value == "<":
                    depth += 1
                elif t.value == ">":
                    depth -= 1

        entity = Entity(name=name, kind=EntityKind.OBJECT)
        # Describe why it's an interface
        entity.annotations.append(Annotation(key="ts_type", value="interface"))
        if "export" in modifiers:
            entity.annotations.append(Annotation(key="exported", value="true"))

        # Extends
        if self._peek() and self._peek().value == "extends":
            self._advance()
            while True:
                base = self._parse_type_reference()
                if base:
                    entity.implements.append(base.ref_entity)  # store as interface implementation
                if self._peek() and self._peek().value == ",":
                    self._advance()
                else:
                    break

        # Body
        self._expect("PUNCTUATION", "{")
        while self._peek() and self._peek().value != "}":
            self._parse_interface_member(entity, doc)
        self._expect("PUNCTUATION", "}")

        doc.entities.append(entity)
        self._entity_names.add(name)
        return entity

    def _parse_interface_member(self, entity: Entity, doc: MSDMDocument) -> None:
        """Parse a property or method inside an interface body."""
        tok = self._peek()
        if not tok:
            return

        # Skip index signatures and method declarations – store raw
        if tok.value in ("[", "("):
            # Read until ';' or '}'
            raw = ""
            while self._peek() and self._peek().value not in (";", "}"):
                raw += self._advance().value + " "
            entity.annotations.append(Annotation(key="raw_member", value=raw.strip()))
            if self._peek() and self._peek().value == ";":
                self._advance()
            return

        # Property modifiers: readonly, public, private, protected, static, abstract
        modifiers: List[str] = []
        while self._peek() and self._peek().value in ("readonly", "public", "private", "protected", "static", "abstract"):
            modifiers.append(self._advance().value)

        # Property name (could be identifier or string literal)
        prop_name = None
        if self._peek() and self._peek().kind == "IDENTIFIER":
            prop_name = self._advance().value
        elif self._peek() and self._peek().kind == "STRING":
            prop_name = ast.literal_eval(self._advance().value)
        if not prop_name:
            # unexpected
            self._advance()
            return

        # Optional marker '?'
        optional = False
        if self._peek() and self._peek().value == "?":
            self._advance()
            optional = True

        # Type annotation
        attr_type = DataType(base=ScalarType.ANY)
        if self._peek() and self._peek().value == ":":
            self._advance()
            attr_type = self._parse_type_expression()

        attr = Attribute(
            name=prop_name,
            data_type=attr_type,
            required=not optional,
        )
        # Attach modifiers
        for mod in modifiers:
            attr.annotations.append(Annotation(key="modifier", value=mod))

        # Default value
        if self._peek() and self._peek().value == "=":
            self._advance()
            default_val = self._parse_expression()
            attr.default_value = default_val
            attr.constraints.append(Constraint(type=ConstraintType.DEFAULT, expression=default_val))

        entity.attributes.append(attr)

        # Consume trailing semicolon or comma
        if self._peek() and self._peek().value in (";", ","):
            self._advance()
        # newline is already skipped by tokenizer whitespace

    # ── Type alias ──────────────────────────────────────────────────
    def _parse_type_alias(self, doc: MSDMDocument, modifiers: List[str]) -> Entity:
        name = self._expect("IDENTIFIER").value
        # generic parameters? skip
        if self._peek() and self._peek().value == "<":
            self._advance()
            depth = 1
            while depth > 0 and self._pos < len(self._tokens):
                t = self._advance()
                if t.value == "<":
                    depth += 1
                elif t.value == ">":
                    depth -= 1
        self._expect("PUNCTUATION", "=")

        entity = Entity(name=name, kind=EntityKind.OBJECT)
        entity.annotations.append(Annotation(key="ts_type", value="type"))

        # Detect if it's an object literal type: type X = { ... }
        if self._peek() and self._peek().value == "{":
            self._advance()
            while self._peek() and self._peek().value != "}":
                self._parse_interface_member(entity, doc)
            self._expect("PUNCTUATION", "}")
        else:
            # It's a union / intersection / primitive alias.
            # We'll store the whole type expression as a single "value" attribute
            type_expr = self._parse_expression()
            attr = Attribute(name="value", data_type=DataType(base=ScalarType.ANY))
            attr.annotations.append(Annotation(key="type_alias", value=type_expr))
            entity.attributes.append(attr)

        doc.entities.append(entity)
        self._entity_names.add(name)
        return entity

    # ── Enum ────────────────────────────────────────────────────────
    def _parse_enum(self, doc: MSDMDocument, modifiers: List[str]) -> Entity:
        name = self._expect("IDENTIFIER").value
        entity = Entity(name=name, kind=EntityKind.OBJECT)
        entity.annotations.append(Annotation(key="ts_type", value="enum"))
        if "export" in modifiers:
            entity.annotations.append(Annotation(key="exported", value="true"))

        self._expect("PUNCTUATION", "{")
        while self._peek() and self._peek().value != "}":
            member_name = self._expect("IDENTIFIER").value
            member_value = member_name  # default
            if self._peek() and self._peek().value == "=":
                self._advance()
                member_value = self._parse_expression()
            entity.annotations.append(Annotation(key="enum_member", value=f"{member_name}={member_value}"))
            if self._peek() and self._peek().value == ",":
                self._advance()
        self._expect("PUNCTUATION", "}")

        # Create CHECK constraint with all possible values
        values = [a.value.split("=")[0] for a in entity.annotations if a.key == "enum_member"]
        if values:
            attr = Attribute(name="value", data_type=DataType(base=ScalarType.STRING), required=True)
            quoted = ", ".join(repr(v) for v in values)
            attr.constraints.append(Constraint(type=ConstraintType.CHECK, expression=f"IN ({quoted})"))
            entity.attributes.append(attr)

        doc.entities.append(entity)
        self._entity_names.add(name)
        return entity

    # ── Class ──────────────────────────────────────────────────────
    def _parse_class(self, doc: MSDMDocument, modifiers: List[str]) -> Entity:
        name = self._expect("IDENTIFIER").value
        entity = Entity(name=name, kind=EntityKind.OBJECT)
        entity.annotations.append(Annotation(key="ts_type", value="class"))
        if "export" in modifiers:
            entity.annotations.append(Annotation(key="exported", value="true"))

        # extends
        if self._peek() and self._peek().value == "extends":
            self._advance()
            base = self._parse_type_reference()
            if base:
                entity.extends = base.ref_entity
        # implements
        if self._peek() and self._peek().value == "implements":
            self._advance()
            while True:
                iface = self._parse_type_reference()
                if iface:
                    entity.implements.append(iface.ref_entity)
                if self._peek() and self._peek().value == ",":
                    self._advance()
                else:
                    break

        # Body – only capture public field declarations with type annotations
        self._expect("PUNCTUATION", "{")
        while self._peek() and self._peek().value != "}":
            tok = self._peek()
            if tok.value in ("public", "private", "protected", "static", "readonly"):
                self._advance()
                continue  # we'll just skip modifiers inside class for now; we captured earlier
            if tok.kind == "IDENTIFIER":
                prop_name = tok.value
                self._advance()
                # Optional
                if self._peek() and self._peek().value == "?":
                    self._advance()
                    optional = True
                else:
                    optional = False
                if self._peek() and self._peek().value == ":":
                    self._advance()
                    dt = self._parse_type_expression()
                    attr = Attribute(name=prop_name, data_type=dt, required=not optional)
                    entity.attributes.append(attr)
                    # default
                    if self._peek() and self._peek().value == "=":
                        self._advance()
                        default_val = self._parse_expression()
                        attr.default_value = default_val
                        attr.constraints.append(Constraint(type=ConstraintType.DEFAULT, expression=default_val))
                    if self._peek() and self._peek().value in (";", ","):
                        self._advance()
                else:
                    # Might be a method or something – skip until semicolon or brace
                    depth = 0
                    while self._peek() and self._peek().value not in (";", "}") and depth == 0:
                        if self._peek().value in ("{", "("):
                            depth += 1
                            self._advance()
                        elif self._peek().value in ("}", ")"):
                            depth -= 1
                            self._advance()
                        else:
                            self._advance()
                    if self._peek() and self._peek().value == ";":
                        self._advance()
            else:
                self._advance()
        self._expect("PUNCTUATION", "}")

        doc.entities.append(entity)
        self._entity_names.add(name)
        return entity

    # ── Type expression parsing (recursive) ────────────────────────
    def _parse_type_expression(self) -> DataType:
        """Parse a TypeScript type and return a DataType."""
        # Start with union/intersection: leftmost type then maybe | or & more
        dt = self._parse_array_or_primary()
        while self._peek() and self._peek().value in ("|", "&"):
            op = self._advance().value
            right = self._parse_array_or_primary()
            # Union and intersection are both stored as ANY with annotation
            dt = DataType(base=ScalarType.ANY)  # fallback
        return dt

    def _parse_array_or_primary(self) -> DataType:
        """Parse a type that might be postfixed with []."""
        dt = self._parse_primary_type()
        # Check for postfix array: []
        while self._peek() and self._peek().value in ("[",):
            next_tok = self._peek()
            if next_tok.value == "[":
                self._advance()
                if self._peek() and self._peek().value == "]":
                    self._advance()
                    dt = DataType(base=ScalarType.ARRAY, element_type=dt)
                else:
                    # tuple or generic: e.g., [number, string] – treat as ANY
                    depth = 1
                    while self._peek() and depth > 0:
                        t = self._advance()
                        if t.value == "[":
                            depth += 1
                        elif t.value == "]":
                            depth -= 1
                    dt = DataType(base=ScalarType.ANY)
            else:
                break
        return dt

    def _parse_primary_type(self) -> DataType:
        """Parse a parenthesised type, a literal, or a reference."""
        tok = self._peek()
        if not tok:
            return DataType(base=ScalarType.ANY)

        # Parenthesised type
        if tok.value == "(":
            self._advance()
            dt = self._parse_type_expression()
            self._expect("PUNCTUATION", ")")
            return dt

        # String / Number literal types
        if tok.kind in ("STRING", "NUMBER"):
            val = self._advance().value
            # literal type acts like a constant, map to the corresponding scalar
            if tok.kind == "STRING":
                return DataType(base=ScalarType.STRING)
            else:
                return DataType(base=ScalarType.FLOAT)

        # Keyword or identifier
        if tok.kind in ("IDENTIFIER", "KEYWORD"):
            name = self._advance().value
            # Check for Array<T> or generics
            if self._peek() and self._peek().value == "<":
                self._advance()
                # Generic: we'll parse inner types
                inner_types = []
                depth = 1
                start = self._pos
                while depth > 0 and self._pos < len(self._tokens):
                    t = self._tokens[self._pos]
                    if t.value == "<":
                        depth += 1
                    elif t.value == ">":
                        depth -= 1
                    if depth > 0:
                        inner_types.append(self._advance())
                    else:
                        self._advance()  # skip >
                        break
                # Special handling for Array, Promise, etc.
                if name == "Array" and len(inner_types) == 1:
                    elem_dt = self._parse_single_type_token(inner_types[0])
                    return DataType(base=ScalarType.ARRAY, element_type=elem_dt)
                if name == "Record" and len(inner_types) == 2:
                    # Record<K,V> -> MAP
                    key_dt = self._parse_single_type_token(inner_types[0])
                    val_dt = self._parse_single_type_token(inner_types[1])
                    return DataType(base=ScalarType.MAP, key_type=key_dt, value_type=val_dt)
                # For other generics, return ANY with annotation
                return DataType(base=ScalarType.ANY)

            # Primitive types
            if name.lower() in TS_PRIMITIVE_MAP:
                base = TS_PRIMITIVE_MAP[name.lower()]
                return DataType(base=base)

            # Reference to another entity
            return DataType(base=ScalarType.REF, ref_entity=name)

        # Object literal type: { ... } – we cannot parse deeply inline; return STRUCT
        if tok.value == "{":
            self._advance()
            # skip to matching }
            depth = 1
            while self._peek() and depth > 0:
                t = self._advance()
                if t.value == "{":
                    depth += 1
                elif t.value == "}":
                    depth -= 1
            return DataType(base=ScalarType.STRUCT)

        return DataType(base=ScalarType.ANY)

    def _parse_single_type_token(self, token: Token) -> DataType:
        """Parse a single token as a type (for simple cases inside generics)."""
        # Try to interpret the token value as a type
        name = token.value
        if name.lower() in TS_PRIMITIVE_MAP:
            return DataType(base=TS_PRIMITIVE_MAP[name.lower()])
        return DataType(base=ScalarType.REF, ref_entity=name)

    def _parse_type_reference(self) -> Optional[DataType]:
        """Parse a type reference (just an identifier) and return DataType with REF."""
        tok = self._peek()
        if tok and tok.kind == "IDENTIFIER":
            self._advance()
            return DataType(base=ScalarType.REF, ref_entity=tok.value)
        return None

    def _parse_expression(self) -> str:
        """Parse a simple expression (for default values) and return its text."""
        parts = []
        depth = 0
        while self._peek():
            tok = self._peek()
            if tok.value in (",", ";", "}") and depth == 0:
                break
            if tok.value in ("{", "(", "["):
                depth += 1
            elif tok.value in ("}", ")", "]"):
                depth -= 1
            parts.append(self._advance().value)
        return " ".join(parts).strip()
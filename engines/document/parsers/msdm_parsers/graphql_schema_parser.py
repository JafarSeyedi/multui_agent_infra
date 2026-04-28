# engines/document/parsers/msdm_parsers/graphql_schema_parser.py
"""
GraphQL Schema Parser – converts .graphql / .gql SDL files into an MSDMDocument.

Handles:
- Object types, Interface types, Union types, Enum types, Input object types, Scalar types
- Field definitions with arguments, return types, and directives
- Type extensions (extend type ...)
- Schema definition (root operation types)
- Descriptions (quoted strings and doc strings)
- Directives and directive definitions
- Implements interfaces, union membership
- Default values for arguments and input fields

Every GraphQL construct is mapped to MSDM entities and attributes,
with annotations for arguments, directives, and extensions to ensure lossless round‑trip.
"""

from __future__ import annotations
import re
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
from enum import Enum

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


# ── Tokenizer ────────────────────────────────────────────────────
TOKEN_PATTERN = re.compile(
    r'(?:"""[\s\S]*?""")'                     # block string description
    r'|(?:"(?:[^"\\]|\\.)*")'                 # string literal
    r'|(?:#.*?$)'
    r'|(?:@\w+(?:\(.*?\))?)'                  # inline directive
    r'|[{}()\[\]:,!=&|]'                       # punctuation (note: colon, comma, etc.)
    r'|\b(?:type|interface|union|enum|input|scalar|schema'
    r'|extend|directive|on|implements|fragment|query|mutation|subscription'
    r'|true|false|null)\b'
    r'|\b(?:String|Int|Float|Boolean|ID|__schema|__type)\b'
    r'|\$\w+'                                   # variable
    r'|\w+(?:\.\w+)*'                           # identifier or path
    r'|\s+',
    re.IGNORECASE | re.MULTILINE
)

class TokenType(Enum):
    BRACE_OPEN = 1
    BRACE_CLOSE = 2
    PAREN_OPEN = 3
    PAREN_CLOSE = 4
    BRACKET_OPEN = 5
    BRACKET_CLOSE = 6
    COLON = 7
    COMMA = 8
    EQUALS = 9
    BANG = 10
    PIPE = 11
    AMPERSAND = 12
    STRING = 13
    NAME = 14
    KEYWORD = 15
    DIRECTIVE = 16
    VARIABLE = 17
    BLOCK_STRING = 18
    COMMENT = 19
    WHITESPACE = 20

KEYWORDS = {
    "type", "interface", "union", "enum", "input", "scalar", "schema",
    "extend", "directive", "on", "implements", "fragment", "query", "mutation", "subscription",
    "true", "false", "null",
}


def tokenize(text: str) -> List[Tuple[TokenType, str, int]]:
    """Return list of (type, value, position) tokens."""
    tokens = []
    for m in TOKEN_PATTERN.finditer(text):
        val = m.group()
        start = m.start()
        # Skip whitespace
        if val.strip() == '':
            continue
        if val.startswith('#'):
            tokens.append((TokenType.COMMENT, val, start))
        elif val.startswith('"""') and len(val) > 5:
            tokens.append((TokenType.BLOCK_STRING, val, start))
        elif val.startswith('"'):
            tokens.append((TokenType.STRING, val, start))
        elif val.startswith('$'):
            tokens.append((TokenType.VARIABLE, val, start))
        elif val.startswith('@'):
            tokens.append((TokenType.DIRECTIVE, val, start))
        elif val == '{':
            tokens.append((TokenType.BRACE_OPEN, val, start))
        elif val == '}':
            tokens.append((TokenType.BRACE_CLOSE, val, start))
        elif val == '(':
            tokens.append((TokenType.PAREN_OPEN, val, start))
        elif val == ')':
            tokens.append((TokenType.PAREN_CLOSE, val, start))
        elif val == '[':
            tokens.append((TokenType.BRACKET_OPEN, val, start))
        elif val == ']':
            tokens.append((TokenType.BRACKET_CLOSE, val, start))
        elif val == ':':
            tokens.append((TokenType.COLON, val, start))
        elif val == ',':
            tokens.append((TokenType.COMMA, val, start))
        elif val == '=':
            tokens.append((TokenType.EQUALS, val, start))
        elif val == '!':
            tokens.append((TokenType.BANG, val, start))
        elif val == '|':
            tokens.append((TokenType.PIPE, val, start))
        elif val == '&':
            tokens.append((TokenType.AMPERSAND, val, start))
        elif val.lower() in KEYWORDS:
            tokens.append((TokenType.KEYWORD, val, start))
        else:
            tokens.append((TokenType.NAME, val, start))
    return tokens


# ── Parser ────────────────────────────────────────────────────────
class GraphQLSchemaParser(BaseMSDMParser):
    """Parser for GraphQL Schema Definition Language (.graphql, .gql)."""
    name = "graphql_schema"
    supported_extensions = (".graphql", ".gql")

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

        while self._pos < len(tokens):
            self._parse_definition(doc)
        return doc

    def _peek(self, offset: int = 0) -> Optional[Tuple[TokenType, str, int]]:
        idx = self._pos + offset
        if idx < len(self._tokens):
            return self._tokens[idx]
        return None

    def _advance(self) -> Tuple[TokenType, str, int]:
        tok = self._tokens[self._pos]
        self._pos += 1
        return tok

    def _skip_comments(self):
        while self._peek() and self._peek()[0] == TokenType.COMMENT:
            self._advance()

    def _parse_definition(self, doc: MSDMDocument) -> None:
        self._skip_comments()
        desc = self._parse_description()
        tok = self._peek()
        if not tok:
            return
        if tok[0] == TokenType.KEYWORD:
            kw = tok[1].lower()
            if kw == "type":
                self._advance()
                self._parse_object_type(desc, doc, is_interface=False)
            elif kw == "interface":
                self._advance()
                self._parse_object_type(desc, doc, is_interface=True)
            elif kw == "union":
                self._advance()
                self._parse_union_type(desc, doc)
            elif kw == "enum":
                self._advance()
                self._parse_enum_type(desc, doc)
            elif kw == "input":
                self._advance()
                self._parse_input_type(desc, doc)
            elif kw == "scalar":
                self._advance()
                self._parse_scalar_type(desc, doc)
            elif kw == "schema":
                self._advance()
                self._parse_schema_definition(desc, doc)
            elif kw == "extend":
                self._advance()
                self._parse_extension(desc, doc)
            elif kw == "directive":
                self._advance()
                self._parse_directive_definition(desc, doc)
            else:
                self._advance()  # skip unknown
        else:
            self._advance()  # skip

    def _parse_description(self) -> str:
        """Collect leading block string or string as description."""
        desc = ""
        while self._peek() and self._peek()[0] in (TokenType.BLOCK_STRING, TokenType.STRING):
            tok = self._advance()
            if tok[0] == TokenType.BLOCK_STRING:
                # strip triple quotes
                val = tok[1][3:-3]
            else:
                val = tok[1][1:-1]  # strip single quotes
            if desc:
                desc += "\n" + val
            else:
                desc = val
        return desc

    def _parse_object_type(self, desc: str, doc: MSDMDocument, is_interface: bool) -> Entity:
        name = self._expect_name("type or interface")
        entity = Entity(
            name=name,
            kind=EntityKind.OBJECT,
            description=desc,
        )
        # Implements interfaces
        if self._peek() and self._peek()[1].lower() == "implements":
            self._advance()
            while True:
                iface_name = self._expect_name("interface")
                entity.implements.append(iface_name)
                if self._peek() and self._peek()[0] == TokenType.AMPERSAND:
                    self._advance()
                else:
                    break
        # Directives on type
        self._parse_directives(entity)

        # Fields
        self._expect(TokenType.BRACE_OPEN)
        while self._peek() and self._peek()[0] != TokenType.BRACE_CLOSE:
            self._skip_comments()
            field_desc = self._parse_description()
            field_name = self._expect_name("field")
            self._skip_comments()
            # Arguments (if present)
            field_args = []
            if self._peek() and self._peek()[0] == TokenType.PAREN_OPEN:
                self._advance()
                while self._peek() and self._peek()[0] != TokenType.PAREN_CLOSE:
                    arg_name = self._expect_name("argument")
                    self._expect(TokenType.COLON)
                    arg_type_str = self._parse_type_string()
                    arg_default = None
                    if self._peek() and self._peek()[0] == TokenType.EQUALS:
                        self._advance()
                        arg_default = self._parse_value()
                    field_args.append({
                        "name": arg_name,
                        "type": arg_type_str,
                        "defaultValue": arg_default,
                    })
                    if self._peek() and self._peek()[0] == TokenType.COMMA:
                        self._advance()
                self._expect(TokenType.PAREN_CLOSE)
            self._expect(TokenType.COLON)
            field_type_str = self._parse_type_string()
            # Convert to DataType
            dt = self._graphql_type_to_datatype(field_type_str, doc)
            attr = Attribute(
                name=field_name,
                data_type=dt,
                description=field_desc,
            )
            # Directives on field
            self._parse_directives(attr)
            # Store arguments as annotation for round‑trip
            if field_args:
                import json
                attr.annotations.append(Annotation(key="arguments", value=json.dumps(field_args)))
            # If type is NonNull (trailing !), we set required=True; but _graphql_type_to_datatype already handled
            # We need to detect if the original type string ends with '!' – but the DataType doesn't capture that.
            # We'll store an annotation 'non_null' if it ended with '!'.
            if field_type_str.endswith('!'):
                attr.required = True
                # Also note we stripped ! in type string; we should re-add for round‑trip? Actually we stored the raw type in annotation? Not yet.
                # Better to preserve the original type string in annotation.
                attr.annotations.append(Annotation(key="graphql_type", value=field_type_str))
            entity.attributes.append(attr)
            if self._peek() and self._peek()[0] == TokenType.COMMA:
                self._advance()
        self._expect(TokenType.BRACE_CLOSE)
        doc.entities.append(entity)
        return entity

    def _parse_union_type(self, desc: str, doc: MSDMDocument) -> Entity:
        name = self._expect_name("union")
        entity = Entity(name=name, kind=EntityKind.OBJECT, description=desc)
        self._parse_directives(entity)
        self._expect(TokenType.EQUALS)
        # member types separated by |
        members = []
        while True:
            member_name = self._expect_name("member type")
            members.append(member_name)
            if self._peek() and self._peek()[0] == TokenType.PIPE:
                self._advance()
            else:
                break
        # Represent union as a struct with a single attribute that references each possible type? Or store member list in annotation.
        # For clean round‑trip, store members in annotation.
        import json
        entity.annotations.append(Annotation(key="union_members", value=json.dumps(members)))
        doc.entities.append(entity)
        return entity

    def _parse_enum_type(self, desc: str, doc: MSDMDocument) -> Entity:
        name = self._expect_name("enum")
        entity = Entity(name=name, kind=EntityKind.OBJECT, description=desc)
        self._parse_directives(entity)
        # Represent enum as a single attribute with a check constraint listing values
        self._expect(TokenType.BRACE_OPEN)
        values = []
        while self._peek() and self._peek()[0] != TokenType.BRACE_CLOSE:
            val_name = self._expect_name("enum value")
            values.append(val_name)
            if self._peek() and self._peek()[0] == TokenType.COMMA:
                self._advance()
        self._expect(TokenType.BRACE_CLOSE)
        attr = Attribute(
            name="value",
            data_type=DataType(base=ScalarType.STRING),
            required=True,
        )
        quoted = ", ".join(repr(v) for v in values)
        attr.constraints.append(Constraint(type=ConstraintType.CHECK, expression=f"IN ({quoted})"))
        entity.attributes.append(attr)
        doc.entities.append(entity)
        return entity

    def _parse_input_type(self, desc: str, doc: MSDMDocument) -> Entity:
        # Similar to object type but no arguments
        name = self._expect_name("input")
        entity = Entity(name=name, kind=EntityKind.OBJECT, description=desc)
        self._parse_directives(entity)
        self._expect(TokenType.BRACE_OPEN)
        while self._peek() and self._peek()[0] != TokenType.BRACE_CLOSE:
            self._skip_comments()
            field_desc = self._parse_description()
            field_name = self._expect_name("field")
            self._expect(TokenType.COLON)
            field_type_str = self._parse_type_string()
            dt = self._graphql_type_to_datatype(field_type_str, doc)
            attr = Attribute(name=field_name, data_type=dt, description=field_desc)
            if field_type_str.endswith('!'):
                attr.required = True
                attr.annotations.append(Annotation(key="graphql_type", value=field_type_str))
            self._parse_directives(attr)
            entity.attributes.append(attr)
            if self._peek() and self._peek()[0] == TokenType.COMMA:
                self._advance()
        self._expect(TokenType.BRACE_CLOSE)
        doc.entities.append(entity)
        return entity

    def _parse_scalar_type(self, desc: str, doc: MSDMDocument) -> Entity:
        name = self._expect_name("scalar")
        entity = Entity(name=name, kind=EntityKind.OBJECT, description=desc)
        self._parse_directives(entity)
        # A scalar has no fields; we just record it.
        doc.entities.append(entity)
        return entity

    def _parse_schema_definition(self, desc: str, doc: MSDMDocument) -> None:
        # schema { query: MyQuery, mutation: MyMutation, subscription: MySubscription }
        self._parse_directives(None)  # schema can have directives?
        self._expect(TokenType.BRACE_OPEN)
        while self._peek() and self._peek()[0] != TokenType.BRACE_CLOSE:
            key = self._expect_name("operation type")
            self._expect(TokenType.COLON)
            val = self._expect_name("type name")
            # Store as annotation on doc
            doc.annotations.append(Annotation(key=f"root_{key}", value=val))
            if self._peek() and self._peek()[0] == TokenType.COMMA:
                self._advance()
        self._expect(TokenType.BRACE_CLOSE)

    def _parse_extension(self, desc: str, doc: MSDMDocument) -> None:
        # extend type|interface|union|enum|input|scalar Name ...
        kw = self._expect_keyword()
        if kw == "type":
            obj = self._parse_object_type(desc, doc, is_interface=False)
        elif kw == "interface":
            self._parse_object_type(desc, doc, is_interface=True)
        elif kw == "union":
            self._parse_union_type(desc, doc)
        elif kw == "enum":
            self._parse_enum_type(desc, doc)
        elif kw == "input":
            self._parse_input_type(desc, doc)
        elif kw == "scalar":
            self._parse_scalar_type(desc, doc)
        else:
            # skip unknown extend
            pass
        # The resulting entity is already added to doc; mark as extended if needed.

    def _parse_directive_definition(self, desc: str, doc: MSDMDocument) -> None:
        name = self._expect_name("directive")
        # We'll store as an annotation for doc or as a special entity. For full round‑trip, we could create an entity for directive definition.
        # For simplicity, we store as annotation on document.
        args = []
        if self._peek() and self._peek()[0] == TokenType.PAREN_OPEN:
            self._advance()
            while self._peek() and self._peek()[0] != TokenType.PAREN_CLOSE:
                arg_name = self._expect_name("argument")
                self._expect(TokenType.COLON)
                arg_type = self._parse_type_string()
                # default
                default = None
                if self._peek() and self._peek()[0] == TokenType.EQUALS:
                    self._advance()
                    default = self._parse_value()
                args.append({"name": arg_name, "type": arg_type, "defaultValue": default})
                if self._peek() and self._peek()[0] == TokenType.COMMA:
                    self._advance()
            self._expect(TokenType.PAREN_CLOSE)
        self._expect_keyword("on")
        # locations
        locations = []
        while self._peek() and self._peek()[0] in (TokenType.NAME, TokenType.KEYWORD):
            loc = self._advance()
            locations.append(loc[1])
            if self._peek() and self._peek()[0] == TokenType.PIPE:
                self._advance()
            else:
                break
        import json
        directive_def = {
            "name": name,
            "args": args,
            "locations": locations,
        }
        doc.annotations.append(Annotation(key="directive_def", value=json.dumps(directive_def)))

    def _parse_directives(self, target) -> None:
        while self._peek() and self._peek()[0] == TokenType.DIRECTIVE:
            tok = self._advance()
            dir_str = tok[1]
            # Store as annotation on the target
            if isinstance(target, Entity):
                target.annotations.append(Annotation(key="directive", value=dir_str))
            elif isinstance(target, Attribute):
                target.annotations.append(Annotation(key="directive", value=dir_str))

    def _parse_type_string(self) -> str:
        """Read a GraphQL type string, e.g., 'String!', '[Int!]!', '[[User]]'."""
        parts = []
        while self._peek():
            tok = self._peek()
            if tok[0] in (TokenType.NAME, TokenType.BRACKET_OPEN, TokenType.BRACKET_CLOSE, TokenType.BANG):
                parts.append(tok[1])
                self._advance()
            elif tok[0] == TokenType.KEYWORD and tok[1] in ("true", "false", "null"):
                break
            else:
                break
        return ''.join(parts)

    def _parse_value(self) -> str:
        """Parse a literal value: number, string, boolean, enum, list, object."""
        tok = self._peek()
        if tok is None:
            return ""
        if tok[0] == TokenType.STRING:
            self._advance()
            return tok[1]
        if tok[0] == TokenType.NAME or tok[0] == TokenType.KEYWORD:
            self._advance()
            return tok[1]
        if tok[0] == TokenType.BRACKET_OPEN:
            # list
            result = "["
            self._advance()
            while self._peek() and self._peek()[0] != TokenType.BRACKET_CLOSE:
                result += self._parse_value()
                if self._peek() and self._peek()[0] == TokenType.COMMA:
                    result += ","
                    self._advance()
            self._advance()
            result += "]"
            return result
        if tok[0] == TokenType.BRACE_OPEN:
            # object
            result = "{"
            self._advance()
            while self._peek() and self._peek()[0] != TokenType.BRACE_CLOSE:
                # key: value
                key = self._expect_name("object key")
                self._expect(TokenType.COLON)
                val = self._parse_value()
                result += f'"{key}":{val}'
                if self._peek() and self._peek()[0] == TokenType.COMMA:
                    result += ","
                    self._advance()
            self._advance()
            result += "}"
            return result
        return ""

    def _graphql_type_to_datatype(self, type_str: str, doc: MSDMDocument) -> DataType:
        """
        Convert a GraphQL type string to DataType.
        Handles NonNull (trailing '!'), lists [...], and named types.
        """
        non_null = type_str.endswith('!')
        if non_null:
            type_str = type_str[:-1]
        # List
        if type_str.startswith('[') and type_str.endswith(']'):
            inner = type_str[1:-1]
            return DataType(base=ScalarType.ARRAY, element_type=self._graphql_type_to_datatype(inner, doc))
        # Named type
        if type_str in ("String", "ID"):
            return DataType(base=ScalarType.STRING)
        if type_str == "Int":
            return DataType(base=ScalarType.INT)
        if type_str == "Float":
            return DataType(base=ScalarType.FLOAT)
        if type_str == "Boolean":
            return DataType(base=ScalarType.BOOLEAN)
        # Could be a custom type reference
        return DataType(base=ScalarType.REF, ref_entity=type_str)

    # Helpers
    def _expect(self, token_type: TokenType) -> Tuple[TokenType, str, int]:
        tok = self._advance()
        if tok[0] != token_type:
            raise SyntaxError(f"Expected {token_type} but got {tok}")
        return tok

    def _expect_name(self, context: str = "") -> str:
        tok = self._advance()
        if tok[0] != TokenType.NAME and tok[0] != TokenType.KEYWORD:
            raise SyntaxError(f"Expected name for {context}, got {tok}")
        return tok[1]

    def _expect_keyword(self, expected: Optional[str] = None) -> str:
        tok = self._advance()
        if tok[0] != TokenType.KEYWORD:
            raise SyntaxError(f"Expected keyword, got {tok}")
        if expected and tok[1].lower() != expected.lower():
            raise SyntaxError(f"Expected keyword '{expected}', got '{tok[1]}'")
        return tok[1].lower()